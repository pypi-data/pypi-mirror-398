"""
Test suite for MLflow Cloudsmith Plugin.

This module contains comprehensive tests for the CloudsmithArtifactRepository
implementation, including unit tests and integration tests.
"""

import os
import tempfile
import unittest
import time
from unittest.mock import Mock, patch
import logging

from plugin.cloudsmith_repository import CloudsmithArtifactRepository
from mlflow.entities import FileInfo


class TestCloudsmithArtifactRepository(unittest.TestCase):
    """Test cases for CloudsmithArtifactRepository."""

    def setUp(self):
        """Set up test fixtures."""
        self.artifact_uri = "cloudsmith://test-owner/test-repo"
        self.api_key = "test-api-key"

        # Mock environment variables
        self.env_patcher = patch.dict(
            os.environ,
            {
                "CLOUDSMITH_API_KEY": self.api_key,
                "CLOUDSMITH_DEBUG": "false",
                "MLFLOW_EXPERIMENT_ID": "test-experiment",
                "MLFLOW_RUN_ID": "test-run-12345",
            },
        )
        self.env_patcher.start()

        # Create repository instance
        self.repo = CloudsmithArtifactRepository(self.artifact_uri)

    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()

    def test_init_with_tracking_uri(self):
        """Test initialization with tracking URI parameter."""
        repo = CloudsmithArtifactRepository(
            self.artifact_uri,
            tracking_uri="http://localhost:5000",
        )
        self.assertEqual(repo.owner, "test-owner")
        self.assertEqual(repo.repository, "test-repo")

    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                CloudsmithArtifactRepository(self.artifact_uri)
            self.assertIn("CLOUDSMITH_API_KEY", str(context.exception))

    def test_parse_uri_basic(self):
        """Test basic URI parsing functionality."""
        owner, repository, base_path = CloudsmithArtifactRepository._parse_uri(
            "cloudsmith://owner/repo"
        )
        self.assertEqual(owner, "owner")
        self.assertEqual(repository, "repo")
        self.assertEqual(base_path, "")

    def test_parse_uri_with_path(self):
        """Test URI parsing with path."""
        owner, repository, base_path = CloudsmithArtifactRepository._parse_uri(
            "cloudsmith://owner/repo/path/to/artifacts"
        )
        self.assertEqual(owner, "owner")
        self.assertEqual(repository, "repo")
        self.assertEqual(base_path, "path/to/artifacts")

    def test_parse_uri_invalid_scheme(self):
        """Test URI parsing with invalid scheme."""
        with self.assertRaises(ValueError) as context:
            CloudsmithArtifactRepository._parse_uri("http://owner/repo")
        self.assertIn("Invalid Cloudsmith URI scheme", str(context.exception))

    def test_parse_uri_missing_repository(self):
        """Test URI parsing fails without repository."""
        with self.assertRaises(ValueError) as context:
            CloudsmithArtifactRepository._parse_uri("cloudsmith://owner")
        self.assertIn(
            "Must specify both owner and repository",
            str(context.exception),
        )

    def test_get_headers(self):
        """Test HTTP headers generation."""
        headers = self.repo._get_headers()
        self.assertEqual(headers["Authorization"], f"Bearer {self.api_key}")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertIn("mlflow-cloudsmith", headers["User-Agent"])

    def test_generate_package_metadata(self):
        """Test package metadata generation."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            metadata = self.repo._generate_package_metadata(
                "test/path/file.txt", temp_path
            )

            # Check basic metadata structure
            self.assertIn("name", metadata)
            self.assertIn("description", metadata)
            self.assertIn("tags", metadata)

            # Check MLflow context is included
            self.assertIn("test-experiment", metadata["description"])
            self.assertIn("test-run-12345", metadata["description"])

            # Check tags format
            tags = metadata["tags"]
            self.assertIn("mlflow", tags)
            self.assertIn("experiment-test-experiment", tags)
            self.assertIn("run-test-run-12345", tags)

        finally:
            os.unlink(temp_path)

    @patch("requests.post")
    @patch("requests.get")
    def test_upload_file_success(self, mock_get, mock_post):
        """Test successful file upload."""
        # Mock upload URL request (Cloudsmith returns 202 for upload URL)
        mock_upload_response = Mock()
        mock_upload_response.status_code = 202
        mock_upload_response.json.return_value = {
            "upload_url": "https://s3.example.com/upload",
            "upload_fields": {"key": "value"},
            "identifier": "test-file-identifier",
        }

        # Mock S3 upload
        mock_s3_response = Mock()
        mock_s3_response.status_code = 204

        # Mock package creation
        mock_package_response = Mock()
        mock_package_response.status_code = 201
        mock_package_response.json.return_value = {
            "slug": "test-package",
            "identifier_perm": "test-package-identifier",
        }

        # Mock package sync status check
        mock_sync_response = Mock()
        mock_sync_response.status_code = 200
        mock_sync_response.json.return_value = {
            "is_sync_completed": True,
            "is_sync_failed": False,
        }

        mock_post.side_effect = [
            mock_upload_response,
            mock_s3_response,
            mock_package_response,
        ]
        mock_get.return_value = mock_sync_response

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            result = self.repo._upload_file_to_cloudsmith(
                temp_path, "test/artifact.txt"
            )
            self.assertEqual(result, "test-package-identifier")
            # Upload process: upload URL, S3 upload, package creation, polling
            self.assertGreaterEqual(mock_post.call_count, 3)
            self.assertEqual(mock_get.call_count, 1)  # Sync status check

        finally:
            os.unlink(temp_path)

    @patch("requests.post")
    @patch("requests.put")
    @patch("requests.get")
    def test_upload_file_multipart_success(
        self, mock_get, mock_put, mock_post
    ):
        """Test successful multi-part upload (minimal path)."""
        # Force small CHUNK_SIZE so we don't create a huge file
        from plugin import cloudsmith_repository as csr
        original_chunk = csr.CHUNK_SIZE
        csr.CHUNK_SIZE = 10  # bytes
        try:
            # Prepare file larger than 2 chunks
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
                f.write(b"0123456789ABCDEFGHIJ")  # 20 bytes -> 2 chunks of 10
                temp_path = f.name

            # Mock sequence:
            # 1) POST upload URL (202)
            # 2) POST completion (200)
            # 3) POST package create (201)
            mock_upload_resp = Mock()
            mock_upload_resp.status_code = 202
            mock_upload_resp.json.return_value = {
                "upload_url": "https://upload.example.com/file",
                "upload_fields": {},
                "identifier": "multi-id-123",
            }
            mock_complete_resp = Mock()
            mock_complete_resp.status_code = 200
            mock_complete_resp.json.return_value = {}
            mock_pkg_resp = Mock()
            mock_pkg_resp.status_code = 201
            mock_pkg_resp.json.return_value = {
                "identifier_perm": "pkg-multi-identifier"
            }
            mock_post.side_effect = [
                mock_upload_resp,
                mock_complete_resp,
                mock_pkg_resp,
            ]

            # PUT per chunk
            mock_put_resp = Mock()
            mock_put_resp.status_code = 200
            mock_put.return_value = mock_put_resp

            # Sync polling GET
            mock_sync_resp = Mock()
            mock_sync_resp.status_code = 200
            mock_sync_resp.json.return_value = {
                "is_sync_completed": True,
                "is_sync_failed": False,
            }
            mock_get.return_value = mock_sync_resp

            result = self.repo._upload_file_to_cloudsmith(
                temp_path, "test/mp.bin"
            )
            self.assertEqual(result, "pkg-multi-identifier")
            # Ensure multi-part path used (>=2 PUT calls)
            self.assertGreaterEqual(mock_put.call_count, 2)
            # Ensure completion + package creation posts present
            self.assertEqual(mock_post.call_count, 3)
        finally:
            csr.CHUNK_SIZE = original_chunk
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch(
        "plugin.cloudsmith_repository.CloudsmithArtifactRepository."
        "_upload_file_to_cloudsmith"
    )
    def test_log_artifact(self, mock_upload):
        """Test log_artifact method."""
        mock_upload.return_value = "test-package-identifier"

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            self.repo.log_artifact(temp_path, "test/path")
            mock_upload.assert_called_once()

        finally:
            os.unlink(temp_path)

    @patch(
        "plugin.cloudsmith_repository.CloudsmithArtifactRepository."
        "_upload_file_to_cloudsmith"
    )
    def test_log_artifacts(self, mock_upload):
        """Test log_artifacts method."""
        mock_upload.return_value = "test-package-identifier"

        # Create temporary directory with files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1_path = os.path.join(temp_dir, "file1.txt")
            file2_path = os.path.join(temp_dir, "subdir", "file2.json")

            os.makedirs(os.path.dirname(file2_path), exist_ok=True)

            with open(file1_path, "w") as f:
                f.write("test content 1")
            with open(file2_path, "w") as f:
                f.write('{"test": "content"}')

            self.repo.log_artifacts(temp_dir, "test/artifacts")

            # Should upload both files
            self.assertEqual(mock_upload.call_count, 2)

    @patch("requests.get")
    def test_list_artifacts_success(self, mock_get):
        """Test successful artifact listing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "mlflow-test-file-run-123",
                "filename": "test.txt",
                "size": 100,
                "description": (
                    "MLflow artifact: test/file.txt "
                    "(experiment: test-exp, run: test-run)"
                ),
                "tags": {
                    "info": [
                        "mlflow",
                        "experiment-test-exp",
                        "run-test-run",
                        "path-test-file.txt",
                    ]
                },
                "cdn_url": "https://cdn.example.com/test.txt",
            }
        ]
        mock_get.return_value = mock_response

        artifacts = self.repo.list_artifacts()
        # At root, immediate child should be directory 'test'
        self.assertEqual(len(artifacts), 1)
        self.assertIsInstance(artifacts[0], FileInfo)
        self.assertTrue(artifacts[0].is_dir)
        self.assertEqual(artifacts[0].path, "test")

    @patch("requests.get")
    def test_list_artifacts_with_path_filter(self, mock_get):
        """Test artifact listing with path filtering."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "name": "mlflow-test1-run-123",
                "filename": "test1.txt",
                "size": 100,
                "description": (
                    "MLflow artifact: models/test1.txt "
                    "(experiment: test-exp, run: test-run)"
                ),
                "tags": {"info": ["mlflow", "path-models-test1.txt"]},
                "cdn_url": "https://cdn.example.com/test1.txt",
            },
            {
                "name": "mlflow-test2-run-123",
                "filename": "test2.txt",
                "size": 200,
                "description": (
                    "MLflow artifact: data/test2.txt "
                    "(experiment: test-exp, run: test-run)"
                ),
                "tags": {"info": ["mlflow", "path-data-test2.txt"]},
                "cdn_url": "https://cdn.example.com/test2.txt",
            },
        ]
        mock_get.return_value = mock_response

        # Test listing inside a path returns immediate children
        artifacts = self.repo.list_artifacts("models")
        self.assertEqual(len(artifacts), 1)
        self.assertFalse(artifacts[0].is_dir)
        self.assertEqual(artifacts[0].path, "models/test1.txt")

    def test_list_artifacts_empty(self):
        """Test artifact listing with no results."""
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            artifacts = self.repo.list_artifacts()
            self.assertEqual(len(artifacts), 0)


class TestCloudsmithIntegration(unittest.TestCase):
    """Integration tests for Cloudsmith API (requires real credentials)."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.api_key = os.getenv("CLOUDSMITH_API_KEY")
        self.owner = os.getenv("CLOUDSMITH_TEST_OWNER")
        self.repo_name = os.getenv("CLOUDSMITH_TEST_REPO")
        run_integration = os.getenv("CLOUDSMITH_RUN_INTEGRATION", "").lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

        if not (run_integration and self.api_key and self.owner and self.repo_name):
            self.skipTest(
                "Integration tests skipped."
                " Set CLOUDSMITH_RUN_INTEGRATION=1 and set"
                " CLOUDSMITH_API_KEY, CLOUDSMITH_TEST_OWNER,"
                " CLOUDSMITH_TEST_REPO."
            )

        self.artifact_uri = f"cloudsmith://{self.owner}/{self.repo_name}"

        # Set up MLflow context
        os.environ["MLFLOW_EXPERIMENT_ID"] = "integration-test"
        os.environ["MLFLOW_RUN_ID"] = f"test-run-{int(time.time())}"

        self.repo = CloudsmithArtifactRepository(self.artifact_uri)

    def test_integration_upload_and_list(self):
        """Test real upload and listing with Cloudsmith API."""
        # Create a test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_content = f"Integration test file created at {time.time()}"
            f.write(test_content)
            temp_path = f.name

        try:
            # Upload the file
            self.repo.log_artifact(temp_path, "integration/test")

            # List artifacts to verify upload
            artifacts = self.repo.list_artifacts()

            # Should have at least our uploaded file
            self.assertGreater(len(artifacts), 0)

            # Check for our specific file
            integration_artifacts = [a for a in artifacts if "integration" in a.path]
            self.assertGreater(len(integration_artifacts), 0)

        finally:
            os.unlink(temp_path)

    def test_integration_large_multipart_upload(self):  # pragma: no cover
        """Test a large (multi-part) upload path if integration enabled.

        Creates a file just over CHUNK_SIZE to force multi-part logic and
        verifies it appears in listing under the integration directory.
        """
        from plugin import cloudsmith_repository as csr
        import tempfile
        large_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                # Create sparse file of size CHUNK_SIZE + 1 byte
                f.seek(csr.CHUNK_SIZE)
                f.write(b"X")
                large_path = f.name

            # Upload (will trigger multi-part due to size)
            self.repo.log_artifact(large_path, "integration/large")

            # List artifacts under integration to ensure presence
            artifacts = self.repo.list_artifacts("integration")
            matched = [a for a in artifacts if "large" in a.path]
            self.assertTrue(matched, "Large multi-part artifact not found in listing")
        finally:
            if large_path and os.path.exists(large_path):
                os.unlink(large_path)


if __name__ == "__main__":
    # Set up logging for tests
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    unittest.main(verbosity=2)
