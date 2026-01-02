"""blendConnect - Interface to Blend API.

This module provides a Python interface to the Blend API for mortgage lending
applications, documents, and follow-ups management.
"""

from __future__ import annotations

import base64
from functools import wraps
from typing import Any

import requests


class blendConnectError(Exception):
    """Base exception for blendConnect errors."""


class APIError(blendConnectError):
    """Raised when an API request fails."""


class blendConnect:
    """Client for interacting with Blend API.

    This class provides methods to:
    - Get authentication status
    - List and retrieve applications
    - Manage application documents
    - Create and manage follow-ups

    Args:
        api_key: Blend API Secret Key (base64 encoded)
        target_instance: Blend target instance identifier (e.g., 'allwestern')
        api_base_url: Base URL for Blend API (default: https://api.blendlabs.com)
        api_version: Blend API version (default: '11.0.0')
    """

    def __init__(
        self,
        api_key: str,
        target_instance: str,
        api_base_url: str = "https://api.blendlabs.com",
        api_version: str = "11.0.0",
    ) -> None:
        """Initialize blendConnect client."""
        if not api_key or not isinstance(api_key, str):
            raise ValueError("api_key must be a non-empty string")
        if not target_instance or not isinstance(target_instance, str):
            raise ValueError("target_instance must be a non-empty string")

        self.api_key = api_key
        self.target_instance = target_instance
        self.api_base_url = api_base_url.rstrip("/")
        self.api_version = api_version

    def _get_headers(self) -> dict[str, str]:
        """Get common headers for Blend API requests.

        Returns:
            Dictionary of HTTP headers
        """
        return {
            'accept': 'application/json',
            'blend-api-version': self.api_version,
            'cache-control': 'no-cache',
            'Content-Type': 'application/json',
            'blend-target-instance': self.target_instance,
            'authorization': f'Bearer {self.api_key}',
        }

    def get_current_user(self) -> dict[str, Any]:
        """Get authentication status from Blend API.

        Reference: https://developers.blend.com/blend/docs/blend-api-quick-start-guide

        Returns:
            Dictionary containing authentication status

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> status = client.get_current_user()
            >>> print(status)
        """
        url = f"{self.api_base_url}/authentication-status"
        headers = self._get_headers()

        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                raise APIError(f"Authentication status check failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during authentication status check: {e}") from e

    def list_applications(
        self,
        limit: int | None = None,
        cursor: str | None = None,
        los_id_exists: str | None = None,
        crm_id_eq: str | None = None,
        party_email_eq: str | None = None,
        exportable: bool | None = None,
        los_id_eq: str | None = None,
        archived_status: bool | None = None,
        sort_by_timestamp: str | None = None,
        solution_sub_type: str | None = None,
        custom_field_query: str | None = None,
        ignore_archived_status: bool | None = None,
    ) -> dict[str, Any]:
        """Get a paginated list of active applications from Blend API.

        Reference: https://developers.blend.com/blend/docs/list-home-lending-applications

        Args:
            limit: Number of applications (1-100, default: 50)
            cursor: Pagination cursor
            los_id_exists: 'true' or 'false' to filter by losId presence
            crm_id_eq: Filter by crmId
            party_email_eq: Filter by party email
            exportable: Filter by exportable status
            los_id_eq: Filter by losId
            archived_status: Filter by archived status (default: false)
            sort_by_timestamp: 'asc' or 'desc' (default: 'desc')
            solution_sub_type: Filter by solution subtype
            custom_field_query: Filter by custom field key-value pair
            ignore_archived_status: Return loans regardless of archived status

        Returns:
            Dictionary containing paginated applications list

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> apps = client.list_applications(limit=10, sort_by_timestamp='desc')
            >>> for app in apps.get('applications', []):
            ...     print(app['id'])
        """
        url = f"{self.api_base_url}/home-lending/applications"
        headers = self._get_headers()

        # Build query parameters
        params = {}
        if limit is not None:
            params['limit'] = limit
        if cursor is not None:
            params['cursor'] = cursor
        if los_id_exists is not None:
            params['losId-exists'] = los_id_exists
        if crm_id_eq is not None:
            params['crmId-eq'] = crm_id_eq
        if party_email_eq is not None:
            params['party-email-eq'] = party_email_eq
        if exportable is not None:
            params['exportable'] = str(exportable).lower()
        if los_id_eq is not None:
            params['losId-eq'] = los_id_eq
        if archived_status is not None:
            params['archivedStatus'] = str(archived_status).lower()
        if sort_by_timestamp is not None:
            params['sort-by-timestamp'] = sort_by_timestamp
        if solution_sub_type is not None:
            params['solution-sub-type'] = solution_sub_type
        if custom_field_query is not None:
            params['custom_field_query'] = custom_field_query
        if ignore_archived_status is not None:
            params['ignoreArchivedStatus'] = str(ignore_archived_status).lower()

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                raise APIError(f"List applications failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during list applications: {e}") from e

    def get_application(self, application_id: str, format: str = "json") -> dict[str, Any]:
        """Get application data by ID from Blend API.

        Reference: https://developers.blend.com/blend/docs/get-application-data

        Args:
            application_id: The UUID of the loan/application in Blend's system
            format: Response format - 'json', 'fannie', or 'mismo' (default: 'json')

        Returns:
            Dictionary containing application data

        Raises:
            APIError: If the API request fails
            ValueError: If format is invalid

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> app = client.get_application("uuid-of-application")
            >>> print(app['borrower']['firstName'])
        """
        if format not in ['json', 'fannie', 'mismo']:
            raise ValueError(f"format must be one of: json, fannie, mismo")

        url = f"{self.api_base_url}/home-lending/applications/{application_id}"
        headers = self._get_headers()
        params = {'format': format}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 404:
                raise APIError(f"Application not found: {application_id}")
            if response.status_code != 200:
                raise APIError(f"Get application failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during get application: {e}") from e

    def get_application_documents(
        self,
        application_id: str,
        include_all_documents: bool = False,
        show_associated_fields: bool = False,
    ) -> dict[str, Any]:
        """Get a list of all uploaded and signature complete documents on a specific application.

        Reference: https://developers.blend.com/blend/docs/get-application-documents

        Args:
            application_id: The UUID of the application in Blend's system
            include_all_documents: If true, returns all documents including signature pending (default: False)
            show_associated_fields: Toggles whether associated fields are shown (default: False)

        Returns:
            Dictionary containing documents list

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> docs = client.get_application_documents("uuid-of-application")
            >>> for doc in docs.get('documents', []):
            ...     print(f"{doc['id']}: {doc['title']}")
        """
        url = f"{self.api_base_url}/home-lending/applications/{application_id}/documents"
        headers = self._get_headers()
        params = {
            'includeAllDocuments': str(include_all_documents).lower(),
            'showAssociatedFields': str(show_associated_fields).lower()
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 404:
                raise APIError(f"Application not found: {application_id}")
            if response.status_code != 200:
                raise APIError(f"Get application documents failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during get application documents: {e}") from e

    def get_document(self, document_id: str) -> dict[str, Any]:
        """Download document binary data from Blend API.

        Reference: https://developers.blend.com/blend/docs/get-document-data

        Args:
            document_id: The UUID of the document in Blend's system

        Returns:
            Dictionary containing:
            - content_type: MIME type of the document
            - content_disposition: Content disposition header
            - size_bytes: Size of the document in bytes
            - data: Base64 encoded document binary data

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> doc = client.get_document("uuid-of-document")
            >>> # Decode base64 to get binary
            >>> import base64
            >>> binary_data = base64.b64decode(doc['data'])
            >>> with open('document.pdf', 'wb') as f:
            ...     f.write(binary_data)
        """
        url = f"{self.api_base_url}/documents/{document_id}"
        headers = self._get_headers()
        headers['accept'] = 'text/plain'

        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 404:
                raise APIError(f"Document not found: {document_id}")
            if response.status_code != 200:
                raise APIError(f"Get document failed (status {response.status_code}): {response.text}")

            # Read binary data
            binary_data = response.content
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            content_disposition = response.headers.get('Content-Disposition', '')

            # Base64 encode the binary data for JSON transport
            encoded_data = base64.b64encode(binary_data).decode('utf-8')

            return {
                'content_type': content_type,
                'content_disposition': content_disposition,
                'size_bytes': len(binary_data),
                'data': encoded_data  # Base64 encoded document data
            }

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during get document: {e}") from e

    def download_document(self, document_id: str) -> bytes:
        """Download document as raw bytes.

        This is a convenience method that returns the document binary data directly.

        Args:
            document_id: The UUID of the document in Blend's system

        Returns:
            Document content as bytes

        Raises:
            APIError: If the download fails

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> pdf_bytes = client.download_document("uuid-of-document")
            >>> with open("document.pdf", "wb") as f:
            ...     f.write(pdf_bytes)
        """
        doc_data = self.get_document(document_id)
        return base64.b64decode(doc_data['data'])

    def get_follow_ups(self, application_id: str, status: str | None = None) -> dict[str, Any]:
        """Get follow-ups on a specific application from Blend API.

        Reference: https://developers.blend.com/blend/docs/list-follow-ups-for-an-application

        Args:
            application_id: The UUID of the application in Blend's system
            status: Optional follow-up status to filter by
                Valid values: REQUESTED, IN_PROGRESS, COMPLETED, COMPLETED_EXTERNALLY,
                             PENDING_REVIEW, REJECTED, CANCELLED, SUGGESTED, WAIVED

        Returns:
            Dictionary containing follow-ups list

        Raises:
            APIError: If the API request fails
            ValueError: If status is invalid

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> follow_ups = client.get_follow_ups("uuid-of-application")
            >>> for fu in follow_ups.get('followUps', []):
            ...     print(f"{fu['id']}: {fu['type']} - {fu['status']}")
        """
        if status:
            valid_statuses = [
                'REQUESTED', 'IN_PROGRESS', 'COMPLETED', 'COMPLETED_EXTERNALLY',
                'PENDING_REVIEW', 'REJECTED', 'CANCELLED', 'SUGGESTED', 'WAIVED'
            ]
            if status not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")

        url = f"{self.api_base_url}/follow-ups"
        headers = self._get_headers()
        headers['accept'] = 'application/json; charset=utf-8'

        params = {'applicationId': application_id}
        if status:
            params['status'] = status

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                raise APIError(f"Get follow-ups failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during get follow-ups: {e}") from e

    def create_follow_up(self, follow_up_data: dict[str, Any]) -> dict[str, Any]:
        """Create a follow-up for an applicant on a specific application in Blend API.

        Reference: https://developers.blend.com/blend/reference/post-follow-up

        Args:
            follow_up_data: Dict containing follow-up details
                Required fields:
                - applicationId: UUID of the application
                - type: Follow-up type (e.g., DOCUMENT_REQUEST, PAYSTUBS, W2, etc.)
                - context: Context object with partyId and type-specific fields
                Optional fields:
                - comments: Additional comments
                - clientFollowUpReferenceId: External reference ID
                - dueDate: Due date for the follow-up
                - status: Initial status (defaults to REQUESTED)

        Returns:
            Dictionary containing created follow-up data

        Raises:
            APIError: If the API request fails
            ValueError: If required fields are missing

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> follow_up = client.create_follow_up({
            ...     'applicationId': 'uuid-of-application',
            ...     'type': 'DOCUMENT_REQUEST',
            ...     'context': {
            ...         'partyId': 'uuid-of-party',
            ...         'title': 'Please upload your W2'
            ...     }
            ... })
            >>> print(follow_up['id'])
        """
        if not follow_up_data or not isinstance(follow_up_data, dict):
            raise ValueError("follow_up_data must be a non-empty dictionary")

        if 'applicationId' not in follow_up_data:
            raise ValueError("follow_up_data must include 'applicationId' field")

        if 'type' not in follow_up_data:
            raise ValueError("follow_up_data must include 'type' field")

        url = f"{self.api_base_url}/follow-ups"
        headers = self._get_headers()
        headers['accept'] = 'application/json; charset=utf-8'

        try:
            response = requests.post(url, headers=headers, json=follow_up_data, timeout=30)

            if response.status_code not in (200, 201):
                raise APIError(f"Create follow-up failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during create follow-up: {e}") from e

    def get_follow_up_by_id(self, follow_up_id: str) -> dict[str, Any]:
        """Get a specific follow-up by ID from Blend API.

        Reference: https://developers.blend.com/blend/reference/get-follow-up

        Args:
            follow_up_id: The UUID of the follow-up in Blend's system

        Returns:
            Dictionary containing follow-up data

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> follow_up = client.get_follow_up_by_id("uuid-of-follow-up")
            >>> print(f"{follow_up['type']}: {follow_up['status']}")
        """
        url = f"{self.api_base_url}/follow-ups/{follow_up_id}"
        headers = self._get_headers()
        headers['accept'] = 'application/json; charset=utf-8'

        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 404:
                raise APIError(f"Follow-up not found: {follow_up_id}")
            if response.status_code != 200:
                raise APIError(f"Get follow-up failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during get follow-up: {e}") from e

    def update_follow_up(self, follow_up_id: str, update_data: dict[str, Any]) -> dict[str, Any]:
        """Update a specific follow-up in Blend API.

        Reference: https://developers.blend.com/blend/reference/patch-follow-up

        Args:
            follow_up_id: The UUID of the follow-up in Blend's system
            update_data: Dict containing update fields
                Optional fields:
                - status: Updated status (COMPLETED_EXTERNALLY, CANCELLED, etc.)
                - comments: Additional comments
                - clientFollowUpReferenceId: External reference ID
                - dueDate: Updated due date
                - context: Updated context (e.g., document title)

        Returns:
            Dictionary containing updated follow-up data

        Raises:
            APIError: If the API request fails
            ValueError: If update_data is invalid

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> updated = client.update_follow_up(
            ...     "uuid-of-follow-up",
            ...     {'status': 'COMPLETED_EXTERNALLY'}
            ... )
            >>> print(updated['status'])
        """
        if not update_data or not isinstance(update_data, dict):
            raise ValueError("update_data must be a non-empty dictionary")

        url = f"{self.api_base_url}/follow-ups/{follow_up_id}"
        headers = self._get_headers()
        headers['accept'] = 'application/json; charset=utf-8'

        try:
            response = requests.patch(url, headers=headers, json=update_data, timeout=30)

            if response.status_code == 404:
                raise APIError(f"Follow-up not found: {follow_up_id}")
            if response.status_code != 200:
                raise APIError(f"Update follow-up failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during update follow-up: {e}") from e

    def delete_follow_up(self, follow_up_id: str) -> bool:
        """Delete a specific follow-up from Blend API.

        Reference: https://developers.blend.com/blend/reference/remove-a-specific-follow-up

        Args:
            follow_up_id: The UUID of the follow-up in Blend's system

        Returns:
            True if successful

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = BlendConnect(api_key, target_instance)
            >>> client.delete_follow_up("uuid-of-follow-up")
            True
        """
        url = f"{self.api_base_url}/follow-ups/{follow_up_id}"
        headers = self._get_headers()
        headers['accept'] = 'application/json; charset=utf-8'

        try:
            response = requests.delete(url, headers=headers, timeout=30)

            if response.status_code == 404:
                raise APIError(f"Follow-up not found: {follow_up_id}")
            if response.status_code != 200:
                raise APIError(f"Delete follow-up failed (status {response.status_code}): {response.text}")

            return True

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during delete follow-up: {e}") from e

    def post_document(self, document_data: dict[str, Any]) -> dict[str, Any]:
        """Upload a loan document to Blend API using multipart/form-data.

        Reference: https://developers.blend.com/blend/reference/post-document

        Args:
            document_data: Dict containing document details
                Required fields:
                - applicationId (str): The UUID of the application in Blend's system
                - type (str): Blend document type (e.g., 'BANK_STATEMENT', 'W2', etc.)
                - file (str): Base64 encoded file content
                - fileName (str): Name of the file (e.g., 'bank_statement.pdf')
                Optional fields:
                - losType (str): LOS document type
                - losTypeId (str): LOS document id for external tracking
                - partyIds (list): UUIDs of parties associated with this document
                - name (str): Document name/title
                - status (str): Document status ('SIGNATURE_REQUESTED' or 'READY')
                - shareWithAllParties (bool): Make document accessible to borrowers (default: false)
                - customFields (dict): Custom fields key-value pairs
                - customMetadata (dict): Custom metadata key-value pairs

        Returns:
            Dictionary containing uploaded document data with 'id' field

        Raises:
            APIError: If the API request fails
            ValueError: If required fields are missing

        Example:
            >>> import base64
            >>> client = BlendConnect(api_key, target_instance)
            >>> with open('bank_statement.pdf', 'rb') as f:
            ...     file_content = base64.b64encode(f.read()).decode('utf-8')
            >>> doc = client.post_document({
            ...     'applicationId': 'uuid-of-application',
            ...     'type': 'BANK_STATEMENT',
            ...     'file': file_content,
            ...     'fileName': 'bank_statement.pdf',
            ...     'shareWithAllParties': False
            ... })
            >>> print(f"Uploaded document ID: {doc['id']}")
        """
        if not document_data or not isinstance(document_data, dict):
            raise ValueError("document_data must be a non-empty dictionary")

        # Validate required fields
        required_fields = ['applicationId', 'type', 'file', 'fileName']
        for field in required_fields:
            if field not in document_data:
                raise ValueError(f"document_data must include '{field}' field")

        url = f"{self.api_base_url}/documents"
        headers = self._get_headers()
        headers['accept'] = 'application/json'
        # Remove Content-Type as requests will set it with boundary for multipart
        headers.pop('Content-Type', None)

        # Prepare multipart form data
        import base64

        files_data = {}
        form_data = {}

        # Decode base64 file content
        file_content = base64.b64decode(document_data['file'])
        file_name = document_data['fileName']

        # Add file to files dictionary
        files_data['file'] = (file_name, file_content, 'application/octet-stream')

        # Add all other fields to form data
        for key, value in document_data.items():
            if key not in ['file', 'fileName']:
                if isinstance(value, (dict, list)):
                    import json
                    form_data[key] = json.dumps(value)
                else:
                    form_data[key] = str(value)

        try:
            response = requests.post(url, headers=headers, data=form_data, files=files_data, timeout=60)

            if response.status_code == 404:
                raise APIError(f"Application not found: {document_data.get('applicationId')}")
            if response.status_code not in (200, 201):
                raise APIError(f"Upload document failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during upload document: {e}") from e
