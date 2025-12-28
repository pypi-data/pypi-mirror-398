"""Dremio Cloud API client."""

from typing import Any, Dict, Optional

from dremio_cli.client.base import BaseClient


class CloudClient(BaseClient):
    """Client for Dremio Cloud API."""

    def __init__(
        self,
        base_url: str,
        project_id: str,
        token: str,
        timeout: int = 30,
    ):
        """Initialize Cloud client.
        
        Args:
            base_url: Base URL for Dremio Cloud API
            project_id: Project ID
            token: Authentication token
            timeout: Request timeout in seconds
        """
        super().__init__(base_url, token, timeout)
        self.project_id = project_id

    def _project_endpoint(self, endpoint: str) -> str:
        """Build project-scoped endpoint.
        
        Args:
            endpoint: Endpoint path
            
        Returns:
            Project-scoped endpoint
        """
        return f"/projects/{self.project_id}/{endpoint.lstrip('/')}"

    # Catalog operations
    def get_catalog(self, include: Optional[str] = None) -> Dict[str, Any]:
        """Get catalog."""
        params = {"include": include} if include else None
        return self.get(self._project_endpoint("catalog"), params=params)

    def get_catalog_item(self, item_id: str, include: Optional[str] = None) -> Dict[str, Any]:
        """Get catalog item by ID."""
        params = {"include": include} if include else None
        return self.get(self._project_endpoint(f"catalog/{item_id}"), params=params)

    def get_catalog_item_by_path(self, path: str, include: Optional[str] = None) -> Dict[str, Any]:
        """Get catalog item by path."""
        params = {"include": include} if include else None
        return self.get(self._project_endpoint(f"catalog/by-path/{path}"), params=params)

    # Source operations
    def create_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a source."""
        return self.post(self._project_endpoint("catalog"), data=source_data)

    def update_source(self, source_id: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a source."""
        return self.put(self._project_endpoint(f"catalog/{source_id}"), data=source_data)

    def delete_source(self, source_id: str) -> None:
        """Delete a source."""
        return self.delete(self._project_endpoint(f"catalog/{source_id}"))

    # Job operations
    def list_jobs(
        self,
        max_results: Optional[int] = None,
        filter_expr: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List jobs."""
        params = {}
        if max_results:
            params["maxResults"] = max_results
        if filter_expr:
            params["filter"] = filter_expr
        if sort:
            params["sort"] = sort
        return self.get(self._project_endpoint("job"), params=params if params else None)

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job by ID."""
        return self.get(self._project_endpoint(f"job/{job_id}"))

    def get_job_results(
        self,
        job_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get job results."""
        params = {}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        return self.get(self._project_endpoint(f"job/{job_id}/results"), params=params if params else None)

    def cancel_job(self, job_id: str) -> None:
        """Cancel a job."""
        return self.post(self._project_endpoint(f"job/{job_id}/cancel"))

    # View operations
    def create_view(self, view_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a view."""
        return self.post(self._project_endpoint("catalog"), data=view_data)

    def update_view(self, view_id: str, view_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a view."""
        return self.put(self._project_endpoint(f"catalog/{view_id}"), data=view_data)

    def delete_view(self, view_id: str, tag: str) -> None:
        """Delete a view."""
        return self.delete(self._project_endpoint(f"catalog/{view_id}?tag={tag}"))

    # Space operations (Cloud: creates top-level folders)
    def create_space(self, space_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a space (top-level folder in Cloud).
        
        In Cloud, spaces are represented as top-level folders in the project catalog.
        
        Args:
            space_data: Space definition with 'name' and optional 'description'
            
        Returns:
            Created folder
        """
        # In Cloud, create a top-level folder
        data = {
            "entityType": "folder",
            "path": [space_data["name"]],
        }
        if "description" in space_data:
            data["description"] = space_data["description"]
        
        return self.post(self._project_endpoint("catalog"), data=data)

    def delete_space(self, space_id: str, tag: str) -> None:
        """Delete a space (folder in Cloud).
        
        Args:
            space_id: Space/folder ID
            tag: Version tag for optimistic concurrency
        """
        return self.delete(self._project_endpoint(f"catalog/{space_id}?tag={tag}"))

    # Folder operations
    def create_folder(self, folder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a folder.
        
        Args:
            folder_data: Folder definition with 'path' and optional 'description'
            
        Returns:
            Created folder
        """
        data = {
            "entityType": "folder",
            "path": folder_data["path"],
        }
        if "description" in folder_data:
            data["description"] = folder_data["description"]
        
        return self.post(self._project_endpoint("catalog"), data=data)

    def delete_folder(self, folder_id: str, tag: str) -> None:
        """Delete a folder.
        
        Args:
            folder_id: Folder ID
            tag: Version tag for optimistic concurrency
        """
        return self.delete(self._project_endpoint(f"catalog/{folder_id}?tag={tag}"))

    # Tag operations
    def set_tags(self, catalog_id: str, tags: list) -> None:
        """Set tags on a catalog object."""
        return self.post(self._project_endpoint(f"catalog/{catalog_id}/collaboration/tag"), data={"tags": tags})

    def get_tags(self, catalog_id: str) -> dict:
        """Get tags from a catalog object."""
        return self.get(self._project_endpoint(f"catalog/{catalog_id}/collaboration/tag"))

    def delete_tags(self, catalog_id: str) -> None:
        """Delete tags from a catalog object."""
        return self.delete(self._project_endpoint(f"catalog/{catalog_id}/collaboration/tag"))

    # Wiki operations
    def set_wiki(self, catalog_id: str, text: str) -> None:
        """Set wiki on a catalog object."""
        return self.post(self._project_endpoint(f"catalog/{catalog_id}/collaboration/wiki"), data={"text": text})

    def get_wiki(self, catalog_id: str) -> dict:
        """Get wiki from a catalog object."""
        return self.get(self._project_endpoint(f"catalog/{catalog_id}/collaboration/wiki"))

    def delete_wiki(self, catalog_id: str) -> None:
        """Delete wiki from a catalog object."""
        return self.delete(self._project_endpoint(f"catalog/{catalog_id}/collaboration/wiki"))

    # Source operations
    def create_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a source."""
        return self.post(self._project_endpoint("catalog"), data=source_data)

    def update_source(self, source_id: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a source."""
        return self.put(self._project_endpoint(f"catalog/{source_id}"), data=source_data)

    def delete_source(self, source_id: str, tag: str) -> None:
        """Delete a source."""
        return self.delete(self._project_endpoint(f"catalog/{source_id}?tag={tag}"))

    def refresh_source(self, source_id: str) -> Dict[str, Any]:
        """Refresh source metadata."""
        return self.post(self._project_endpoint(f"source/{source_id}/refresh"))

    def test_source_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test source connection."""
        return self.post(self._project_endpoint("source/test"), data=config)

    # Grant operations
    def list_grants(self, catalog_id: str) -> Dict[str, Any]:
        """List grants for a catalog object."""
        return self.get(self._project_endpoint(f"catalog/{catalog_id}/grants"))

    def add_grant(self, catalog_id: str, grant_data: Dict[str, Any]) -> None:
        """Add a grant to a catalog object."""
        return self.post(self._project_endpoint(f"catalog/{catalog_id}/grants"), data=grant_data)

    def remove_grant(self, catalog_id: str, grantee_type: str, grantee_id: str) -> None:
        """Remove a grant from a catalog object."""
        return self.delete(self._project_endpoint(f"catalog/{catalog_id}/grants/{grantee_type}/{grantee_id}"))

    def set_grants(self, catalog_id: str, grants_data: Dict[str, Any]) -> None:
        """Set all grants for a catalog object."""
        return self.put(self._project_endpoint(f"catalog/{catalog_id}/grants"), data=grants_data)

    # User operations
    def list_users(self) -> Dict[str, Any]:
        """List all users."""
        return self.get(self._project_endpoint("user"))

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID."""
        return self.get(self._project_endpoint(f"user/{user_id}"))

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user."""
        return self.post(self._project_endpoint("user"), data=user_data)

    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user."""
        return self.put(self._project_endpoint(f"user/{user_id}"), data=user_data)

    def delete_user(self, user_id: str) -> None:
        """Delete a user."""
        return self.delete(self._project_endpoint(f"user/{user_id}"))

    # Role operations
    def list_roles(self) -> Dict[str, Any]:
        """List all roles."""
        return self.get(self._project_endpoint("role"))

    def get_role(self, role_id: str) -> Dict[str, Any]:
        """Get role by ID."""
        return self.get(self._project_endpoint(f"role/{role_id}"))

    def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a role."""
        return self.post(self._project_endpoint("role"), data=role_data)

    def update_role(self, role_id: str, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a role."""
        return self.put(self._project_endpoint(f"role/{role_id}"), data=role_data)

    def delete_role(self, role_id: str) -> None:
        """Delete a role."""
        return self.delete(self._project_endpoint(f"role/{role_id}"))

    def add_role_member(self, role_id: str, user_id: str) -> None:
        """Add a user to a role."""
        return self.post(self._project_endpoint(f"role/{role_id}/members"), data={"userId": user_id})

    def remove_role_member(self, role_id: str, user_id: str) -> None:
        """Remove a user from a role."""
        return self.delete(self._project_endpoint(f"role/{role_id}/members/{user_id}"))

    # Table operations
    def promote_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Promote a dataset to a physical dataset."""
        return self.post(self._project_endpoint(f"catalog/{dataset_id}/promote"))

    def set_dataset_format(self, dataset_id: str, format_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set format configuration for a dataset."""
        return self.post(self._project_endpoint(f"catalog/{dataset_id}/format"), data=format_config)

    def update_dataset(self, dataset_id: str, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update dataset metadata."""
        return self.put(self._project_endpoint(f"catalog/{dataset_id}"), data=dataset_data)
