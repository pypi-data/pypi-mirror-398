"""Dremio Software API client."""

from typing import Any, Dict, Optional

from dremio_cli.client.base import BaseClient


class SoftwareClient(BaseClient):
    """Client for Dremio Software API."""

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: int = 30,
    ):
        """Initialize Software client.
        
        Args:
            base_url: Base URL for Dremio Software API
            token: Authentication token
            timeout: Request timeout in seconds
        """
        super().__init__(base_url, token, timeout)

    # Catalog operations
    def get_catalog(
        self,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get catalog."""
        params = {}
        if include:
            params["include"] = include
        if exclude:
            params["exclude"] = exclude
        return self.get("catalog", params=params if params else None)

    def get_catalog_item(
        self,
        item_id: str,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
        max_children: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get catalog item by ID."""
        params = {}
        if include:
            params["include"] = include
        if exclude:
            params["exclude"] = exclude
        if max_children:
            params["maxChildren"] = max_children
        return self.get(f"catalog/{item_id}", params=params or None)

    def get_catalog_item_by_path(
        self,
        path: str,
        include: Optional[str] = None,
        exclude: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get catalog item by path."""
        params = {}
        if include:
            params["include"] = include
        if exclude:
            params["exclude"] = exclude
        return self.get(f"catalog/by-path/{path}", params=params or None)

    # Source operations
    def create_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a source."""
        return self.post("catalog", data=source_data)

    def update_source(self, source_id: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a source."""
        return self.put(f"catalog/{source_id}", data=source_data)

    def delete_source(self, source_id: str) -> None:
        """Delete a source."""
        return self.delete(f"catalog/{source_id}")

    # SQL operations
    def execute_sql(self, sql: str, context: Optional[list] = None) -> Dict[str, Any]:
        """Execute SQL query."""
        data = {"sql": sql}
        if context:
            data["context"] = context
        return self.post("sql", data=data)

    # Job operations
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job by ID."""
        return self.get(f"job/{job_id}")

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
        return self.get(f"job/{job_id}/results", params=params or None)

    def cancel_job(self, job_id: str) -> None:
        """Cancel a job."""
        return self.post(f"job/{job_id}/cancel")

    # Job management operations
    def list_jobs(
        self,
        max_results: Optional[int] = None,
        filter_expr: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List jobs.
        
        Args:
            max_results: Maximum number of results
            filter_expr: Filter expression (e.g., 'state=COMPLETED')
            sort: Sort field (prefix with - for descending)
            
        Returns:
            Jobs list response
        """
        params = {}
        if max_results:
            params["maxResults"] = max_results
        if filter_expr:
            params["filter"] = filter_expr
        if sort:
            params["sort"] = sort
        return self.get("job", params=params if params else None)

    def get_job_profile(self, job_id: str) -> Any:
        """Get job profile for performance analysis.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job profile data
        """
        return self.get(f"job/{job_id}/download")

    def get_job_reflections(self, job_id: str) -> Dict[str, Any]:
        """Get reflection information for a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job reflection information
        """
        return self.get(f"job/{job_id}/reflection")

    # View operations
    def create_view(self, view_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a view.
        
        Args:
            view_data: View definition
            
        Returns:
            Created view
        """
        return self.post("catalog", data=view_data)

    def update_view(self, view_id: str, view_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a view.
        
        Args:
            view_id: View ID
            view_data: Updated view definition
            
        Returns:
            Updated view
        """
        return self.put(f"catalog/{view_id}", data=view_data)

    def delete_view(self, view_id: str, tag: str) -> None:
        """Delete a view.
        
        Args:
            view_id: View ID
            tag: Version tag for optimistic concurrency
        """
        return self.delete(f"catalog/{view_id}?tag={tag}")

    # Space operations
    def create_space(self, space_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a space.
        
        Args:
            space_data: Space definition with 'name' and optional 'description'
            
        Returns:
            Created space
        """
        # Create SPACE container
        data = {
            "entityType": "space",
            "name": space_data["name"],
        }
        if "description" in space_data:
            data["description"] = space_data["description"]
        
        return self.post("catalog", data=data)

    def delete_space(self, space_id: str, tag: str) -> None:
        """Delete a space.
        
        Args:
            space_id: Space ID
            tag: Version tag for optimistic concurrency
        """
        return self.delete(f"catalog/{space_id}?tag={tag}")

    # Folder operations
    def create_folder(self, folder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a folder.
        
        Args:
            folder_data: Folder definition with 'path' and optional 'description'
            
        Returns:
            Created folder
        """
        # Create FOLDER container
        data = {
            "entityType": "folder",
            "path": folder_data["path"],
        }
        if "description" in folder_data:
            data["description"] = folder_data["description"]
        
        return self.post("catalog", data=data)

    def delete_folder(self, folder_id: str, tag: str) -> None:
        """Delete a folder.
        
        Args:
            folder_id: Folder ID
            tag: Version tag for optimistic concurrency
        """
        return self.delete(f"catalog/{folder_id}?tag={tag}")

    # Tag operations
    def set_tags(self, catalog_id: str, tags: list) -> None:
        """Set tags on a catalog object.
        
        Args:
            catalog_id: Catalog object ID
            tags: List of tag strings
        """
        return self.post(f"catalog/{catalog_id}/collaboration/tag", data={"tags": tags})

    def get_tags(self, catalog_id: str) -> dict:
        """Get tags from a catalog object.
        
        Args:
            catalog_id: Catalog object ID
            
        Returns:
            Tags data
        """
        return self.get(f"catalog/{catalog_id}/collaboration/tag")

    def delete_tags(self, catalog_id: str) -> None:
        """Delete tags from a catalog object.
        
        Args:
            catalog_id: Catalog object ID
        """
        return self.delete(f"catalog/{catalog_id}/collaboration/tag")

    # Wiki operations
    def set_wiki(self, catalog_id: str, text: str) -> None:
        """Set wiki on a catalog object.
        
        Args:
            catalog_id: Catalog object ID
            text: Wiki markdown text
        """
        return self.post(f"catalog/{catalog_id}/collaboration/wiki", data={"text": text})

    def get_wiki(self, catalog_id: str) -> dict:
        """Get wiki from a catalog object.
        
        Args:
            catalog_id: Catalog object ID
            
        Returns:
            Wiki data
        """
        return self.get(f"catalog/{catalog_id}/collaboration/wiki")

    def delete_wiki(self, catalog_id: str) -> None:
        """Delete wiki from a catalog object.
        
        Args:
            catalog_id: Catalog object ID
        """
        return self.delete(f"catalog/{catalog_id}/collaboration/wiki")

    # Source operations
    def create_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a source.
        
        Args:
            source_data: Source definition with name, type, and config
            
        Returns:
            Created source
        """
        return self.post("catalog", data=source_data)

    def update_source(self, source_id: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a source.
        
        Args:
            source_id: Source ID
            source_data: Updated source definition
            
        Returns:
            Updated source
        """
        return self.put(f"catalog/{source_id}", data=source_data)

    def delete_source(self, source_id: str, tag: str) -> None:
        """Delete a source.
        
        Args:
            source_id: Source ID
            tag: Version tag for optimistic concurrency
        """
        return self.delete(f"catalog/{source_id}?tag={tag}")

    def refresh_source(self, source_id: str) -> Dict[str, Any]:
        """Refresh source metadata.
        
        Args:
            source_id: Source ID
            
        Returns:
            Refresh job information
        """
        return self.post(f"source/{source_id}/refresh")

    def test_source_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test source connection.
        
        Args:
            config: Source configuration
            
        Returns:
            Test result
        """
        return self.post("source/test", data=config)

    # Grant operations
    def list_grants(self, catalog_id: str) -> Dict[str, Any]:
        """List grants for a catalog object.
        
        Args:
            catalog_id: Catalog object ID
            
        Returns:
            Grants data
        """
        return self.get(f"catalog/{catalog_id}/grants")

    def add_grant(self, catalog_id: str, grant_data: Dict[str, Any]) -> None:
        """Add a grant to a catalog object.
        
        Args:
            catalog_id: Catalog object ID
            grant_data: Grant definition with granteeType, granteeId, and privileges
        """
        return self.post(f"catalog/{catalog_id}/grants", data=grant_data)

    def remove_grant(self, catalog_id: str, grantee_type: str, grantee_id: str) -> None:
        """Remove a grant from a catalog object.
        
        Args:
            catalog_id: Catalog object ID
            grantee_type: USER or ROLE
            grantee_id: User or role ID
        """
        return self.delete(f"catalog/{catalog_id}/grants/{grantee_type}/{grantee_id}")

    def set_grants(self, catalog_id: str, grants_data: Dict[str, Any]) -> None:
        """Set all grants for a catalog object (replaces existing).
        
        Args:
            catalog_id: Catalog object ID
            grants_data: Complete grants definition
        """
        return self.put(f"catalog/{catalog_id}/grants", data=grants_data)

    # User operations
    def list_users(self) -> Dict[str, Any]:
        """List all users.
        
        Returns:
            Users data
        """
        return self.get("user")

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User data
        """
        return self.get(f"user/{user_id}")

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user.
        
        Args:
            user_data: User definition with name, email, userName
            
        Returns:
            Created user
        """
        return self.post("user", data=user_data)

    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user.
        
        Args:
            user_id: User ID
            user_data: Updated user definition
            
        Returns:
            Updated user
        """
        return self.put(f"user/{user_id}", data=user_data)

    def delete_user(self, user_id: str) -> None:
        """Delete a user.
        
        Args:
            user_id: User ID
        """
        return self.delete(f"user/{user_id}")

    # Role operations
    def list_roles(self) -> Dict[str, Any]:
        """List all roles.
        
        Returns:
            Roles data
        """
        return self.get("role")

    def get_role(self, role_id: str) -> Dict[str, Any]:
        """Get role by ID.
        
        Args:
            role_id: Role ID
            
        Returns:
            Role data
        """
        return self.get(f"role/{role_id}")

    def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a role.
        
        Args:
            role_data: Role definition with name
            
        Returns:
            Created role
        """
        return self.post("role", data=role_data)

    def update_role(self, role_id: str, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a role.
        
        Args:
            role_id: Role ID
            role_data: Updated role definition
            
        Returns:
            Updated role
        """
        return self.put(f"role/{role_id}", data=role_data)

    def delete_role(self, role_id: str) -> None:
        """Delete a role.
        
        Args:
            role_id: Role ID
        """
        return self.delete(f"role/{role_id}")

    def add_role_member(self, role_id: str, user_id: str) -> None:
        """Add a user to a role.
        
        Args:
            role_id: Role ID
            user_id: User ID
        """
        return self.post(f"role/{role_id}/members", data={"userId": user_id})

    def remove_role_member(self, role_id: str, user_id: str) -> None:
        """Remove a user from a role.
        
        Args:
            role_id: Role ID
            user_id: User ID
        """
        return self.delete(f"role/{role_id}/members/{user_id}")

    # Table operations
    def promote_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Promote a dataset to a physical dataset.
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Promoted dataset
        """
        return self.post(f"catalog/{dataset_id}/promote")

    def set_dataset_format(self, dataset_id: str, format_config: Dict[str, Any]) -> Dict[str, Any]:
        """Set format configuration for a dataset.
        
        Args:
            dataset_id: Dataset ID
            format_config: Format configuration
            
        Returns:
            Updated dataset
        """
        return self.post(f"catalog/{dataset_id}/format", data=format_config)

    def update_dataset(self, dataset_id: str, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update dataset metadata.
        
        Args:
            dataset_id: Dataset ID
            dataset_data: Updated dataset definition
            
        Returns:
            Updated dataset
        """
        return self.put(f"catalog/{dataset_id}", data=dataset_data)
