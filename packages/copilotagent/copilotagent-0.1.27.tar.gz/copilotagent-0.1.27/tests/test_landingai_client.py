"""Tests for LandingAIClient."""

from unittest.mock import MagicMock, patch

import pytest

from copilotagent.landingai_client import LandingAIClient, LandingAIError


class TestLandingAIClientInit:
    """Tests for LandingAIClient initialization."""

    def test_init_with_valid_api_key(self):
        """Test initialization with a valid API key."""
        client = LandingAIClient(api_key="test-api-key")
        assert client.api_key == "test-api-key"
        assert client.timeout == 60
        assert client.max_retries == 2
        assert client.retry_wait_seconds == 30
        assert client.base_url == "https://api.va.landing.ai"

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        client = LandingAIClient(
            api_key="test-key",
            timeout=120,
            max_retries=5,
            retry_wait_seconds=10,
            base_url="https://custom.api.com/",
        )
        assert client.api_key == "test-key"
        assert client.timeout == 120
        assert client.max_retries == 5
        assert client.retry_wait_seconds == 10
        assert client.base_url == "https://custom.api.com"  # trailing slash stripped

    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises LandingAIError."""
        with pytest.raises(LandingAIError, match="API key is required"):
            LandingAIClient(api_key="")

    def test_init_with_none_api_key_raises_error(self):
        """Test that initialization with None API key raises LandingAIError."""
        with pytest.raises(LandingAIError, match="API key is required"):
            LandingAIClient(api_key=None)  # type: ignore[arg-type]


class TestExtractDocumentData:
    """Tests for extract_document_data method."""

    @patch("copilotagent.landingai_client.requests.post")
    def test_successful_extraction(self, mock_post):
        """Test successful document extraction."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "extracted_schema": {
                    "loan_amount": 350000,
                    "borrower_name": "John Doe",
                }
            }
        }
        mock_post.return_value = mock_response

        client = LandingAIClient(api_key="test-key")
        schema = {
            "type": "object",
            "properties": {
                "loan_amount": {"type": "number"},
                "borrower_name": {"type": "string"},
            },
        }

        result = client.extract_document_data(
            document_bytes=b"fake-pdf-content",
            schema=schema,
            filename="test.pdf",
        )

        assert result["extraction_method"] == "landingai-agentic"
        assert result["extracted_schema"]["loan_amount"] == 350000
        assert result["extracted_schema"]["borrower_name"] == "John Doe"
        mock_post.assert_called_once()

    @patch("copilotagent.landingai_client.requests.post")
    def test_extraction_with_image_file(self, mock_post):
        """Test extraction with image file."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"extracted_schema": {}}}
        mock_post.return_value = mock_response

        client = LandingAIClient(api_key="test-key")
        client.extract_document_data(
            document_bytes=b"fake-image-content",
            schema={"type": "object", "properties": {}},
            filename="document.jpg",
        )

        # Check that the correct field name was used for image
        call_args = mock_post.call_args
        files = call_args.kwargs.get("files") or call_args[1].get("files")
        assert files[0][0] == "image"

    @patch("copilotagent.landingai_client.requests.post")
    def test_extraction_api_error(self, mock_post):
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        client = LandingAIClient(api_key="test-key", max_retries=0)

        with pytest.raises(LandingAIError, match="Document extraction failed"):
            client.extract_document_data(
                document_bytes=b"fake-content",
                schema={"type": "object", "properties": {}},
            )

    @patch("copilotagent.landingai_client.requests.post")
    @patch("copilotagent.landingai_client.time.sleep")
    def test_retry_logic_on_failure(self, mock_sleep, mock_post):
        """Test retry logic when extraction fails."""
        # First two calls fail, third succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.ok = False
        mock_response_fail.status_code = 503
        mock_response_fail.text = "Service Unavailable"

        mock_response_success = MagicMock()
        mock_response_success.ok = True
        mock_response_success.json.return_value = {"data": {"extracted_schema": {"field": "value"}}}

        mock_post.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success,
        ]

        client = LandingAIClient(api_key="test-key", max_retries=2, retry_wait_seconds=1)
        result = client.extract_document_data(
            document_bytes=b"content",
            schema={"type": "object", "properties": {}},
        )

        assert result["extracted_schema"]["field"] == "value"
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2  # Called between retries

    @patch("copilotagent.landingai_client.requests.post")
    @patch("copilotagent.landingai_client.time.sleep")
    def test_retry_exhausted_raises_error(self, mock_sleep, mock_post):
        """Test that error is raised when all retries are exhausted."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_post.return_value = mock_response

        client = LandingAIClient(api_key="test-key", max_retries=2, retry_wait_seconds=1)

        with pytest.raises(LandingAIError, match="failed after 3 attempts"):
            client.extract_document_data(
                document_bytes=b"content",
                schema={"type": "object", "properties": {}},
            )

        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("copilotagent.landingai_client.requests.post")
    def test_network_error_handling(self, mock_post):
        """Test handling of network errors."""
        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        client = LandingAIClient(api_key="test-key", max_retries=0)

        with pytest.raises(LandingAIError, match="Network error"):
            client.extract_document_data(
                document_bytes=b"content",
                schema={"type": "object", "properties": {}},
            )

    @patch("copilotagent.landingai_client.requests.post")
    def test_timeout_error_handling(self, mock_post):
        """Test handling of timeout errors."""
        import requests

        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        client = LandingAIClient(api_key="test-key", max_retries=0)

        with pytest.raises(LandingAIError, match="Network error"):
            client.extract_document_data(
                document_bytes=b"content",
                schema={"type": "object", "properties": {}},
            )


