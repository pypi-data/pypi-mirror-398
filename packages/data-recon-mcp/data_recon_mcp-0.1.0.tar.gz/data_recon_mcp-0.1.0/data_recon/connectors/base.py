"""Abstract base connector."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseConnector(ABC):
    """Abstract base class for database connectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize connector with configuration."""
        self.config = config
        self._connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close the database connection."""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test database connection."""
        pass
    
    @abstractmethod
    def get_databases(self) -> List[str]:
        """List all databases."""
        pass
    
    @abstractmethod
    def get_schemas(self, database: str) -> List[str]:
        """List all schemas in a database."""
        pass
    
    @abstractmethod
    def get_tables(self, database: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tables in a database/schema."""
        pass
    
    @abstractmethod
    def get_table_schema(
        self, database: str, table: str, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get column definitions for a table."""
        pass
    
    @abstractmethod
    def get_row_count(
        self, 
        database: str, 
        table: str, 
        schema: Optional[str] = None,
        where_clause: Optional[str] = None
    ) -> int:
        """Get row count for a table."""
        pass
    
    @abstractmethod
    def get_aggregates(
        self,
        database: str,
        table: str,
        columns: List[str],
        aggregates: List[str],
        schema: Optional[str] = None,
        where_clause: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get aggregate values for columns."""
        pass
    
    @abstractmethod
    def get_sample_rows(
        self,
        database: str,
        table: str,
        limit: int = 100,
        schema: Optional[str] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get sample rows from a table."""
        pass
    
    @abstractmethod
    def search_tables(
        self, 
        pattern: str, 
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for tables matching a pattern."""
        pass
    
    @abstractmethod
    def get_table_stats(
        self,
        database: str,
        table: str,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get table statistics."""
        pass
    
    @abstractmethod
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
