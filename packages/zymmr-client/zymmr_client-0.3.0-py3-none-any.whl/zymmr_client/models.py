"""Resource model classes for Zymmr API client.

This module defines model classes that represent resources transferred to and from
the Zymmr API, following established patterns for API client development.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional


class BaseModel:
    """Base model class for all Zymmr resources."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize model from API response data."""
        self._data = data
        self._parse_data(data)

    def _parse_data(self, data: Dict[str, Any]):
        """Parse API response data into model attributes."""
        for key, value in data.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model back to dictionary."""
        return self._data.copy()

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"{self.__class__.__name__}(id={getattr(self, 'name', 'N/A')})"


class Project(BaseModel):
    """Model representing a Zymmr Project.

    This class represents a project entity with all its associated fields
    as defined in the Frappe DocType schema.
    """

    def __init__(self, data: Dict[str, Any]):
        """Initialize Project model from API response."""
        super().__init__(data)

    @property
    def project_id(self) -> str:
        """Get the project ID/key."""
        return getattr(self, 'key', '')

    @property
    def title(self) -> str:
        """Get the project title."""
        return getattr(self, 'title', '')

    @property
    def status(self) -> str:
        """Get the project status."""
        return getattr(self, 'status', '')

    @property
    def lead(self) -> str:
        """Get the project lead."""
        return getattr(self, 'lead', '')

    @property
    def description(self) -> str:
        """Get the project description."""
        return getattr(self, 'description', '')

    @property
    def start_date(self) -> Optional[date]:
        """Get the project start date."""
        date_str = getattr(self, 'start_date', None)
        if date_str:
            return datetime.fromisoformat(date_str).date()
        return None

    @property
    def end_date(self) -> Optional[date]:
        """Get the project end date."""
        date_str = getattr(self, 'end_date', None)
        if date_str:
            return datetime.fromisoformat(date_str).date()
        return None

    @property
    def is_active(self) -> bool:
        """Check if project is active."""
        return self.status.lower() == 'active'


class WorkItem(BaseModel):
    """Model representing a Zymmr Work Item.

    This class represents a work item (task, story, bug, etc.) entity
    with all its associated fields as defined in the Frappe DocType schema.
    """

    def __init__(self, data: Dict[str, Any]):
        """Initialize WorkItem model from API response."""
        super().__init__(data)

    @property
    def work_item_id(self) -> str:
        """Get the work item ID/key (user-friendly identifier)."""
        return getattr(self, 'key', '')

    @property
    def name(self) -> str:
        """Get the work item name (Frappe internal ID)."""
        return getattr(self, 'name', '')

    @property
    def title(self) -> str:
        """Get the work item title."""
        return getattr(self, 'title', '')

    @property
    def status(self) -> str:
        """Get the work item status."""
        return getattr(self, 'status', '')

    @property
    def priority(self) -> str:
        """Get the work item priority."""
        return getattr(self, 'priority', '')

    @property
    def work_item_type(self) -> str:
        """Get the work item type (Story, Task, Bug, etc.)."""
        return getattr(self, 'type', '')

    @property
    def primary_assignee(self) -> str:
        """Get the primary assignee (passignee field in Frappe)."""
        return getattr(self, 'passignee', '')

    @property
    def secondary_assignee(self) -> str:
        """Get the secondary assignee (sassignee field in Frappe)."""
        return getattr(self, 'sassignee', '')

    @property
    def description(self) -> str:
        """Get the work item description."""
        return getattr(self, 'description', '')

    @property
    def story_point(self) -> Optional[int]:
        """Get the work item story point estimate."""
        return getattr(self, 'story_point', None)

    @property
    def project(self) -> str:
        """Get the associated project key."""
        return getattr(self, 'project', '')

    @property
    def sprint(self) -> Optional[str]:
        """Get the associated sprint."""
        return getattr(self, 'sprint', None)

    @property
    def reporter(self) -> str:
        """Get the work item reporter."""
        return getattr(self, 'reporter', '')

    @property
    def start_date(self) -> Optional[date]:
        """Get the work item start date."""
        date_str = getattr(self, 'start_date', None)
        if date_str:
            return datetime.fromisoformat(date_str).date()
        return None

    @property
    def end_date(self) -> Optional[date]:
        """Get the work item end date."""
        date_str = getattr(self, 'end_date', None)
        if date_str:
            return datetime.fromisoformat(date_str).date()
        return None

    @property
    def actual_start_date(self) -> Optional[date]:
        """Get the actual start date."""
        date_str = getattr(self, 'actual_start_date', None)
        if date_str:
            return datetime.fromisoformat(date_str).date()
        return None

    @property
    def completion_date(self) -> Optional[date]:
        """Get the completion date."""
        date_str = getattr(self, 'completion_date', None)
        if date_str:
            return datetime.fromisoformat(date_str).date()
        return None

    @property
    def is_completed(self) -> bool:
        """Check if work item is completed."""
        return self.status.lower() in ['done', 'completed', 'closed']

    @property
    def is_blocked(self) -> bool:
        """Check if work item is blocked."""
        return self.status.lower() == 'blocked'

    @property
    def is_in_progress(self) -> bool:
        """Check if work item is in progress."""
        return self.status.lower() == 'in progress'


class ResourceList(list):
    """A list of resources with additional metadata."""

    def __init__(self, data: List[Dict[str, Any]], model_class=None):
        """Initialize resource list from API response."""
        super().__init__()
        self.model_class = model_class
        if model_class:
            for item in data:
                self.append(model_class(item))
        else:
            self.extend(data)

    def first(self):
        """Get the first item in the list."""
        return self[0] if self else None

    def last(self):
        """Get the last item in the list."""
        return self[-1] if self else None

    def filter(self, **conditions):
        """Filter the list by conditions."""
        result = []
        for item in self:
            match = True
            for key, value in conditions.items():
                if getattr(item, key, None) != value:
                    match = False
                    break
            if match:
                result.append(item)
        return ResourceList(result, self.model_class)