class TestMimetypeDetection:
    """Tests for mimetype detection based on filename."""

    @patch("copilotagent.landingai_client.requests.post")
    def test_pdf_mimetype(self, mock_post):
        """Test PDF mimetype detection."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"extracted_schema": {}}}
        mock_post.return_value = mock_response

        client = LandingAIClient(api_key="test-key")
        client.extract_document_data(b"content", {}, "doc.pdf")

        call_args = mock_post.call_args
        files = call_args.kwargs.get("files") or call_args[1].get("files")
        assert files[0][0] == "pdf"  # field name
        assert files[0][1][2] == "application/pdf"  # mimetype

    @patch("copilotagent.landingai_client.requests.post")
    def test_jpeg_mimetype(self, mock_post):
        """Test JPEG mimetype detection."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"extracted_schema": {}}}
        mock_post.return_value = mock_response

        client = LandingAIClient(api_key="test-key")
        client.extract_document_data(b"content", {}, "image.jpeg")

        call_args = mock_post.call_args
        files = call_args.kwargs.get("files") or call_args[1].get("files")
        assert files[0][0] == "image"
        assert files[0][1][2] == "image/jpeg"

    @patch("copilotagent.landingai_client.requests.post")
    def test_png_mimetype(self, mock_post):
        """Test PNG mimetype detection."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"extracted_schema": {}}}
        mock_post.return_value = mock_response

        client = LandingAIClient(api_key="test-key")
        client.extract_document_data(b"content", {}, "scan.png")

        call_args = mock_post.call_args
        files = call_args.kwargs.get("files") or call_args[1].get("files")
        assert files[0][0] == "image"
        assert files[0][1][2] == "image/png"

    @patch("copilotagent.landingai_client.requests.post")
    def test_tiff_mimetype(self, mock_post):
        """Test TIFF mimetype detection."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"extracted_schema": {}}}
        mock_post.return_value = mock_response

        client = LandingAIClient(api_key="test-key")
        client.extract_document_data(b"content", {}, "document.tiff")

        call_args = mock_post.call_args
        files = call_args.kwargs.get("files") or call_args[1].get("files")
        assert files[0][0] == "image"
        assert files[0][1][2] == "image/tiff"

    @patch("copilotagent.landingai_client.requests.post")
    def test_default_to_pdf_for_unknown(self, mock_post):
        """Test that unknown extensions default to PDF."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"extracted_schema": {}}}
        mock_post.return_value = mock_response

        client = LandingAIClient(api_key="test-key")
        client.extract_document_data(b"content", {}, "document.xyz")

        call_args = mock_post.call_args
        files = call_args.kwargs.get("files") or call_args[1].get("files")
        assert files[0][0] == "pdf"
        assert files[0][1][2] == "application/pdf"

