import os
import unittest
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.main import app
from app.services.data_loader import save_upload
from app.utils.file_validator import validate_file_size


class UploadLimitTests(unittest.TestCase):
    def test_file_size_at_or_below_configured_limit_is_allowed(self):
        limit_bytes = 100 * 1024 * 1024

        validate_file_size(99 * 1024 * 1024, 100)
        validate_file_size(limit_bytes - 1, 100)
        validate_file_size(limit_bytes, 100)

    def test_file_size_above_configured_limit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "100 MiB"):
            validate_file_size(101 * 1024 * 1024, 100)

    def test_lower_configured_limit_is_enforced(self):
        lower_limit_bytes = 25 * 1024 * 1024

        validate_file_size(lower_limit_bytes, 25)
        with self.assertRaisesRegex(ValueError, "25 MiB"):
            validate_file_size(lower_limit_bytes + 1, 25)

    def test_environment_override_is_reported_and_enforced_consistently(self):
        with patch.dict(os.environ, {"MAX_UPLOAD_MB": "50"}):
            self.assertEqual(Settings().max_upload_mb, 50)

            with patch.object(settings, "max_upload_mb", 50):
                response = TestClient(app).get("/api/upload/config")

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"max_upload_mb": 50})
                validate_file_size(50 * 1024 * 1024, settings.max_upload_mb)
                with self.assertRaisesRegex(ValueError, "50 MiB"):
                    validate_file_size(
                        50 * 1024 * 1024 + 1,
                        settings.max_upload_mb,
                    )

    def test_upload_config_endpoint_returns_effective_server_limit(self):
        self.assertEqual(settings.max_upload_mb, 100)

        client = TestClient(app)
        response = client.get("/api/upload/config")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"max_upload_mb": 100})

    def test_streaming_upload_rejects_oversize_and_removes_partial_file(self):
        with TemporaryDirectory() as upload_dir:
            with patch.object(settings, "upload_dir", upload_dir):
                with self.assertRaisesRegex(ValueError, "1 MiB"):
                    save_upload(
                        BytesIO(b"x" * (1024 * 1024 + 1)),
                        "oversize.csv",
                        1,
                    )

            self.assertEqual(os.listdir(upload_dir), [])

    def test_streaming_upload_accepts_exactly_100_mib(self):
        class RepeatingReader:
            def __init__(self, size):
                self.remaining = size

            def read(self, size=-1):
                chunk_size = min(size, self.remaining)
                self.remaining -= chunk_size
                return b"x" * chunk_size

        max_bytes = 100 * 1024 * 1024
        with TemporaryDirectory() as upload_dir:
            with patch.object(settings, "upload_dir", upload_dir):
                _, file_path = save_upload(
                    RepeatingReader(max_bytes),
                    "exact-limit.csv",
                    100,
                )

            self.assertEqual(os.path.getsize(file_path), max_bytes)


if __name__ == "__main__":
    unittest.main()
