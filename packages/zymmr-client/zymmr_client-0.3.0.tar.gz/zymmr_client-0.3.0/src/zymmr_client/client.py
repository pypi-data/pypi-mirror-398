"""Main Zymmr API client implementation.

Provides the primary ZymmrClient class for interacting with Zymmr's Frappe-based
REST API endpoints.
"""

import json
import os
from io import BytesIO
from typing import IO, Any, Dict, List, Optional, Union

from .auth import FrappeAuth
from .exceptions import ZymmrValidationError
from .http import HTTPClient
from .resources import ProjectsClient, WorkItemsClient


class ZymmrClient:
    """Main client for interacting with Zymmr API.

    This client provides both the original generic DocType API and the new
    resource-based API for maximum flexibility. The resource-based API follows
    modern API client patterns and provides better developer experience.

    The client supports two complementary patterns:

    1. **Generic DocType API** (Original) - Direct Frappe DocType access
    2. **Resource-Based API** (New) - Hierarchical resource management

    Currently implementing Projects resource with more resources to be added.

    Example - Generic API (still supported):
        ```python
        # Initialize client
        client = ZymmrClient(
            base_url="https://yourdomain.zymmr.com",
            username="your-username",
            password="your-password"
        )

        # Get list of projects (generic way)
        projects = client.get_list("Project",
                                  fields=["name", "status", "project_name"],
                                  limit_page_length=10)
        ```

    Example - Resource-Based API (New) - Projects:
        ```python
        # List all projects
        projects = client.projects.list(
            fields=["title", "key", "status"],
            filters={"status": "Active"}
        )

        # Get active projects only
        active_projects = client.projects.get_active()

        # Get projects by lead email
        my_projects = client.projects.get_by_lead("admin@example.com")

        # Get specific project by key
        project = client.projects.get("ZMR")

        # Create new project
        new_project = client.projects.create({
            "title": "My New Project",
            "key": "MNP",
            "description": "Project description",
            "lead": "pm@example.com"
        })
        ```

    Example - Resource-Based API (New) - Work Items:
        ```python
        # Create new work item
        new_work_item = client.work_items.create({
            "title": "Implement new feature",
            "project": "<hashofproject>",
            "type": "<typeoftype>",
            "priority": "High",
            "description": "Implement the new feature as requested",
            "passignee": "<hashofuser>"  # Primary assignee
        })

        # Get work items by project
        project_work_items = client.work_items.get_by_project("ZMR")
        ```
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int = 30,
        max_retries: int = 3,
        debug: bool = False
    ):
        """Initialize Zymmr client.

        Args:
            base_url: Base URL of your Zymmr instance (e.g., 'https://yourdomain.zymmr.com')
            username: Username for authentication
            password: Password for authentication
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retries for failed requests (default: 3)
            debug: Enable debug logging (default: False)

        Raises:
            ZymmrAuthenticationError: If authentication fails
            ZymmrConnectionError: If unable to connect to server
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.debug = debug

        # Initialize authentication
        self._auth = FrappeAuth(base_url, username, password)

        # Authenticate immediately
        self._auth.authenticate()

        # Initialize HTTP client
        self._http = HTTPClient(
            auth=self._auth,
            timeout=timeout,
            max_retries=max_retries,
            debug=debug
        )

    @property
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._auth.is_authenticated

    @property
    def projects(self) -> ProjectsClient:
        """Get the Projects resource client.

        Returns:
            ProjectsClient instance for managing projects
        """
        if not hasattr(self, '_projects_client'):
            self._projects_client = ProjectsClient(self._http)
        return self._projects_client

    @property
    def work_items(self) -> WorkItemsClient:
        """Get the Work Items resource client.

        Returns:
            WorkItemsClient instance for managing work items
        """
        if not hasattr(self, '_work_items_client'):
            self._work_items_client = WorkItemsClient(self._http)
        return self._work_items_client

    def get_list(
        self,
        doctype: str,
        fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit_start: int = 0,
        limit_page_length: int = 20,
        group_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get a list of documents from Frappe.

        This method corresponds to Frappe's GET /api/resource/{doctype} endpoint.

        Args:
            doctype: The DocType to fetch (e.g., 'Project', 'Task', 'User')
            fields: List of field names to fetch. If None, fetches all allowed fields
            filters: Dictionary of filter conditions (e.g., {'status': 'Open'})
            order_by: Field to order by with optional ASC/DESC (e.g., 'creation desc')
            limit_start: Starting offset for pagination (default: 0)
            limit_page_length: Number of records to fetch (default: 20, max: 200)
            group_by: Field to group results by

        Returns:
            List of dictionaries containing the document data

        Raises:
            ZymmrValidationError: If parameters are invalid
            ZymmrNotFoundError: If DocType doesn't exist
            ZymmrPermissionError: If user lacks read permissions
            ZymmrAPIError: For other API errors

        Example:
            ```python
            # Basic usage
            projects = client.get_list("Project")

            # With specific fields
            projects = client.get_list("Project", 
                                      fields=["name", "project_name", "status"])

            # With filters
            open_tasks = client.get_list("Task", 
                                        filters={"status": "Open"},
                                        order_by="priority desc",
                                        limit_page_length=50)

            # Complex filters
            filtered_projects = client.get_list("Project", 
                                               filters={
                                                   "status": ["in", ["Active", "On Hold"]],
                                                   "creation": [">", "2023-01-01"]
                                               })
            ```
        """
        # Validate inputs
        if not doctype:
            raise ZymmrValidationError("DocType cannot be empty")

        if limit_page_length > 200:
            raise ZymmrValidationError("limit_page_length cannot exceed 200")

        if limit_start < 0:
            raise ZymmrValidationError("limit_start must be non-negative")

        # Build request parameters
        params: Dict[str, Any] = {
            'limit_start': limit_start,
            'limit_page_length': limit_page_length
        }

        # Add fields parameter
        if fields:
            # Frappe expects fields as JSON string
            params['fields'] = json.dumps(fields)

        # Add filters parameter
        if filters:
            # Frappe expects filters as JSON string
            params['filters'] = json.dumps(filters)

        # Add order_by parameter
        if order_by:
            params['order_by'] = order_by

        # Add group_by parameter
        if group_by:
            params['group_by'] = group_by

        # Make API request
        url = f"/api/resource/{doctype}"

        if self.debug:
            print(f"[DEBUG] Fetching {doctype} with params: {params}")

        response = self._http.get(url, params=params)

        # Extract data from response
        # Frappe typically returns data in the 'data' field
        if isinstance(response, dict) and 'data' in response:
            return response['data']
        elif isinstance(response, list):
            return response
        else:
            # Fallback - return empty list if structure is unexpected
            return []

    def get_doc(self, doctype: str, name: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get a single document by name.

        This method corresponds to Frappe's GET /api/resource/{doctype}/{name} endpoint.

        Args:
            doctype: The DocType (e.g., 'Project', 'Task')
            name: The name/ID of the document
            fields: List of field names to fetch. If None, fetches all allowed fields

        Returns:
            Dictionary containing the document data

        Raises:
            ZymmrNotFoundError: If document doesn't exist
            ZymmrPermissionError: If user lacks read permissions
            ZymmrAPIError: For other API errors
        """
        if not doctype or not name:
            raise ZymmrValidationError("Both doctype and name are required")

        params = {}
        if fields:
            params['fields'] = json.dumps(fields)

        url = f"/api/resource/{doctype}/{name}"
        response = self._http.get(url, params=params)

        # Frappe returns the document data directly or in 'data' field
        if isinstance(response, dict):
            return response.get('data', response)

        return response

    def insert(self, doctype: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document in Frappe.

        This method corresponds to Frappe's POST /api/resource/{doctype} endpoint.

        Args:
            doctype: The DocType to create (e.g., 'Work Item', 'Project')
            data: Dictionary containing the document data

        Returns:
            Dictionary containing the created document data

        Raises:
            ZymmrValidationError: If data is invalid or required fields missing
            ZymmrPermissionError: If user lacks create permissions
            ZymmrAPIError: For other API errors

        Example:
            ```python
            # Create a new work item
            work_item = client.insert("Work Item", {
                "title": "Fix login bug",
                "project": "PROJ-001", 
                "type": "Bug",
                "priority": "High",
                "description": "Users can't login with special characters"
            })

            # Create a new project
            project = client.insert("Project", {
                "title": "New Website",
                "key": "NW",
                "description": "Company website redesign",
                "lead": "john@company.com"
            })
            ```
        """
        if not doctype:
            raise ZymmrValidationError("DocType cannot be empty")

        if not data or not isinstance(data, dict):
            raise ZymmrValidationError("Data must be a non-empty dictionary")

        url = f"/api/resource/{doctype}"

        if self.debug:
            print(f"[DEBUG] Creating {doctype} with data: {data}")

        response = self._http.post(url, json=data)

        # Frappe returns the created document data
        if isinstance(response, dict):
            return response.get('data', response)

        return response

    def update(self, doctype: str, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing document in Frappe.

        This method corresponds to Frappe's PUT /api/resource/{doctype}/{name} endpoint.

        Args:
            doctype: The DocType (e.g., 'Work Item', 'Project')
            name: The name/ID of the document to update
            data: Dictionary containing the fields to update

        Returns:
            Dictionary containing the updated document data

        Raises:
            ZymmrNotFoundError: If document doesn't exist
            ZymmrValidationError: If data is invalid
            ZymmrPermissionError: If user lacks write permissions
            ZymmrAPIError: For other API errors

        Example:
            ```python
            # Update work item status
            updated_item = client.update("Work Item", "WI-123", {
                "status": "In Progress",
                "assignee": "jane@company.com"
            })

            # Update project end date
            updated_project = client.update("Project", "PROJ-001", {
                "end_date": "2024-12-31",
                "status": "Active"
            })
            ```
        """
        if not doctype or not name:
            raise ZymmrValidationError("Both doctype and name are required")

        if not data or not isinstance(data, dict):
            raise ZymmrValidationError("Data must be a non-empty dictionary")

        url = f"/api/resource/{doctype}/{name}"

        if self.debug:
            print(f"[DEBUG] Updating {doctype} {name} with data: {data}")

        response = self._http.put(url, json=data)

        # Frappe returns the updated document data
        if isinstance(response, dict):
            return response.get('data', response)

        return response

    def delete(self, doctype: str, name: str) -> bool:
        """Delete a document from Frappe.

        This method corresponds to Frappe's DELETE /api/resource/{doctype}/{name} endpoint.

        Args:
            doctype: The DocType (e.g., 'Work Item', 'Project')
            name: The name/ID of the document to delete

        Returns:
            True if deletion was successful

        Raises:
            ZymmrNotFoundError: If document doesn't exist
            ZymmrPermissionError: If user lacks delete permissions
            ZymmrAPIError: For other API errors

        Example:
            ```python
            # Delete a work item
            success = client.delete("Work Item", "WI-123")
            if success:
                print("Work item deleted successfully")

            # Delete a time log
            client.delete("Time Log", "TL-456")
            ```
        """
        if not doctype or not name:
            raise ZymmrValidationError("Both doctype and name are required")

        url = f"/api/resource/{doctype}/{name}"

        if self.debug:
            print(f"[DEBUG] Deleting {doctype} {name}")

        response = self._http.delete(url)

        # Frappe typically returns success message or empty response for deletes
        return True  # If no exception was raised, deletion was successful

    def call(
        self,
        method: str,
        http_method: str = "POST",
        use_form: bool = False,
        **kwargs
    ) -> Any:
        """Call a whitelisted Frappe server-side method.

        This method allows you to invoke any whitelisted (@frappe.whitelist) method
        on the server via the /api/method/{method} endpoint.

        Args:
            method: Dotted path to the method (e.g., 'frappe.client.rename_doc',
                    'myapp.api.custom_method')
            http_method: HTTP method to use ("GET" or "POST", default: "POST").
                         Use GET for read-only methods, POST for mutations.
            use_form: Send payload as form data instead of JSON (default: False).
                Some Frappe handlers (especially legacy ones) only read
                frappe.form_dict and ignore JSON bodies. Set this to True when
                the server complains that parameters are missing even though
                they are provided.
            **kwargs: Keyword arguments to pass to the method

        Returns:
            The 'message' field from the response (method's return value)

        Raises:
            ZymmrNotFoundError: If method doesn't exist
            ZymmrPermissionError: If method is not whitelisted or user lacks permission
            ZymmrAPIError: For other API errors

        Example:
            ```python
            # Rename a document (POST - default)
            client.call("frappe.client.rename_doc",
                        doctype="User",
                        old="old@email.com",
                        new="new@email.com")

            # Call custom API method
            result = client.call("myapp.api.process_data",
                                 data={"key": "value"},
                                 options={"async": True})

            # Read-only method with GET
            result = client.call("frappe.client.get_count",
                                 http_method="GET",
                                 doctype="User")

            # Insert work item via custom endpoint
            work_item = client.call("insert_work_item", doc={
                "project": "abc123",
                "title": "New Task",
                "workflow_state": "In Progress"
            })
            ```
        """
        url = f"/api/method/{method}"

        if self.debug:
            print(
                f"[DEBUG] Calling method {method} ({http_method}) with args: {kwargs}")

        if http_method.upper() == "GET":
            response = self._http.get(url, params=kwargs)
        else:
            if use_form:
                # Match frappeclient behaviour: form-encode and stringify nested objects.
                encoded_kwargs = {}
                for key, value in kwargs.items():
                    if isinstance(value, (dict, list)):
                        encoded_kwargs[key] = json.dumps(value)
                    else:
                        encoded_kwargs[key] = value
                response = self._http.post(url, data=encoded_kwargs)
            else:
                response = self._http.post(url, json=kwargs)

        # Frappe returns method results in 'message' field
        if isinstance(response, dict):
            return response.get('message')

        return response

    def upload_file(
        self,
        file: Optional[Union[str, bytes, IO[bytes]]] = None,
        doctype: str = "",
        docname: str = "",
        file_name: Optional[str] = None,
        is_private: bool = False,
        file_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a file and attach it to a document via /api/method/upload_file.

        Args:
            file: Path, bytes, or file-like object for the upload content. Optional
                if file_url is provided.
            doctype: Target DocType (e.g., 'Work Item').
            docname: Target document name/hash.
            file_name: Optional filename to store; if not provided and a path is
                given, the basename of the path is used.
            is_private: Whether to mark the file as private.
            file_url: Remote URL to attach instead of uploading bytes.

        Returns:
            Parsed JSON response from the server.
        """
        if not doctype or not docname:
            raise ZymmrValidationError(
                "doctype and docname are required for file upload")

        if file is None and not file_url:
            raise ZymmrValidationError(
                "Provide either file content/path or file_url")

        # Resolve file content and name
        upload_name = file_name
        file_obj: Optional[IO[bytes]] = None
        files = None

        if file is not None:
            if isinstance(file, str):
                upload_name = upload_name or os.path.basename(file)
                file_obj = open(file, "rb")
            elif isinstance(file, bytes):
                file_obj = BytesIO(file)
            else:
                file_obj = file

            if not upload_name:
                upload_name = "upload.bin"

            files = {
                "file": (upload_name, file_obj)
            }
        else:
            upload_name = upload_name or os.path.basename(
                file_url or "") or "remote-file"
        data = {
            "doctype": doctype,
            "docname": docname,
            "file_name": upload_name,
            "is_private": json.dumps(is_private)
        }
        if file_url:
            data["file_url"] = file_url

        try:
            return self._http.post("/api/method/upload_file", files=files, data=data)
        finally:
            # Only close if we opened the file ourselves (i.e., path or bytes)
            if isinstance(file, str) and file_obj:
                file_obj.close()
            elif isinstance(file, bytes) and file_obj:
                file_obj.close()

    def ping(self) -> bool:
        """Test connection to server.

        Returns:
            True if server is reachable and client is authenticated
        """
        try:
            url = "/api/method/ping"
            response = self._http.get(url)
            return response.get('message') == 'pong'
        except:
            return False

    def get_user_info(self) -> str:
        """Get information about the currently logged-in user.

        Returns:
            Dictionary containing user information
        """
        url = "/api/method/frappe.auth.get_logged_user"
        response = self._http.get(url)

        return response.get('message')

    def get_logged_user(self) -> str:
        """Get the currently logged-in user's email/name.

        This is an alias for get_user_info() for compatibility with
        frappe-client patterns.

        Returns:
            str: Username/email of authenticated user
        """
        return self.get_user_info()

    def close(self) -> None:
        """Close the client and logout.

        This method logs out from the server and cleans up resources.
        It's recommended to call this when you're done with the client.
        """
        if hasattr(self, '_auth'):
            self._auth.logout()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically logout."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        status = "authenticated" if self.is_authenticated else "not authenticated"
        return f"ZymmrClient(base_url='{self.base_url}', user='{self.username}', {status})"
