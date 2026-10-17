import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.services.chart_generator import generate_charts
from app.services.data_loader import DatasetStore, load_dataframe
from app.services.data_summary import build_dataset_summary
from app.config import settings


class DatasetPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dataset_ids: list[str] = []
        self.data_dir_patcher = patch.object(settings, "data_dir", self.temp_dir.name)
        self.data_dir_patcher.start()

    def tearDown(self):
        self.temp_dir.cleanup()
        self.data_dir_patcher.stop()

    def register_dataset(self, filename: str, df: pd.DataFrame) -> str:
        path = Path(self.temp_dir.name) / filename
        df.to_csv(path, index=False) if path.suffix == ".csv" else df.to_excel(path, index=False)
        dataset_id = path.stem
        DatasetStore.register(path, filename, dataset_id)
        self.dataset_ids.append(dataset_id)
        return dataset_id

    def test_pagination_returns_requested_page_and_dataset_totals(self):
        dataset_id = self.register_dataset(
            "pages.csv",
            pd.DataFrame({"number": range(23), "label": [f"row {n}" for n in range(23)]}),
        )

        result = build_dataset_summary(dataset_id, page=2, page_size=10)

        self.assertEqual(result.total_rows, 23)
        self.assertEqual(result.matching_rows, 23)
        self.assertEqual(result.current_page, 2)
        self.assertEqual(result.page_size, 10)
        self.assertEqual([row["number"] for row in result.preview_rows], list(range(10, 20)))

    def test_sorting_is_applied_to_full_filtered_dataset_before_pagination(self):
        dataset_id = self.register_dataset(
            "sorted-pages.csv",
            pd.DataFrame(
                {
                    "label": ["match-a", "other", "match-z", "match-b", "other"],
                    "score": [5, 0, 100, 20, 1],
                }
            ),
        )

        result = build_dataset_summary(
            dataset_id,
            page=2,
            page_size=1,
            search="match",
            sort_by="score",
            sort_desc=True,
        )

        self.assertEqual(result.matching_rows, 3)
        self.assertEqual(result.preview_rows[0]["score"], 20)

    def test_small_medium_and_large_datasets_keep_preview_page_bounded(self):
        for row_count in (10, 120, 5000):
            with self.subTest(row_count=row_count):
                dataset_id = self.register_dataset(
                    f"rows-{row_count}.csv",
                    pd.DataFrame(
                        {
                            "record": range(row_count),
                            "description": [f"row {number}" for number in range(row_count)],
                        }
                    ),
                )

                result = build_dataset_summary(dataset_id, page=1, page_size=10)

                self.assertEqual(result.total_rows, row_count)
                self.assertEqual(len(result.preview_rows), min(row_count, 10))

    def test_case_insensitive_search_finds_csv_record_after_first_page(self):
        labels = [f"regular row {n}" for n in range(24)] + ["Needle Record"]
        dataset_id = self.register_dataset(
            "late-match.csv",
            pd.DataFrame({"label": labels, "number": range(len(labels))}),
        )

        result = build_dataset_summary(dataset_id, search="nEeDlE rEcOrD")

        self.assertEqual(result.total_rows, 25)
        self.assertEqual(result.matching_rows, 1)
        self.assertEqual(result.preview_rows[0]["number"], 24)

    def test_search_tolerates_empty_cells(self):
        dataset_id = self.register_dataset(
            "empty-cells.csv",
            pd.DataFrame(
                {
                    "name": ["ordinary", None, "LAST RECORD"],
                    "detail": [None, "other", None],
                }
            ),
        )

        result = build_dataset_summary(dataset_id, search="last record")

        self.assertEqual(result.matching_rows, 1)
        self.assertEqual(result.preview_rows, [{"name": "LAST RECORD", "detail": None}])

    def test_summary_api_accepts_search_and_pagination_parameters(self):
        dataset_id = self.register_dataset(
            "api.csv",
            pd.DataFrame({"label": [f"record {n}" for n in range(12)]}),
        )

        response = TestClient(app).get(
            f"/api/datasets/{dataset_id}/summary",
            params={"page": 2, "page_size": 5, "search": "RECORD"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total_rows"], 12)
        self.assertEqual(payload["matching_rows"], 12)
        self.assertEqual(payload["current_page"], 2)
        self.assertEqual(payload["page_size"], 5)
        self.assertEqual(payload["preview_rows"][0]["label"], "record 5")

    def test_summary_api_sorts_before_pagination(self):
        dataset_id = self.register_dataset(
            "api-sorted.csv",
            pd.DataFrame({"score": [5, 100, 20, 1]}),
        )

        response = TestClient(app).get(
            f"/api/datasets/{dataset_id}/summary",
            params={"page": 2, "page_size": 1, "sort_by": "score", "sort_desc": "true"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["preview_rows"], [{"score": 20}])

    def test_sqlite_metadata_survives_new_store_connections_and_dataset_reopens(self):
        dataset_id = self.register_dataset(
            "persistent.csv",
            pd.DataFrame({"name": ["first", "second"], "amount": [5, 10]}),
        )

        history = TestClient(app).get("/api/datasets")
        summary = TestClient(app).get(f"/api/datasets/{dataset_id}/summary")

        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()[0]["id"], dataset_id)
        self.assertEqual(history.json()[0]["filename"], "persistent.csv")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.json()["total_rows"], 2)

    def test_dataset_metadata_and_source_survive_a_fresh_backend_process(self):
        dataset_id = self.register_dataset(
            "process-restart.csv",
            pd.DataFrame({"name": ["first", "second"], "amount": [5, 10]}),
        )
        environment = os.environ.copy()
        environment["DATA_DIR"] = self.temp_dir.name
        script = (
            "import json; "
            "from app.services.data_loader import DatasetStore, load_dataframe; "
            f"dataset_id = {dataset_id!r}; "
            "record = DatasetStore.get(dataset_id); "
            "print(json.dumps({'filename': record['filename'], "
            "'rows': len(load_dataframe(dataset_id))}))"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            capture_output=True,
            check=True,
            text=True,
        )

        self.assertEqual(
            json.loads(result.stdout),
            {"filename": "process-restart.csv", "rows": 2},
        )

    def test_upload_metadata_file_validation_and_delete_lifecycle(self):
        client = TestClient(app)
        with patch.object(settings, "upload_dir", self.temp_dir.name):
            empty = client.post(
                "/api/upload",
                files={"file": ("empty.csv", b"", "text/csv")},
            )
            unsupported = client.post(
                "/api/upload",
                files={"file": ("notes.txt", b"hello", "text/plain")},
            )
            malformed = client.post(
                "/api/upload",
                files={"file": ("broken.xlsx", b"not-an-excel-file", "application/octet-stream")},
            )
            first_upload = client.post(
                "/api/upload",
                files={"file": ("history.csv", b"label,value\na,1\nb,2\n", "text/csv")},
            )
            second_upload = client.post(
                "/api/upload",
                files={"file": ("history.csv", b"label,value\nc,3\nd,4\n", "text/csv")},
            )

            self.assertEqual(empty.status_code, 400)
            self.assertIn("empty", empty.json()["detail"].lower())
            self.assertEqual(unsupported.status_code, 400)
            self.assertEqual(malformed.status_code, 400)
            self.assertEqual(first_upload.status_code, 200)
            self.assertEqual(second_upload.status_code, 200)
            self.assertNotEqual(first_upload.json()["id"], second_upload.json()["id"])

            dataset_id = first_upload.json()["id"]
            history = client.get("/api/datasets")
            self.assertEqual(len(history.json()), 2)
            reopened = client.get(f"/api/datasets/{dataset_id}/summary")
            self.assertEqual(reopened.status_code, 200)
            self.assertEqual(reopened.json()["total_rows"], 2)

            deleted = client.delete(f"/api/datasets/{dataset_id}")
            self.assertEqual(deleted.status_code, 204)
            self.assertEqual(client.get(f"/api/datasets/{dataset_id}/summary").status_code, 404)
            self.assertEqual(len(client.get("/api/datasets").json()), 1)

    def test_missing_stored_file_and_invalid_id_return_clear_not_found(self):
        dataset_id = self.register_dataset(
            "missing-file.csv",
            pd.DataFrame({"amount": [1, 2]}),
        )
        stored_path = DatasetStore.get(dataset_id)["path"]
        stored_path.unlink()
        client = TestClient(app)

        missing_file = client.get(f"/api/datasets/{dataset_id}/summary")
        missing_report = client.get(f"/api/datasets/{dataset_id}/report.pdf")
        invalid_id = client.get("/api/datasets/not-a-dataset/summary")

        self.assertEqual(missing_file.status_code, 404)
        self.assertEqual(missing_report.status_code, 404)
        self.assertIn("stored file", missing_file.json()["detail"].lower())
        self.assertIn("stored file", missing_report.json()["detail"].lower())
        history = client.get("/api/datasets")
        self.assertEqual(history.json()[0]["status"], "missing")
        self.assertEqual(invalid_id.status_code, 404)

    def test_empty_chart_result_explains_detected_columns(self):
        with patch("app.services.chart_generator.load_dataframe", return_value=pd.DataFrame()):
            result = generate_charts("empty")

            self.assertEqual(result.charts, [])
            self.assertTrue(any("Detected columns: none" in item for item in result.diagnostics))

    def test_excel_header_cleanup_and_search_find_late_record(self):
        path = Path(self.temp_dir.name) / "late-match.xlsx"
        records = [
            ["Sales report", None, None],
            ["Customer", None, "Amount"],
            *[
                [f"customer {n}", f"segment {n}", n]
                for n in range(14)
            ],
            ["Excel Needle", "last segment", 14],
        ]
        pd.DataFrame(records).to_excel(path, index=False, header=False)
        dataset_id = path.stem
        DatasetStore.register(path, path.name, dataset_id)
        self.dataset_ids.append(dataset_id)

        loaded = load_dataframe(dataset_id)
        result = build_dataset_summary(dataset_id, search="EXCEL NEEDLE")

        self.assertEqual(list(loaded.columns), ["Customer", "Column 2", "Amount"])
        self.assertEqual(result.total_rows, 15)
        self.assertEqual(result.matching_rows, 1)
        self.assertEqual(result.preview_rows[0]["Customer"], "Excel Needle")


if __name__ == "__main__":
    unittest.main()
