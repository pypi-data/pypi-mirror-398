"""
Airtable API client for handling HTTP requests and responses
"""

import json
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote
import requests

from .exceptions import APIError, RecordNotFoundError


class AirtableClient:
    """
    Client for interacting with the Airtable API
    """

    BASE_URL = "https://api.airtable.com/v0"

    def __init__(self, access_token: str, base_id: str, table_name: str, api_key: str = None):
        """
        Initialize Airtable client

        Args:
            access_token: Airtable Personal Access Token (PAT) - starts with 'pat'
            base_id: Airtable base ID (starts with 'app')
            table_name: Name of the table in the base
            api_key: DEPRECATED - Use access_token instead. Will be removed in v1.0
        """
        # Handle backward compatibility
        if api_key is not None and access_token is None:
            import warnings
            warnings.warn(
                "The 'api_key' parameter is deprecated. Use 'access_token' instead. "
                "API keys are deprecated by Airtable in favor of Personal Access Tokens (PATs). "
                "See: https://airtable.com/developers/web/api/authentication",
                DeprecationWarning,
                stacklevel=2
            )
            access_token = api_key
        elif api_key is not None and access_token is not None:
            raise ValueError("Cannot specify both 'access_token' and 'api_key'. Use 'access_token' only.")
        
        if not access_token:
            raise ValueError("access_token is required. Get your Personal Access Token from: https://airtable.com/developers/web/api/authentication")
            
        self.access_token = access_token
        self.base_id = base_id
        self.table_name = table_name
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })

    def _get_url(self, record_id: Optional[str] = None) -> str:
        """Get the full URL for API requests"""
        url = f"{self.BASE_URL}/{self.base_id}/{quote(self.table_name)}"
        if record_id:
            url += f"/{record_id}"
        return url

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate exceptions"""
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"error": {"message": response.text}}

        if not response.ok:
            error_message = data.get("error", {}).get("message", f"HTTP {response.status_code}")
            raise APIError(
                message=error_message,
                status_code=response.status_code,
                response_data=data
            )

        return data

    def _rate_limit_retry(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Retry API calls with exponential backoff for rate limiting"""
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                response = func(*args, **kwargs)
                return self._handle_response(response)
            except APIError as e:
                if e.status_code == 429 and attempt < max_retries:  # Rate limited
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                raise

    def create_record(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record in Airtable

        Args:
            fields: Dictionary of field names to values

        Returns:
            The created record data from Airtable
        """
        data = {"fields": fields}
        return self._rate_limit_retry(
            self.session.post,
            self._get_url(),
            json=data
        )

    def get_record(self, record_id: str) -> Dict[str, Any]:
        """
        Get a specific record by ID

        Args:
            record_id: The Airtable record ID

        Returns:
            The record data from Airtable

        Raises:
            RecordNotFoundError: If the record doesn't exist
        """
        try:
            return self._rate_limit_retry(
                self.session.get,
                self._get_url(record_id)
            )
        except APIError as e:
            if e.status_code == 404:
                raise RecordNotFoundError(f"Record {record_id} not found")
            raise

    def update_record(self, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing record

        Args:
            record_id: The Airtable record ID
            fields: Dictionary of field names to values

        Returns:
            The updated record data from Airtable
        """
        data = {"fields": fields}
        try:
            return self._rate_limit_retry(
                self.session.patch,
                self._get_url(record_id),
                json=data
            )
        except APIError as e:
            if e.status_code == 404:
                raise RecordNotFoundError(f"Record {record_id} not found")
            raise

    def delete_record(self, record_id: str) -> Dict[str, Any]:
        """
        Delete a record

        Args:
            record_id: The Airtable record ID

        Returns:
            Confirmation data from Airtable
        """
        try:
            return self._rate_limit_retry(
                self.session.delete,
                self._get_url(record_id)
            )
        except APIError as e:
            if e.status_code == 404:
                raise RecordNotFoundError(f"Record {record_id} not found")
            raise

    def list_records(
        self,
        fields: Optional[List[str]] = None,
        filter_by_formula: Optional[str] = None,
        max_records: Optional[int] = None,
        page_size: Optional[int] = None,
        sort: Optional[List[Dict[str, str]]] = None,
        view: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List records with optional filtering and sorting

        Args:
            fields: List of field names to return
            filter_by_formula: Airtable formula for filtering records
            max_records: Maximum number of records to return
            page_size: Number of records per page (max 100)
            sort: List of sort specifications [{"field": "Name", "direction": "asc"}]
            view: Name of view to use

        Returns:
            List of record data from Airtable
        """
        all_records = []
        offset = None

        while True:
            params = {}

            if fields:
                params["fields[]"] = fields
            if filter_by_formula:
                params["filterByFormula"] = filter_by_formula
            if max_records:
                params["maxRecords"] = max_records
            if page_size:
                params["pageSize"] = min(page_size, 100)  # Airtable max is 100
            if sort:
                for i, sort_spec in enumerate(sort):
                    params[f"sort[{i}][field]"] = sort_spec["field"]
                    params[f"sort[{i}][direction]"] = sort_spec.get("direction", "asc")
            if view:
                params["view"] = view
            if offset:
                params["offset"] = offset

            response_data = self._rate_limit_retry(
                self.session.get,
                self._get_url(),
                params=params
            )

            records = response_data.get("records", [])
            all_records.extend(records)

            # Check if we have more pages
            offset = response_data.get("offset")
            if not offset:
                break

            # Check if we've reached max_records
            if max_records and len(all_records) >= max_records:
                all_records = all_records[:max_records]
                break

        return all_records

    def batch_create(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple records in a single batch operation

        Args:
            records: List of record field dictionaries

        Returns:
            List of created record data from Airtable
        """
        # Airtable allows max 10 records per batch
        batch_size = 10
        all_created = []

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_data = {
                "records": [{"fields": record} for record in batch]
            }

            response_data = self._rate_limit_retry(
                self.session.post,
                self._get_url(),
                json=batch_data
            )

            created_records = response_data.get("records", [])
            all_created.extend(created_records)

        return all_created

    def batch_update(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update multiple records in a single batch operation

        Args:
            updates: List of dicts with 'id' and 'fields' keys

        Returns:
            List of updated record data from Airtable
        """
        # Airtable allows max 10 records per batch
        batch_size = 10
        all_updated = []

        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            batch_data = {"records": batch}

            response_data = self._rate_limit_retry(
                self.session.patch,
                self._get_url(),
                json=batch_data
            )

            updated_records = response_data.get("records", [])
            all_updated.extend(updated_records)

        return all_updated
