# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-01-XX

### Added
- **Work Items Resource Implementation** - Complete Work Items resource with full CRUD operations:
  - `client.work_items.list()` - List work items with filtering and pagination
  - `client.work_items.get()` - Get specific work item by key
  - `client.work_items.create()` - Create new work items
  - `client.work_items.update()` - Update existing work items
  - `client.work_items.delete()` - Delete work items
- **Convenience Methods** for Work Items:
  - `client.work_items.get_by_project()` - Get all work items for a specific project
- **File Upload Functionality** - Upload files and attach them to documents:
  - `client.upload_file()` - Upload files from local path, bytes, or remote URL
  - Support for both binary uploads and remote URL attachments
  - Private/public file support
- **Enhanced Call Method** - Improved method invocation with form data support:
  - `client.call()` - Call any whitelisted Frappe server-side method
  - Support for both GET and POST HTTP methods
  - Form data encoding option for legacy Frappe handlers
- **User Info Retrieval** - Get current authenticated user information:
  - `client.get_user_info()` - Get logged-in user details
  - `client.get_logged_user()` - Alias for compatibility

### Changed
- **Package Structure** - Added `WorkItemsClient` to resource clients
- **Import Structure** - Added `WorkItem` and `WorkItemsClient` to main exports
- **Client Integration** - `ZymmrClient` now includes `work_items` resource client

### Technical Details
- **Work Items API**: Full resource-based implementation following Projects pattern
- **File Upload**: Supports multiple input types (file path, bytes, file-like objects, URLs)
- **Method Calls**: Enhanced flexibility for calling custom Frappe methods
- **Backward Compatibility**: All existing APIs remain fully functional

## [0.2.1] - 2025-09-21

### Added
- **Resource-Based API Pattern** - New modern hierarchical API for better developer experience
- **Projects Resource Implementation** - Complete Projects resource with full CRUD operations:
  - `client.projects.list()` - List projects with filtering and pagination
  - `client.projects.get()` - Get specific project by ID
  - `client.projects.create()` - Create new projects
  - `client.projects.update()` - Update existing projects
  - `client.projects.delete()` - Delete projects
- **Convenience Methods** for Projects:
  - `client.projects.get_active()` - Get all active projects
  - `client.projects.get_by_user()` - Get projects by user email
  - `client.projects.get_analytics()` - Get project analytics (framework ready)
- **Project Model Class** - Object-oriented interface for projects with properties:
  - `project.title`, `project.status`, `project.lead`, `project.is_active`
  - `project.project_id`, `project.description`, `project.start_date`, `project.end_date`
- **ResourceList Class** - Enhanced list handling with filtering and metadata
- **BaseResourceClient** - Reusable base class for future resource implementations
- **Enhanced Documentation** - Updated README with both Generic and Resource API examples

### Changed
- **Package Structure** - Added `resources.py` and enhanced `models.py` for resource-based API
- **Client Integration** - `ZymmrClient` now supports both Generic and Resource APIs
- **Import Structure** - Added `Project`, `ProjectsClient`, and `ResourceList` to main exports

### Technical Details
- **Resource-Based Pattern**: Follows modern API client patterns (GitHub API style)
- **Hierarchical Access**: `client.projects.*` pattern for intuitive resource management
- **Model Classes**: Rich object representation with property access
- **Backward Compatibility**: Generic API remains fully functional for all DocTypes
- **Future-Proof**: Architecture ready for additional resources (Work Items, Time Logs, etc.)

## [0.2.0] - 2025-09-18

### Added
- **Complete Frappe Framework v14 integration** - Built specifically for Frappe-based applications
- **Robust authentication system** - Session-based authentication with username/password
- **`get_list()` method** - Full implementation of Frappe's REST API endpoint with:
  - Field selection with JSON array support
  - Complex filtering with JSON object support
  - Ordering and pagination
  - Group by functionality
- **`get_doc()` method** - Fetch individual documents by name
- **Utility methods**: `ping()`, `get_user_info()`, connection testing
- **Context manager support** - Automatic session cleanup
- **Comprehensive error handling** - Custom exceptions for all Frappe API scenarios:
  - `ZymmrAuthenticationError` for auth failures
  - `ZymmrPermissionError` for access denied
  - `ZymmrNotFoundError` for missing resources
  - `ZymmrValidationError` for Frappe validation failures
  - `ZymmrServerError` for server-side issues
- **Retry logic** - Exponential backoff for network failures
- **Debug logging** - Detailed request/response logging when enabled
- **Type safety** - Full type hints throughout the codebase

### Changed  
- **BREAKING**: Complete API rewrite - moved from resource-based API to Frappe-style DocType access
- **BREAKING**: Authentication changed from API keys to username/password (Frappe standard)
- **README.md** - Updated with actual implementation examples and usage patterns
- **Package description** - Now reflects Frappe Framework v14 integration

### Fixed
- Authentication verification issues with Frappe's user ID system
- Session management and cookie handling
- Error handling and response parsing
- Import statements and package structure

### Technical Details
- Built on `requests` library with session management
- Follows Frappe REST API patterns: `GET /api/resource/{doctype}`
- Session-based auth via `POST /api/method/login`
- Production-ready with proper error handling and retries

## [0.1.1] - 2025-09-17

### Added
- Initial package structure with uv
- Basic project metadata and configuration
- MIT License and GitHub repository setup

## [0.1.0] - 2025-09-17

### Added
- Initial project setup
- Basic package scaffolding
- Project metadata configuration
