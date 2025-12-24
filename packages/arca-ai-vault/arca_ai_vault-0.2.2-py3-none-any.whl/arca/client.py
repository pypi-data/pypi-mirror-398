"""
Main client classes for interacting with Arca API
"""

import requests
from typing import Dict, List, Optional, Any
from .models import TableColumn, SkillMetadata, VectorSkillMetadata
from .exceptions import ArcaAPIError, ArcaAuthError


class ArcaTableClient:
    """Client for interacting with Arca Tables API"""
    
    def __init__(self, user_id: str, base_url: str = "https://arca.build"):
        """
        Initialize the Arca Table Client
        
        Args:
            user_id: Your Arca API key (WorkOS user ID)
            base_url: Base URL for Arca API (default: https://arca.build)
        """
        if not user_id:
            raise ArcaAuthError("user_id (API key) is required")
        
        self.user_id = user_id
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {user_id}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Internal method to make HTTP requests with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            
            if response.status_code == 401:
                raise ArcaAuthError("Invalid API key")
            
            if not response.ok:
                error_data = response.json() if response.content else {}
                
                error_message = error_data.get('error', f'Request failed with status {response.status_code}')
                details = error_data.get('details')
                suggestion = error_data.get('suggestion')
                technical_details = error_data.get('technicalDetails')
                problematic_query = error_data.get('problematicQuery')
                
                raise ArcaAPIError(
                    message=error_message,
                    status_code=response.status_code,
                    details=details,
                    suggestion=suggestion,
                    technical_details=technical_details,
                    problematic_query=problematic_query
                )
            
            return response.json()
        except requests.RequestException as e:
            raise ArcaAPIError(f"Network error: {str(e)}")
    
    def upsert(
        self,
        table_name: str,
        data: Dict[str, Any],
        columns: Optional[List[TableColumn]] = None,
        skill: Optional[SkillMetadata] = None
    ) -> Dict[str, Any]:
        """
        Create or append to a table. This is the recommended method.
        
        Args:
            table_name: Name of the table
            data: Dictionary of data to insert
            columns: List of TableColumn objects (only needed on first insert)
            skill: Optional SkillMetadata to help AI understand the table
        
        Returns:
            Dictionary with success status, message, tableName, s3Path, and recordId
        
        Example:
            client.upsert(
                table_name="meals",
                columns=[
                    TableColumn("food", "VARCHAR"),
                    TableColumn("calories", "INTEGER")
                ],
                data={"food": "Pizza", "calories": 800},
                skill=SkillMetadata(
                    description="Tracks daily meals",
                    examples=["SELECT * FROM meals WHERE calories > 500"]
                )
            )
        """
        payload = {
            "tableName": table_name,
            "data": data
        }
        
        if columns:
            payload["columns"] = [col.to_dict() for col in columns]
        if skill:
            payload["skill"] = skill.to_dict()
        
        return self._make_request("POST", "/api/v1/tables/upsert", json=payload)
    
    def query(
        self,
        table_name: str,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        select: Optional[List[str]] = None,
        group_by: Optional[str] = None,
        having: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query a table with filters and aggregations
        
        Args:
            table_name: Name of the table to query
            query: Raw SQL WHERE clause (e.g., "calories > 500", "protein > 20 AND carbs < 50")
            filters: Dictionary of filters (e.g., {"daysAgo": 7, "food": "Pizza"})
            limit: Maximum number of results
            offset: Number of results to skip
            order_by: Column to order by (e.g., "created_at DESC")
            select: List of columns to select
            group_by: Column to group by
            having: HAVING clause for aggregations
        
        Returns:
            Dictionary with success status, data array, and metadata
        
        Examples:
            # Query with comparison operators
            results = client.query(
                table_name="meals",
                query="calories > 500",
                order_by="calories DESC"
            )
            
            # Query with time-based filters
            results = client.query(
                table_name="meals",
                filters={"daysAgo": 7},
                limit=10,
                order_by="created_at DESC"
            )
            
            # Combine custom WHERE clause with other filters
            results = client.query(
                table_name="meals",
                query="protein > 20",
                filters={"daysAgo": 30},
                limit=5
            )
        """
        payload: Dict[str, Any] = {"tableName": table_name}
        
        # Handle query parameter by mapping it to filters.customWhere
        if query or filters:
            filter_dict = filters.copy() if filters else {}
            if query:
                filter_dict["customWhere"] = query
            payload["filters"] = filter_dict
        
        if limit is not None:
            payload["limit"] = limit
        if offset is not None:
            payload["offset"] = offset
        if order_by:
            payload["orderBy"] = order_by
        if select:
            payload["select"] = select
        if group_by:
            payload["groupBy"] = group_by
        if having:
            payload["having"] = having
        
        return self._make_request("POST", "/api/v1/tables/query", json=payload)
    
    def update(
        self,
        table_name: str,
        data: Dict[str, Any],
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update rows in a table
        
        Args:
            table_name: Name of the table
            data: Dictionary of column:value pairs to update
            where: Dictionary specifying which rows to update (e.g., {"id": 5})
                   If omitted, updates all rows (use with caution!)
        
        Returns:
            Dictionary with success status, rowsUpdated count, and updatedRow data
        
        Examples:
            # Update specific row by ID
            result = client.update(
                table_name="meals",
                data={"calories": 910, "meal_type": "dinner"},
                where={"id": 5}
            )
            
            # Update row by exact column match
            result = client.update(
                table_name="meals",
                data={"calories": 170},
                where={"food": "Grilled Chicken Breast"}
            )
        """
        payload = {
            "tableName": table_name,
            "data": data
        }
        
        if where:
            payload["where"] = where
        
        return self._make_request("POST", "/api/v1/tables/update", json=payload)
    
    def alter_schema(
        self,
        table_name: str,
        add_columns: List[TableColumn],
        default_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Alter table schema by adding new columns while preserving existing data
        
        Args:
            table_name: Name of the table to alter
            add_columns: List of TableColumn objects to add
            default_values: Dictionary mapping column names to default values for existing rows
        
        Returns:
            Dictionary with success status, message, tableName, changes, and newSchema
        
        Example:
            client.alter_schema(
                table_name="meals",
                add_columns=[
                    TableColumn("category", "VARCHAR"),
                    TableColumn("rating", "INTEGER")
                ],
                default_values={
                    "category": "General",
                    "rating": 0
                }
            )
        """
        # Build the addColumns array with default values
        columns_with_defaults = []
        for col in add_columns:
            col_dict = col.to_dict()
            # Add defaultValue if provided
            if default_values and col.name in default_values:
                col_dict["defaultValue"] = default_values[col.name]
            columns_with_defaults.append(col_dict)
        
        payload = {
            "tableName": table_name,
            "addColumns": columns_with_defaults
        }
        
        return self._make_request("POST", "/api/v1/tables/alter-schema", json=payload)
    
    def delete(self, table_name: str) -> Dict[str, Any]:
        """
        Delete an entire table
        
        Args:
            table_name: Name of the table to delete
        
        Returns:
            Dictionary with success status and message
        """
        payload = {"tableName": table_name}
        return self._make_request("DELETE", "/api/v1/tables/delete", json=payload)
    
    def list_tables(self) -> Dict[str, Any]:
        """
        List all tables for the authenticated user
        
        Returns:
            Dictionary with tableCount, tables array with name, s3Path, and rowCount
        """
        return self._make_request("GET", "/api/v1/tables/list")
    
    def get_schemas(self) -> Dict[str, Any]:
        """
        Get schemas for all tables
        
        Returns:
            Dictionary with schemas array containing tableName, s3Path, and columns
        """
        return self._make_request("GET", "/api/v1/tables/schemas")
    
    def get_skill(self, table_name: str) -> Dict[str, Any]:
        """
        Get the SKILL.md file for a specific table
        
        Args:
            table_name: Name of the table
        
        Returns:
            Dictionary with success status, tableName, and skill content
        """
        return self._make_request("GET", f"/api/v1/tables/{table_name}/skill")
    
    def update_skill(
        self,
        table_name: str,
        skill: SkillMetadata
    ) -> Dict[str, Any]:
        """
        Update the SKILL.md file for a table
        
        Args:
            table_name: Name of the table
            skill: SkillMetadata object with updated information
        
        Returns:
            Dictionary with success status and message
        """
        payload = {"skill": skill.to_dict()}
        return self._make_request("POST", f"/api/v1/tables/{table_name}/skill", json=payload)
    
    def get_all_skills(self) -> Dict[str, Any]:
        """
        Get all table skills in one request (useful for MCP context)
        
        Returns:
            Dictionary with skills array containing tableName and skill content
        """
        return self._make_request("GET", "/api/v1/tables/skills")
    
    def export(self, table_name: str) -> bytes:
        """
        Export a table as Parquet file
        
        Args:
            table_name: Name of the table to export
        
        Returns:
            Parquet file as bytes
        """
        url = f"{self.base_url}/api/v1/tables/export?tableName={table_name}"
        response = requests.get(url, headers=self.headers, stream=True)
        
        if not response.ok:
            error_data = response.json() if response.content else {}
            error_message = error_data.get('error', 'Export failed')
            details = error_data.get('details')
            suggestion = error_data.get('suggestion')
            technical_details = error_data.get('technicalDetails')
            problematic_query = error_data.get('problematicQuery')
            
            raise ArcaAPIError(
                message=error_message,
                status_code=response.status_code,
                details=details,
                suggestion=suggestion,
                technical_details=technical_details,
                problematic_query=problematic_query
            )
        
        return response.content


class ArcaVectorClient:
    """Client for interacting with Arca Vectors API (semantic search)"""
    
    def __init__(self, user_id: str, base_url: str = "https://arca.build"):
        """
        Initialize the Arca Vector Client
        
        Args:
            user_id: Your Arca API key (WorkOS user ID)
            base_url: Base URL for Arca API (default: https://arca.build)
        """
        if not user_id:
            raise ArcaAuthError("user_id (API key) is required")
        
        self.user_id = user_id
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {user_id}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Internal method to make HTTP requests with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            
            if response.status_code == 401:
                raise ArcaAuthError("Invalid API key")
            
            if not response.ok:
                error_data = response.json() if response.content else {}
                
                error_message = error_data.get('error', f'Request failed with status {response.status_code}')
                details = error_data.get('details')
                suggestion = error_data.get('suggestion')
                technical_details = error_data.get('technicalDetails')
                problematic_query = error_data.get('problematicQuery')
                
                raise ArcaAPIError(
                    message=error_message,
                    status_code=response.status_code,
                    details=details,
                    suggestion=suggestion,
                    technical_details=technical_details,
                    problematic_query=problematic_query
                )
            
            return response.json()
        except requests.RequestException as e:
            raise ArcaAPIError(f"Network error: {str(e)}")
    
    def add(
        self,
        table_name: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        generate_embedding: bool = True,
        embedding: Optional[List[float]] = None,
        skill: Optional[VectorSkillMetadata] = None
    ) -> Dict[str, Any]:
        """
        Add a vector entry with automatic embedding generation
        
        Args:
            table_name: Name of the vector table
            text: Text content to embed and store
            metadata: Optional metadata dictionary
            generate_embedding: Whether to auto-generate embedding (default: True)
            embedding: Pre-computed embedding vector (if generate_embedding=False)
            skill: Optional VectorSkillMetadata to help AI understand the table
        
        Returns:
            Dictionary with success status, tableName, s3Path, embeddingDimension
        
        Example:
            client.add(
                table_name="journal_entries",
                text="Today was productive. Finished the project.",
                metadata={
                    "category": "personal",
                    "mood": "positive",
                    "tags": "productivity"
                },
                skill=VectorSkillMetadata(
                    description="Personal journal entries",
                    metadata_fields=[
                        MetadataField("category", "string", "Type of entry", ["personal", "work"]),
                        MetadataField("mood", "string", "Emotional state", ["positive", "neutral"])
                    ],
                    search_examples=["Find productive days"],
                    filter_examples=["mood = 'positive'"]
                )
            )
        """
        payload = {
            "tableName": table_name,
            "text": text,
            "generateEmbedding": generate_embedding
        }
        
        if metadata:
            payload["metadata"] = metadata
        if embedding:
            payload["embedding"] = embedding
        if skill:
            payload["skill"] = skill.to_dict()
        
        return self._make_request("POST", "/api/v1/vectors/add", json=payload)
    
    def search(
        self,
        table_name: str,
        query: str,
        limit: int = 5,
        generate_embedding: bool = True,
        embedding: Optional[List[float]] = None,
        filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search vectors semantically
        
        Args:
            table_name: Name of the vector table to search
            query: Search query text
            limit: Maximum number of results (default: 5)
            generate_embedding: Whether to auto-generate query embedding (default: True)
            embedding: Pre-computed query embedding vector
            filter: SQL-like filter expression (e.g., "category = 'personal'")
        
        Returns:
            Dictionary with success, tableName, query, resultCount, and results array
        
        Example:
            results = client.search(
                table_name="journal_entries",
                query="days when I felt accomplished",
                limit=5,
                filter="category = 'personal'"
            )
        """
        payload = {
            "tableName": table_name,
            "query": query,
            "limit": limit,
            "generateEmbedding": generate_embedding
        }
        
        if embedding:
            payload["embedding"] = embedding
        if filter:
            payload["filter"] = filter
        
        return self._make_request("POST", "/api/v1/vectors/search", json=payload)
    
    def delete(self, table_name: str) -> Dict[str, Any]:
        """
        Delete an entire vector table
        
        Args:
            table_name: Name of the vector table to delete
        
        Returns:
            Dictionary with success status and message
        """
        payload = {"tableName": table_name}
        return self._make_request("DELETE", "/api/v1/vectors/delete", json=payload)
    
    def list_tables(self) -> Dict[str, Any]:
        """
        List all vector tables for the authenticated user
        
        Returns:
            Dictionary with userId, tableCount, and tables array
        """
        return self._make_request("GET", "/api/v1/vectors/list")
    
    def get_skill(self, table_name: str) -> Dict[str, Any]:
        """
        Get the SKILL.md file for a specific vector table
        
        Args:
            table_name: Name of the vector table
        
        Returns:
            Dictionary with success status, tableName, and skill content
        """
        return self._make_request("GET", f"/api/v1/vectors/{table_name}/skill")
    
    def update_skill(
        self,
        table_name: str,
        skill: VectorSkillMetadata
    ) -> Dict[str, Any]:
        """
        Update the SKILL.md file for a vector table
        
        Args:
            table_name: Name of the vector table
            skill: VectorSkillMetadata object with updated information
        
        Returns:
            Dictionary with success status and message
        """
        payload = {"skill": skill.to_dict()}
        return self._make_request("POST", f"/api/v1/vectors/{table_name}/skill", json=payload)
    
    def get_all_skills(self) -> Dict[str, Any]:
        """
        Get all vector skills in one request (useful for MCP context)
        
        Returns:
            Dictionary with skills array containing tableName and skill content
        """
        return self._make_request("GET", "/api/v1/vectors/skills")
    
    def export(self, table_name: str) -> bytes:
        """
        Export a vector table as CSV file
        
        Args:
            table_name: Name of the vector table to export
        
        Returns:
            CSV file as bytes
        """
        url = f"{self.base_url}/api/v1/vectors/export?tableName={table_name}"
        response = requests.get(url, headers=self.headers, stream=True)
        
        if not response.ok:
            error_data = response.json() if response.content else {}
            error_message = error_data.get('error', 'Export failed')
            details = error_data.get('details')
            suggestion = error_data.get('suggestion')
            technical_details = error_data.get('technicalDetails')
            problematic_query = error_data.get('problematicQuery')
            
            raise ArcaAPIError(
                message=error_message,
                status_code=response.status_code,
                details=details,
                suggestion=suggestion,
                technical_details=technical_details,
                problematic_query=problematic_query
            )
        
        return response.content


def get_all_skills(user_id: str, base_url: str = "https://arca.build") -> Dict[str, Any]:
    """
    Get all skills (both table and vector) in one request
    
    This is a convenience function that fetches all skills from both
    the Tables API and Vectors API in a single call. Useful for providing
    complete context to AI assistants.
    
    Args:
        user_id: Your Arca API key (WorkOS user ID)
        base_url: Base URL for Arca API (default: https://arca.build)
    
    Returns:
        Dictionary with:
        - success (bool): Request success status
        - userId (str): User ID
        - skills (list): Array of skills, each with tableName, skill, type, success
        - tableSkillCount (int): Number of table skills
        - vectorSkillCount (int): Number of vector skills
    
    Example:
        from arca import get_all_skills
        
        all_skills = get_all_skills(user_id="your-api-key")
        print(f"Total: {len(all_skills['skills'])} skills")
        print(f"Tables: {all_skills['tableSkillCount']}, Vectors: {all_skills['vectorSkillCount']}")
        
        # Filter by type
        table_skills = [s for s in all_skills['skills'] if s['type'] == 'table']
    """
    if not user_id:
        raise ArcaAuthError("user_id (API key) is required")
    
    url = f"{base_url.rstrip('/')}/api/v1/skills"
    headers = {
        "Authorization": f"Bearer {user_id}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 401:
            raise ArcaAuthError("Invalid API key")
        
        if not response.ok:
            error_data = response.json() if response.content else {}
            error_message = error_data.get('error', f'Request failed with status {response.status_code}')
            details = error_data.get('details')
            suggestion = error_data.get('suggestion')
            technical_details = error_data.get('technicalDetails')
            problematic_query = error_data.get('problematicQuery')
            
            raise ArcaAPIError(
                message=error_message,
                status_code=response.status_code,
                details=details,
                suggestion=suggestion,
                technical_details=technical_details,
                problematic_query=problematic_query
            )
        
        return response.json()
    except requests.RequestException as e:
        raise ArcaAPIError(f"Network error: {str(e)}")
