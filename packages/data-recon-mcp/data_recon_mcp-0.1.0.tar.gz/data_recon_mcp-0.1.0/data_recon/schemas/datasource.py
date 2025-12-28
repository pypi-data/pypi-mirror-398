"""Pydantic schemas for data sources."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime


class DataSourceType(str, Enum):
    """Supported database types."""
    MYSQL = "mysql"
    SNOWFLAKE = "snowflake"


class MySQLConfig(BaseModel):
    """MySQL connection configuration."""
    host: str
    port: int = 3306
    username: str
    password: str
    database: Optional[str] = None


class SnowflakeConfig(BaseModel):
    """Snowflake connection configuration."""
    account: str
    username: str
    password: str
    warehouse: str
    database: Optional[str] = None
    schema_name: Optional[str] = Field(None, alias="schema")
    role: Optional[str] = None


class DataSourceCreate(BaseModel):
    """Schema for creating a data source."""
    name: str = Field(..., min_length=1, max_length=255)
    type: DataSourceType
    connection_config: Union[MySQLConfig, SnowflakeConfig]


class DataSourceResponse(BaseModel):
    """Schema for data source response."""
    name: str
    type: DataSourceType
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConnectionTestResult(BaseModel):
    """Result of connection test."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class ColumnInfo(BaseModel):
    """Column information."""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    default: Optional[str] = None


class TableInfo(BaseModel):
    """Table information."""
    name: str
    schema_name: Optional[str] = Field(None, alias="schema")
    database: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    size_bytes: Optional[int] = None
    columns: Optional[List[ColumnInfo]] = None


class SchemaInfo(BaseModel):
    """Schema information with tables."""
    name: str
    tables: List[TableInfo]


class DatabaseInfo(BaseModel):
    """Database information with schemas."""
    name: str
    schemas: List[SchemaInfo]


class MetadataCatalog(BaseModel):
    """Full metadata catalog for a data source."""
    datasource: str
    type: DataSourceType
    databases: List[DatabaseInfo]
    total_tables: int


class TableSearchResult(BaseModel):
    """Search result for tables."""
    datasource: str
    matches: List[TableInfo]
    total_matches: int


class SampleDataResult(BaseModel):
    """Sample data from a table."""
    datasource: str
    table: str
    columns: List[str]
    rows: List[List[Any]]
    total_rows: int
    sample_size: int


class TableStatsResult(BaseModel):
    """Table statistics."""
    datasource: str
    table: str
    row_count: int
    column_count: int
    size_bytes: Optional[int] = None
    last_updated: Optional[datetime] = None


class TableStructureComparison(BaseModel):
    """Side-by-side table structure comparison."""
    source_table: str
    target_table: str
    source_columns: List[ColumnInfo]
    target_columns: List[ColumnInfo]
    columns_only_in_source: List[str]
    columns_only_in_target: List[str]
    type_differences: List[Dict[str, Any]]
    structures_match: bool
