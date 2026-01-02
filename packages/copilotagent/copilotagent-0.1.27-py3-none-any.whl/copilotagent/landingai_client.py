"""LandingAI Client - Document extraction using LandingAI API.

This module provides a Python client for the LandingAI Agentic Document
Extraction API, enabling structured data extraction from PDF and image documents.
"""

from __future__ import annotations

import io
import json
import time
from typing import Any

import requests


class LandingAIError(Exception):
    """Raised when LandingAI extraction fails."""


class LandingAIClient:
    """Client for extracting structured data from documents using LandingAI.

    This class provides methods to extract structured data from PDF and image
    documents using the LandingAI Agentic Document Extraction API.

    Args:
        api_key: LandingAI API key for authentication
        timeout: Request timeout in seconds (default: 60)
        max_retries: Maximum number of retry attempts on failure (default: 2)
        retry_wait_seconds: Seconds to wait between retries (default: 30)
        base_url: Base URL for LandingAI API (default: https://api.va.landing.ai)

    Example:
        >>> client = LandingAIClient(api_key="your-api-key")
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "loan_amount": {"type": "number", "title": "Loan Amount"},
        ...         "borrower_name": {"type": "string", "title": "Borrower Name"}
        ...     }
        ... }
        >>> result = client.extract_document_data(pdf_bytes, schema)
        >>> print(result['extracted_schema'])
    """

    def __init__(
        self,
        api_key: str,
        timeout: int = 60,
        max_retries: int = 2,
        retry_wait_seconds: int = 30,
        base_url: str = "https://api.va.landing.ai",
    ) -> None:
        """Initialize LandingAI client."""
        if not api_key:
            raise LandingAIError("LandingAI API key is required")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_wait_seconds = retry_wait_seconds
        self.base_url = base_url.rstrip("/")

    def extract_document_data(
        self,
        document_bytes: bytes,
        schema: dict[str, Any],
        filename: str = "document.pdf",
    ) -> dict[str, Any]:
        """Extract structured data from a document using LandingAI.

        Uses the LandingAI Agentic Document Extraction API to parse and extract
        structured data from documents. Includes automatic retry logic for
        transient failures.

        Args:
            document_bytes: Document content as bytes (PDF or image)
            schema: JSON schema defining what data to extract. Format:
                {
                    "type": "object",
                    "properties": {
                        "field_name": {"type": "string", "title": "Field Name", "description": "..."},
                        "amount": {"type": "number", "title": "Amount", "description": "..."},
                        ...
                    }
                }
            filename: Name of the file being processed (default: "document.pdf")

        Returns:
            Dictionary containing extracted data and metadata:
            - extracted_schema: The extracted data matching the provided schema
            - extraction_method: Always "landingai-agentic"
            - raw_response: Full response data from the API

        Raises:
            LandingAIError: If extraction fails after all retries

        Example:
            >>> client = LandingAIClient(api_key="key")
            >>> schema = {"type": "object", "properties": {"name": {"type": "string"}}}
            >>> result = client.extract_document_data(pdf_bytes, schema)
            >>> print(result['extracted_schema']['name'])
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._do_extraction(document_bytes, schema, filename)
            except LandingAIError as e:
                last_error = e
                if attempt < self.max_retries:
                    print(f"[LandingAI] Attempt {attempt + 1} failed, retrying in {self.retry_wait_seconds}s...")
                    time.sleep(self.retry_wait_seconds)
                else:
                    print(f"[LandingAI] All {self.max_retries + 1} attempts failed")

        # If we get here, all retries failed
        raise LandingAIError(f"Document extraction failed after {self.max_retries + 1} attempts: {last_error}") from last_error

    def _do_extraction(
        self,
        document_bytes: bytes,
        schema: dict[str, Any],
        filename: str,
    ) -> dict[str, Any]:
        """Perform a single extraction attempt.

        Args:
            document_bytes: Document content as bytes
            schema: JSON schema for extraction
            filename: Name of the file

        Returns:
            Extraction result dictionary

        Raises:
            LandingAIError: If the extraction request fails
        """
        url = f"{self.base_url}/v1/tools/agentic-document-analysis"
        headers = {"Authorization": f"Basic {self.api_key}"}

        # Detect mimetype from filename extension
        file_ext = filename.lower().split(".")[-1] if "." in filename else "pdf"

        # Create file-like object from bytes
        file_obj = io.BytesIO(document_bytes)

        # Determine field name and mimetype based on file type
        if file_ext in ["jpg", "jpeg", "png", "gif", "tiff", "tif"]:
            # Use 'image' field name for image files
            field_name = "image"
            mimetype_map = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
                "tiff": "image/tiff",
                "tif": "image/tiff",
            }
            mimetype = mimetype_map.get(file_ext, "image/jpeg")
            print(f"[LandingAI] Sending {file_ext.upper()} as image")
        else:
            # Use 'pdf' field name for PDF files
            field_name = "pdf"
            mimetype = "application/pdf"

        files = [(field_name, (filename, file_obj, mimetype))]
        payload = {"fields_schema": json.dumps(schema)}

        # Debug logging
        print(f"[LandingAI Debug] Filename: {filename}, Extension: {file_ext}, Field: {field_name}, Mimetype: {mimetype}")

        try:
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=payload,
                timeout=self.timeout,
            )

            if not response.ok:
                raise LandingAIError(f"Document extraction failed (status {response.status_code}): {response.text}")

            result = response.json()

            # Extract the data from the response
            output_data = result.get("data", {})
            extracted_schema = output_data.get("extracted_schema", {})

            # Return structured result
            return {
                "extracted_schema": extracted_schema,
                "extraction_method": "landingai-agentic",
                "raw_response": output_data,
            }

        except requests.exceptions.RequestException as e:
            raise LandingAIError(f"Network error during extraction: {e}") from e
        except LandingAIError:
            raise
        except Exception as e:
            raise LandingAIError(f"Unexpected error during extraction: {e}") from e

