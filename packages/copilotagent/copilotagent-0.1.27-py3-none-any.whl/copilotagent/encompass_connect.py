"""EncompassConnect - Interface to Encompass API.

This module provides a Python interface to the ICE Mortgage Technology (Encompass)
API for field operations and document management.
"""

from __future__ import annotations

import warnings
from functools import wraps
from typing import Any

import requests

from copilotagent.landingai_client import LandingAIClient, LandingAIError


class EncompassConnectError(Exception):
    """Base exception for EncompassConnect errors."""


class TokenRefreshError(EncompassConnectError):
    """Raised when token refresh fails."""


class APIError(EncompassConnectError):
    """Raised when an API request fails."""


# Re-export LandingAIError for backward compatibility
__all__ = ["EncompassConnect", "EncompassConnectError", "TokenRefreshError", "APIError", "LandingAIError"]


class EncompassConnect:
    """Client for interacting with the Encompass API.

    This class provides methods to:
    - Read and write loan fields
    - Retrieve document metadata
    - Download document attachments

    Note:
        For document extraction using LandingAI, use the dedicated LandingAIClient class.
        The extract_document_data method on this class is deprecated and will be removed
        in a future version.

    Args:
        access_token: Encompass API access token (impersonation token)
        landingai_api_key: LandingAI API key for document extraction (deprecated, use LandingAIClient)
        api_base_url: Base URL for Encompass API (default: https://api.elliemae.com)
        credentials: Dictionary containing credentials for token refresh:
            For client_credentials flow (API users / test environments):
            - client_id: OAuth client ID
            - client_secret: OAuth client secret
            - instance_id: Encompass instance ID

            For password + impersonation flow (production with regular users):
            - username: Encompass username
            - password: Encompass password
            - client_id: OAuth client ID
            - client_secret: OAuth client secret
            - instance_id: Encompass instance ID
            - subject_user_id: User ID to impersonate
    """

    def __init__(
        self,
        access_token: str | None = None,
        landingai_api_key: str | None = None,
        api_base_url: str = "https://api.elliemae.com",
        credentials: dict[str, str] | None = None,
    ) -> None:
        """Initialize EncompassConnect client."""
        self.access_token = access_token or ""
        self.landingai_api_key = landingai_api_key
        self.api_base_url = api_base_url.rstrip("/")
        self.credentials = credentials or {}
        self._auth_flow: str | None = None  # Will be set based on credentials

        # Determine auth flow based on available credentials
        # Check for NON-EMPTY values, not just key existence
        if self.credentials:
            client_creds_fields = ["client_id", "client_secret", "instance_id"]
            password_extra_fields = ["username", "password", "subject_user_id"]
            
            # Check if values are present and non-empty
            has_client_creds = all(self.credentials.get(f) for f in client_creds_fields)
            has_password_creds = all(self.credentials.get(f) for f in password_extra_fields)
            
            if has_client_creds and has_password_creds:
                # Has all credentials - use password + impersonation flow
                self._auth_flow = "password"
            elif has_client_creds:
                # Only has client credentials - use client_credentials flow
                self._auth_flow = "client_credentials"
            else:
                # Check what's missing
                missing_client = [f for f in client_creds_fields if not self.credentials.get(f)]
                if missing_client:
                    raise ValueError(f"Missing required credential fields: {', '.join(missing_client)}")
        
        # If no access token provided but we have credentials, get one now
        if not self.access_token and self.credentials:
            self.refresh_token()

    def _check_token_validity(self) -> bool:
        """Check if the current access token is valid.

        Returns:
            True if the token is valid, False otherwise.
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/encompass/v1/company/users/me",
                headers={"Authorization": f"Bearer {self.access_token}", "Accept": "application/json"},
                timeout=10,
            )
            return response.status_code == 200
        except Exception:
            return False

    def refresh_token(self) -> str:
        """Refresh the access token using stored credentials.

        Supports two OAuth flows:
        1. Client Credentials flow (for API users / test environments)
           - Uses client_id, client_secret, instance_id
        2. Password + Impersonation flow (for production with regular users)
           - Uses username, password, client_id, client_secret, instance_id, subject_user_id

        Returns:
            New access token

        Raises:
            TokenRefreshError: If token refresh fails or credentials are not set
        """
        if not self.credentials:
            raise TokenRefreshError("Cannot refresh token: credentials not provided during initialization")

        try:
            if self._auth_flow == "client_credentials":
                # Client Credentials flow (for API users / test environments)
                response = requests.post(
                    f"{self.api_base_url}/oauth2/v1/token",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.credentials["client_id"],
                        "client_secret": self.credentials["client_secret"],
                        "instance_id": self.credentials["instance_id"],
                        "scope": "lp",
                    },
                    timeout=10,
                )

                if response.status_code != 200:
                    raise TokenRefreshError(f"Failed to get access token (client_credentials): {response.text}")

                token = response.json().get("access_token")
                if not token:
                    raise TokenRefreshError("No access_token in client_credentials response")

                self.access_token = token

            else:
                # Password + Impersonation flow (default for production)
                # Step 1: Get Super Admin token
                response = requests.post(
                    f"{self.api_base_url}/oauth2/v1/token",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "password",
                        "username": f"{self.credentials['username']}@encompass:{self.credentials['instance_id']}",
                        "password": self.credentials["password"],
                        "client_id": self.credentials["client_id"],
                        "client_secret": self.credentials["client_secret"],
                        "scope": "lp",
                    },
                    timeout=10,
                )

                if response.status_code != 200:
                    raise TokenRefreshError(f"Failed to get Super Admin token: {response.text}")

                actor_token = response.json().get("access_token")
                if not actor_token:
                    raise TokenRefreshError("No access_token in Super Admin token response")

                # Step 2: Get Impersonation token
                response = requests.post(
                    f"{self.api_base_url}/oauth2/v1/token",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                        "actor_token_type": "urn:ietf:params:oauth:token-type:access_token",
                        "subject_user_id": self.credentials["subject_user_id"],
                        "actor_token": actor_token,
                        "scope": "lp",
                        "client_id": self.credentials["client_id"],
                        "client_secret": self.credentials["client_secret"],
                    },
                    timeout=10,
                )

                if response.status_code != 200:
                    raise TokenRefreshError(f"Failed to get Impersonation token: {response.text}")

                impersonation_token = response.json().get("access_token")
                if not impersonation_token:
                    raise TokenRefreshError("No access_token in Impersonation token response")

                self.access_token = impersonation_token

            return self.access_token

        except requests.exceptions.RequestException as e:
            raise TokenRefreshError(f"Network error during token refresh: {e}") from e
        except KeyError as e:
            raise TokenRefreshError(f"Missing credential field: {e}") from e

    def _auto_refresh_on_401(func):  # noqa: N805
        """Decorator to automatically refresh token on 401 Unauthorized responses."""

        @wraps(func)
        def wrapper(self, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003, ANN202
            try:
                return func(self, *args, **kwargs)
            except APIError as e:
                # Check if it's a 401 error
                if "401" in str(e) or "Unauthorized" in str(e):
                    # Try to refresh the token
                    try:
                        self.refresh_token()
                        # Retry the original function with the new token
                        return func(self, *args, **kwargs)
                    except TokenRefreshError:
                        # If refresh fails, re-raise the original error
                        raise e from None
                # If not a 401 error, re-raise
                raise

        return wrapper

    @_auto_refresh_on_401
    def get_field(self, loan_id: str, field_ids: str | list[str]) -> dict[str, Any]:
        """Retrieve one or multiple loan fields.

        Args:
            loan_id: The loan GUID
            field_ids: Single field ID string or list of field IDs

        Returns:
            Dictionary mapping field IDs to their values

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> # Get single field
            >>> result = client.get_field("loan-guid", "4000")
            >>> # Get multiple fields
            >>> result = client.get_field("loan-guid", ["4000", "4002", "4004"])
        """
        # Normalize input to list
        if isinstance(field_ids, str):
            field_ids = [field_ids]

        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/fieldReader"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
        }

        try:
            response = requests.post(url, json=field_ids, headers=headers, timeout=30)

            if response.status_code != 200:
                raise APIError(f"Field read failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during field read: {e}") from e

    @_auto_refresh_on_401
    def write_field(self, loan_id: str, field_id: str, value: Any) -> bool:
        """Write a single loan field value.

        Args:
            loan_id: The loan GUID
            field_id: The field ID to write
            value: The value to set

        Returns:
            True if successful

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> client.write_field("loan-guid", "4000", 350000)
        """
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
        }

        # Construct the payload with the field to update
        payload = {field_id: value}

        try:
            response = requests.patch(url, json=payload, headers=headers, timeout=30)

            if response.status_code not in (200, 204):
                raise APIError(f"Field write failed (status {response.status_code}): {response.text}")

            return True

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during field write: {e}") from e

    @_auto_refresh_on_401
    def write_fields(self, loan_id: str, updates: dict[str, Any]) -> bool:
        """Write multiple loan field values at once using Field Writer API.

        Args:
            loan_id: The loan GUID
            updates: Dictionary mapping field IDs to values

        Returns:
            True if successful

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> client.write_fields("loan-guid", {"4000": 350000, "4002": "John"})
        """
        if not updates:
            return True

        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/fieldWriter"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
        }

        # Field Writer expects array of {id, value, lock} objects
        payload = [{"id": field_id, "value": value, "lock": False} for field_id, value in updates.items()]

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code not in (200, 204):
                raise APIError(f"Field write failed (status {response.status_code}): {response.text}")

            return True

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during field write: {e}") from e

    @_auto_refresh_on_401
    def get_disclosure_tracking(self, loan_id: str) -> dict[str, Any]:
        """Get disclosure tracking information for a loan.

        Args:
            loan_id: The loan GUID

        Returns:
            Dictionary containing disclosure tracking data

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> tracking = client.get_disclosure_tracking("loan-guid")
        """
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/disclosureTracking2015"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            response = requests.get(url, headers=headers, timeout=60)

            if response.status_code == 404:
                return {"found": False, "message": "No disclosure tracking data"}
            if response.status_code != 200:
                raise APIError(f"Disclosure tracking failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during disclosure tracking: {e}") from e

    @_auto_refresh_on_401
    def get_milestones(self, loan_id: str) -> list[dict[str, Any]]:
        """Get all milestones for a loan.

        Args:
            loan_id: The loan GUID

        Returns:
            List of milestone dictionaries

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> milestones = client.get_milestones("loan-guid")
        """
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/milestones"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            response = requests.get(url, headers=headers, timeout=60)

            if response.status_code != 200:
                raise APIError(f"Milestones retrieval failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during milestones retrieval: {e}") from e

    @_auto_refresh_on_401
    def run_mavent(self, loan_id: str, run_type: str = "FULL") -> dict[str, Any]:
        """Run Mavent compliance check for a loan.

        Args:
            loan_id: The loan GUID
            run_type: Type of Mavent run ("FULL", "QUICK", etc.)

        Returns:
            Dictionary containing Mavent results

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> result = client.run_mavent("loan-guid")
        """
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/associates/mavent"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
        }
        payload = {"runType": run_type}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)

            if response.status_code not in (200, 201, 202):
                raise APIError(f"Mavent run failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during Mavent run: {e}") from e

    @_auto_refresh_on_401
    def get_mavent_results(self, loan_id: str) -> dict[str, Any]:
        """Get Mavent compliance results for a loan.

        Args:
            loan_id: The loan GUID

        Returns:
            Dictionary containing Mavent results

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> results = client.get_mavent_results("loan-guid")
        """
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/associates/mavent"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        params = {"view": "results"}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)

            if response.status_code == 404:
                return {"found": False, "message": "No Mavent results"}
            if response.status_code != 200:
                raise APIError(f"Mavent results failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during Mavent results: {e}") from e

    @_auto_refresh_on_401
    def order_disclosure(self, loan_id: str, disclosure_type: str = "LE", delivery_method: str = "eDisclosure") -> dict[str, Any]:
        """Order a disclosure for a loan.

        Args:
            loan_id: The loan GUID
            disclosure_type: Type of disclosure ("LE", "CD", etc.)
            delivery_method: Delivery method ("eDisclosure", "Paper", etc.)

        Returns:
            Dictionary containing order result

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> result = client.order_disclosure("loan-guid", "LE")
        """
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/disclosureOrdering"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
        }
        payload = {
            "disclosureType": disclosure_type,
            "deliveryMethod": delivery_method,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)

            if response.status_code not in (200, 201, 202):
                raise APIError(f"Disclosure order failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during disclosure order: {e}") from e

    @_auto_refresh_on_401
    def get_loan_documents(self, loan_id: str) -> list[dict[str, Any]]:
        """List all documents in a loan with their attachment metadata.

        Args:
            loan_id: The loan GUID

        Returns:
            List of document dictionaries, each containing document metadata including
            attachments with their IDs

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> docs = client.get_loan_documents("loan-guid")
            >>> for doc in docs:
            ...     print(f"{doc['title']}: {len(doc.get('attachments', []))} attachments")
            ...     for att in doc.get('attachments', []):
            ...         print(f"  - {att.get('attachmentId')}")
        """
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/documents"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                raise APIError(f"Document list retrieval failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during document list retrieval: {e}") from e

    def get_loan_documents_raw(self, loan_id: str) -> list[dict[str, Any]]:
        """Alias for get_loan_documents - returns raw document list.
        
        This method is an alias for get_loan_documents() for backward compatibility.
        Both methods return the same raw API response.
        
        Args:
            loan_id: The loan GUID
            
        Returns:
            List of document dictionaries with full metadata
            
        Example:
            >>> client = EncompassConnect(token)
            >>> docs = client.get_loan_documents_raw("loan-guid")
        """
        return self.get_loan_documents(loan_id)

    @_auto_refresh_on_401
    def get_loan_entity(self, loan_id: str) -> dict[str, Any]:
        """Get full loan data including all fields and custom fields.

        This retrieves the complete loan entity with view=entity parameter which
        includes standard fields, custom fields, and other loan data.

        Args:
            loan_id: The loan GUID

        Returns:
            Dictionary containing complete loan data

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> loan = client.get_loan_entity("loan-guid")
            >>> print(f"Loan Number: {loan.get('loanNumber')}")
            >>> print(f"Borrower: {loan.get('borrowerFirstName')} {loan.get('borrowerLastName')}")
        """
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
        params = {"view": "entity"}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code != 200:
                raise APIError(f"Loan entity retrieval failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during loan entity retrieval: {e}") from e

    @_auto_refresh_on_401
    def search_loans_pipeline(
        self,
        borrower_name: str | None = None,
        loan_number: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for loans by borrower name or loan number using the Loan Pipeline API.

        Args:
            borrower_name: Borrower name in "LastName, FirstName MiddleName" format
            loan_number: Loan number as a string

        Returns:
            List of loan dictionaries, each containing:
            - loanGuid: The loan GUID
            - loanNumber: Loan number
            - borrowerName: Borrower name
            - loanFolder: Loan folder path

        Raises:
            APIError: If the API request fails
            ValueError: If neither borrower_name nor loan_number is provided

        Example:
            >>> client = EncompassConnect(token)
            >>> loans = client.search_loans_pipeline(borrower_name="Doe, John")
            >>> for loan in loans:
            ...     print(f"{loan['loanNumber']}: {loan['borrowerName']}")
        """
        if not borrower_name and not loan_number:
            raise ValueError("Must provide either borrower_name or loan_number")

        url = f"{self.api_base_url}/encompass/v3/loanPipeline"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
        }

        # Build filter based on search criteria
        if loan_number:
            filter_config = {
                "canonicalName": "Loan.LoanNumber",
                "value": loan_number,
                "matchType": "exact",
            }
        else:  # borrower_name
            filter_config = {
                "canonicalName": "Loan.BorrowerName",
                "value": borrower_name,
                "matchType": "exact",
            }

        payload = {
            "fields": [
                "Loan.Guid",
                "Loan.LoanNumber",
                "Loan.BorrowerName",
                "Loan.LoanFolder",
            ],
            "filter": filter_config,
            "includeArchivedLoans": True,
            "loanOwnership": "AllLoans",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                raise APIError(f"Loan search failed (status {response.status_code}): {response.text}")

            data = response.json()

            # The response is a list of rows directly
            rows = data if isinstance(data, list) else data.get("rows", [])

            # Convert to standard format
            results = []
            for row in rows:
                fields = row.get("fields", {})
                results.append({
                    "loanGuid": row.get("loanId"),  # GUID is at root level as "loanId"
                    "loanNumber": fields.get("Loan.LoanNumber"),
                    "borrowerName": fields.get("Loan.BorrowerName"),
                    "loanFolder": fields.get("Loan.LoanFolder"),
                })

            return results

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during loan search: {e}") from e

    @_auto_refresh_on_401
    def get_document(self, loan_id: str, document_id: str) -> dict[str, Any]:
        """Retrieve document metadata including attachments list.

        Args:
            loan_id: The loan GUID
            document_id: The document GUID

        Returns:
            Dictionary containing document metadata and attachments

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = EncompassConnect(token)
            >>> doc = client.get_document("loan-guid", "doc-guid")
            >>> print(doc['title'])
            >>> print(doc['attachments'])
        """
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/documents/{document_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 404:
                raise APIError(f"Document not found: {document_id}")
            if response.status_code != 200:
                raise APIError(f"Document retrieval failed (status {response.status_code}): {response.text}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during document retrieval: {e}") from e

    @_auto_refresh_on_401
    def download_attachment(self, loan_id: str, attachment_id: str) -> bytes:
        """Download a document attachment as bytes.

        This method handles both Cloud Storage (with authorization header) and
        Legacy (with signed URL) storage types.

        Args:
            loan_id: The loan GUID
            attachment_id: The attachment entity ID

        Returns:
            Document content as bytes

        Raises:
            APIError: If the download fails

        Example:
            >>> client = EncompassConnect(token)
            >>> pdf_bytes = client.download_attachment("loan-guid", "attachment-guid")
            >>> # Save to file
            >>> with open("document.pdf", "wb") as f:
            ...     f.write(pdf_bytes)
        """
        # Step 1: Get download URL
        url = f"{self.api_base_url}/encompass/v3/loans/{loan_id}/attachmentDownloadUrl"
        payload = {"attachments": [attachment_id]}
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json",
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            if response.status_code != 200:
                raise APIError(f"Failed to get download URL (status {response.status_code}): {response.text}")

            data = response.json()

            # Extract download information
            attachments = data.get("attachments", [])
            if not attachments:
                raise APIError("No download information returned")

            attachment_info = attachments[0]

            # Determine download URL and auth method based on storage type
            download_url = None
            authorization_header = attachment_info.get("authorizationHeader")

            # Cloud Storage (newer documents) - has 'url' field
            if attachment_info.get("url"):
                download_url = attachment_info.get("url")
            # Legacy - multi-page documents with originalUrls
            elif attachment_info.get("originalUrls"):
                download_url = attachment_info.get("originalUrls")[0]
            # Page-based (converted documents)
            elif attachment_info.get("pages"):
                download_url = attachment_info.get("pages")[0].get("url")

            if not download_url:
                raise APIError(f"No download URL found in response. Available fields: {list(attachment_info.keys())}")

            # Step 2: Download the actual file
            download_headers = {}
            if authorization_header:
                # Cloud Storage requires the authorization header
                download_headers["Authorization"] = authorization_header

            download_response = requests.get(download_url, headers=download_headers, stream=True, timeout=60)

            if download_response.status_code != 200:
                raise APIError(f"Failed to download file (status {download_response.status_code}): {download_response.text}")

            # Collect the file content
            content = b""
            for chunk in download_response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk

            return content

        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during download: {e}") from e

    def extract_document_data(
        self,
        document_bytes: bytes,
        schema: dict[str, Any],
        doc_type: str | None = None,
        filename: str = "document.pdf",
    ) -> dict[str, Any]:
        """Extract structured data from a document using LandingAI.

        .. deprecated::
            This method is deprecated and will be removed in a future version.
            Use LandingAIClient directly instead:

            >>> from copilotagent import LandingAIClient
            >>> client = LandingAIClient(api_key="your-key")
            >>> result = client.extract_document_data(pdf_bytes, schema)

        Args:
            document_bytes: Document content as bytes
            schema: JSON schema defining what data to extract
            doc_type: Optional document type label for logging/metadata (ignored, kept for compatibility)
            filename: Name of the file being processed (default: "document.pdf")

        Returns:
            Dictionary containing extracted data and metadata

        Raises:
            LandingAIError: If extraction fails or API key not set
        """
        warnings.warn(
            "EncompassConnect.extract_document_data() is deprecated. "
            "Use LandingAIClient directly instead: "
            "from copilotagent import LandingAIClient; client = LandingAIClient(api_key='...')",
            DeprecationWarning,
            stacklevel=2,
        )

        if not self.landingai_api_key:
            raise LandingAIError("LandingAI API key not set. Provide landingai_api_key during initialization.")

        # Delegate to LandingAIClient
        client = LandingAIClient(api_key=self.landingai_api_key)
        result = client.extract_document_data(document_bytes, schema, filename)

        # Add doc_type for backward compatibility
        result["doc_type"] = doc_type
        return result


