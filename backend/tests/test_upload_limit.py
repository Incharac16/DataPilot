import unittest

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.utils.file_validator import validate_file_size


class UploadLimitTests(unittest.TestCase):
    def test_file_size_at_or_below_configured_limit_is_allowed(self):
        limit_bytes = 100 * 1024 * 1024

        validate_file_size(limit_bytes - 1, 100)
        validate_file_size(limit_bytes, 100)

    def test_file_size_above_configured_limit_is_rejected(self):
        limit_bytes = 100 * 1024 * 1024

        with self.assertRaisesRegex(ValueError, "100 MB"):
            validate_file_size(limit_bytes + 1, 100)

    def test_lower_configured_limit_is_enforced(self):
        lower_limit_bytes = 25 * 1024 * 1024

        validate_file_size(lower_limit_bytes, 25)
        with self.assertRaisesRegex(ValueError, "25 MB"):
            validate_file_size(lower_limit_bytes + 1, 25)

    def test_upload_config_endpoint_returns_effective_server_limit(self):
        client = TestClient(app)
        response = client.get("/api/upload/config")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"max_upload_mb": settings.max_upload_mb})


if __name__ == "__main__":
    unittest.main()
