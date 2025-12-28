"""Data source management service."""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.datasource import DataSource, DataSourceType
from ..connectors import MySQLConnector, SnowflakeConnector, BaseConnector


class DataSourceService:
    """Service for managing data sources."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_connector(self, datasource: DataSource) -> BaseConnector:
        """Get appropriate connector for data source type."""
        config = json.loads(datasource.connection_config)
        
        if datasource.type == DataSourceType.MYSQL:
            return MySQLConnector(config)
        elif datasource.type == DataSourceType.SNOWFLAKE:
            return SnowflakeConnector(config)
        else:
            raise ValueError(f"Unsupported data source type: {datasource.type}")
    
    def create(self, name: str, ds_type: str, connection_config: Dict[str, Any]) -> DataSource:
        """Create a new data source."""
        existing = self.get_by_name(name)
        if existing:
            raise ValueError(f"Data source '{name}' already exists")
        
        datasource = DataSource(
            name=name,
            type=DataSourceType(ds_type),
            connection_config=json.dumps(connection_config)
        )
        self.db.add(datasource)
        self.db.commit()
        self.db.refresh(datasource)
        return datasource
    
    def get_by_name(self, name: str) -> Optional[DataSource]:
        """Get data source by name."""
        return self.db.query(DataSource).filter(DataSource.name == name).first()
    
    def get_all(self) -> List[DataSource]:
        """Get all data sources."""
        return self.db.query(DataSource).all()
    
    def delete(self, name: str) -> bool:
        """Delete a data source."""
        datasource = self.get_by_name(name)
        if not datasource:
            return False
        self.db.delete(datasource)
        self.db.commit()
        return True
    
    def test_connection(self, name: str) -> Dict[str, Any]:
        """Test connection to a data source."""
        datasource = self.get_by_name(name)
        if not datasource:
            return {"success": False, "message": f"Data source '{name}' not found"}
        
        connector = self._get_connector(datasource)
        return connector.test_connection()
    
    def get_databases(self, name: str) -> List[str]:
        """Get databases from a data source."""
        datasource = self.get_by_name(name)
        if not datasource:
            raise ValueError(f"Data source '{name}' not found")
        
        connector = self._get_connector(datasource)
        with connector:
            return connector.get_databases()
    
    def get_tables(
        self, name: str, database: str, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tables from a database."""
        datasource = self.get_by_name(name)
        if not datasource:
            raise ValueError(f"Data source '{name}' not found")
        
        connector = self._get_connector(datasource)
        with connector:
            return connector.get_tables(database, schema)
    
    def get_table_schema(
        self, name: str, database: str, table: str, schema: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get table schema."""
        datasource = self.get_by_name(name)
        if not datasource:
            raise ValueError(f"Data source '{name}' not found")
        
        connector = self._get_connector(datasource)
        with connector:
            return connector.get_table_schema(database, table, schema)
    
    def get_metadata_catalog(self, name: str) -> Dict[str, Any]:
        """Get full metadata catalog for a data source."""
        datasource = self.get_by_name(name)
        if not datasource:
            raise ValueError(f"Data source '{name}' not found")
        
        connector = self._get_connector(datasource)
        with connector:
            databases = connector.get_databases()
            catalog = {
                "datasource": name,
                "type": datasource.type.value,
                "databases": [],
                "total_tables": 0
            }
            
            for db_name in databases:
                try:
                    schemas = connector.get_schemas(db_name)
                    db_info = {"name": db_name, "schemas": []}
                    
                    for schema_name in schemas:
                        tables = connector.get_tables(db_name, schema_name)
                        db_info["schemas"].append({
                            "name": schema_name,
                            "tables": tables
                        })
                        catalog["total_tables"] += len(tables)
                    
                    catalog["databases"].append(db_info)
                except Exception:
                    # Skip databases we can't access
                    continue
            
            return catalog
    
    def search_tables(
        self, name: str, pattern: str, database: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for tables matching a pattern."""
        datasource = self.get_by_name(name)
        if not datasource:
            raise ValueError(f"Data source '{name}' not found")
        
        connector = self._get_connector(datasource)
        with connector:
            matches = connector.search_tables(pattern, database)
            return {
                "datasource": name,
                "matches": matches,
                "total_matches": len(matches)
            }
    
    def get_sample_data(
        self, name: str, database: str, table: str, 
        schema: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """Get sample data from a table."""
        datasource = self.get_by_name(name)
        if not datasource:
            raise ValueError(f"Data source '{name}' not found")
        
        connector = self._get_connector(datasource)
        with connector:
            result = connector.get_sample_rows(database, table, limit, schema)
            return {
                "datasource": name,
                "table": f"{database}.{schema}.{table}" if schema else f"{database}.{table}",
                **result
            }
    
    def validate_table_exists(
        self, name: str, database: str, table: str, schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate that a table exists."""
        datasource = self.get_by_name(name)
        if not datasource:
            raise ValueError(f"Data source '{name}' not found")
        
        connector = self._get_connector(datasource)
        with connector:
            tables = connector.get_tables(database, schema)
            table_names = [t["name"].lower() for t in tables]
            exists = table.lower() in table_names
            return {
                "exists": exists,
                "datasource": name,
                "table": table,
                "message": f"Table '{table}' {'exists' if exists else 'does not exist'}"
            }
    
    def validate_columns_exist(
        self, name: str, database: str, table: str, 
        columns: List[str], schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate that columns exist in a table."""
        datasource = self.get_by_name(name)
        if not datasource:
            raise ValueError(f"Data source '{name}' not found")
        
        connector = self._get_connector(datasource)
        with connector:
            table_schema = connector.get_table_schema(database, table, schema)
            existing_cols = {col["name"].lower() for col in table_schema}
            
            results = {}
            missing = []
            for col in columns:
                exists = col.lower() in existing_cols
                results[col] = exists
                if not exists:
                    missing.append(col)
            
            return {
                "all_exist": len(missing) == 0,
                "results": results,
                "missing": missing
            }
    
    def get_table_stats(
        self, name: str, database: str, table: str, schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get table statistics."""
        datasource = self.get_by_name(name)
        if not datasource:
            raise ValueError(f"Data source '{name}' not found")
        
        connector = self._get_connector(datasource)
        with connector:
            stats = connector.get_table_stats(database, table, schema)
            return {
                "datasource": name,
                "table": table,
                **stats
            }
    
    def compare_table_structures(
        self, 
        source_name: str, source_db: str, source_table: str, source_schema: Optional[str],
        target_name: str, target_db: str, target_table: str, target_schema: Optional[str]
    ) -> Dict[str, Any]:
        """Compare table structures side by side."""
        source_ds = self.get_by_name(source_name)
        target_ds = self.get_by_name(target_name)
        
        if not source_ds:
            raise ValueError(f"Source data source '{source_name}' not found")
        if not target_ds:
            raise ValueError(f"Target data source '{target_name}' not found")
        
        source_connector = self._get_connector(source_ds)
        target_connector = self._get_connector(target_ds)
        
        with source_connector:
            source_cols = source_connector.get_table_schema(source_db, source_table, source_schema)
        
        with target_connector:
            target_cols = target_connector.get_table_schema(target_db, target_table, target_schema)
        
        source_col_names = {col["name"].lower() for col in source_cols}
        target_col_names = {col["name"].lower() for col in target_cols}
        
        only_in_source = list(source_col_names - target_col_names)
        only_in_target = list(target_col_names - source_col_names)
        
        # Find type differences
        source_types = {col["name"].lower(): col["data_type"] for col in source_cols}
        target_types = {col["name"].lower(): col["data_type"] for col in target_cols}
        
        type_diffs = []
        for col_name in source_col_names & target_col_names:
            if source_types[col_name] != target_types[col_name]:
                type_diffs.append({
                    "column": col_name,
                    "source_type": source_types[col_name],
                    "target_type": target_types[col_name]
                })
        
        return {
            "source_table": f"{source_db}.{source_table}",
            "target_table": f"{target_db}.{target_table}",
            "source_columns": source_cols,
            "target_columns": target_cols,
            "columns_only_in_source": only_in_source,
            "columns_only_in_target": only_in_target,
            "type_differences": type_diffs,
            "structures_match": len(only_in_source) == 0 and len(only_in_target) == 0 and len(type_diffs) == 0
        }
