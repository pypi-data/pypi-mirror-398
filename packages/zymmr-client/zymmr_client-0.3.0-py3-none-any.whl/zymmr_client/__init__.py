"""Zymmr Client - Python library for Zymmr Project Management API.

A modern, robust Python client for interacting with Zymmr's REST API,
built on top of Frappe Framework v14.

The client supports two complementary API patterns:

1. **Generic DocType API** (Original) - Direct Frappe DocType access
2. **Resource-Based API** (New) - Hierarchical resource management

Currently implementing Projects resource with more resources to be added.

Example usage - Generic API (still supported):
    ```python
    from zymmr_client import ZymmrClient

    # Initialize client
    client = ZymmrClient(
        base_url="https://yourdomain.zymmr.com",
        username="your-username",
        password="your-password"
    )

    # Get list of projects (generic way)
    projects = client.get_list("Project", fields=["name", "status"])

    # Get specific document
    project = client.get_doc("Project", "PROJ-001")
    ```

Example usage - Resource-Based API (New) - Projects:
    ```python
    from zymmr_client import ZymmrClient

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

Example usage - Resource-Based API (New) - Work Items:
    ```python
    from zymmr_client import ZymmrClient

    # List work items for a project
    work_items = client.work_items.list(project="PROJ-001")

    # Get work items by type
    stories = client.work_items.get_by_type("Story")

    # Get work items by priority
    high_priority = client.work_items.get_by_priority(["High", "Critical"])

    # Get work items by assignee
    my_work_items = client.work_items.get_by_assignee("dev@example.com")

    # Create new work item
    new_work_item = client.work_items.create({
        "title": "Implement new feature",
        "project": "ZMR",
        "type": "Story",
        "priority": "High",
        "description": "Implement the new feature as requested",
        "passignee": "dev@example.com"  # Primary assignee
    })

    # Get work items by project
    project_work_items = client.work_items.get_by_project("ZMR")
    ```
"""

__version__ = "0.3.0"
__author__ = "Kiran Harbak"
__email__ = "kiran.harbak@amruts.com"

# Main exports
from .client import ZymmrClient
from .exceptions import (
    ZymmrAPIError,
    ZymmrAuthenticationError,
    ZymmrPermissionError,
    ZymmrNotFoundError,
    ZymmrValidationError,
    ZymmrServerError,
    ZymmrConnectionError,
    ZymmrTimeoutError
)
from .models import (
    Project,
    WorkItem,
    ResourceList
)
from .resources import (
    ProjectsClient,
    WorkItemsClient
)

__all__ = [
    # Main client
    "ZymmrClient",

    # Exceptions
    "ZymmrAPIError",
    "ZymmrAuthenticationError",
    "ZymmrPermissionError",
    "ZymmrNotFoundError",
    "ZymmrValidationError",
    "ZymmrServerError",
    "ZymmrConnectionError",
    "ZymmrTimeoutError",

    # Models
    "Project",
    "WorkItem",
    "ResourceList",

    # Resource clients
    "ProjectsClient",
    "WorkItemsClient",
]


def main() -> None:
    """CLI entry point."""
    print(f"Zymmr Client v{__version__}")
    print("Python client library for Zymmr Project Management API")
    print("\nFor usage examples, visit: https://github.com/kiran-harbak/zymmr-client")
