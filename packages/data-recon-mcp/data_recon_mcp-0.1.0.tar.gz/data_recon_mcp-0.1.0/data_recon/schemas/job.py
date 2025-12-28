"""Pydantic schemas for reconciliation jobs."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class JobStatus(str, Enum):
    """Job status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CheckType(str, Enum):
    """Reconciliation check types."""
    ROW_COUNT = "row_count"
    AGGREGATES = "aggregates"
    SCHEMA = "schema"
    SAMPLE_ROWS = "sample_rows"


class AggregateType(str, Enum):
    """Aggregate function types."""
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"


class TableReference(BaseModel):
    """Reference to a table in a data source."""
    datasource: str
    database: str
    schema_name: Optional[str] = Field(None, alias="schema")
    table: str


class PartitionConfig(BaseModel):
    """Configuration for partitioned/incremental reconciliation."""
    column: str
    start_value: Optional[Any] = None
    end_value: Optional[Any] = None
    partition_type: str = "range"  # range, list


class CheckConfig(BaseModel):
    """Configuration for a single check."""
    type: CheckType
    columns: Optional[List[str]] = None  # For aggregates
    aggregates: Optional[List[AggregateType]] = None  # For aggregates
    primary_key: Optional[List[str]] = None  # For sample rows
    sample_size: Optional[int] = 100  # For sample rows


class ReconJobCreate(BaseModel):
    """Schema for creating a reconciliation job."""
    source: TableReference
    target: TableReference
    checks: List[CheckConfig]
    partition_config: Optional[PartitionConfig] = None


class CheckResultResponse(BaseModel):
    """Result of a single check."""
    check_type: CheckType
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ReconJobResponse(BaseModel):
    """Schema for job response."""
    id: str
    status: JobStatus
    source: Dict[str, Any]
    target: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobStatusResponse(BaseModel):
    """Job status with progress."""
    id: str
    status: JobStatus
    progress_percent: float
    progress_message: Optional[str] = None
    checks_completed: int
    checks_total: int
    estimated_time_remaining: Optional[int] = None  # seconds


class JobResultsResponse(BaseModel):
    """Detailed job results."""
    id: str
    status: JobStatus
    source: Dict[str, Any]
    target: Dict[str, Any]
    checks: List[CheckResultResponse]
    summary: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None


# Individual check request/response schemas

class RowCountCheckRequest(BaseModel):
    """Request for row count check."""
    source: TableReference
    target: TableReference
    partition_config: Optional[PartitionConfig] = None


class RowCountCheckResponse(BaseModel):
    """Response for row count check."""
    source_count: int
    target_count: int
    difference: int
    match_percentage: float
    match: bool


class AggregateCheckRequest(BaseModel):
    """Request for aggregate check."""
    source: TableReference
    target: TableReference
    columns: List[str]
    aggregates: List[AggregateType] = [AggregateType.SUM]
    partition_config: Optional[PartitionConfig] = None


class ColumnAggregateResult(BaseModel):
    """Aggregate results for a single column."""
    column: str
    source_values: Dict[str, Any]
    target_values: Dict[str, Any]
    differences: Dict[str, Any]
    match: bool


class AggregateCheckResponse(BaseModel):
    """Response for aggregate check."""
    columns: List[ColumnAggregateResult]
    all_match: bool


class SchemaCheckRequest(BaseModel):
    """Request for schema check."""
    source: TableReference
    target: TableReference


class SchemaCheckResponse(BaseModel):
    """Response for schema check."""
    source_columns: List[Dict[str, Any]]
    target_columns: List[Dict[str, Any]]
    columns_only_in_source: List[str]
    columns_only_in_target: List[str]
    type_differences: List[Dict[str, Any]]
    match: bool


class SampleCheckRequest(BaseModel):
    """Request for sample row check."""
    source: TableReference
    target: TableReference
    primary_key: List[str]
    sample_size: int = 100
    columns: Optional[List[str]] = None  # Compare specific columns only


class RowMismatch(BaseModel):
    """Details of a mismatched row."""
    primary_key_values: Dict[str, Any]
    differences: List[Dict[str, Any]]


class SampleCheckResponse(BaseModel):
    """Response for sample row check."""
    sample_size: int
    rows_compared: int
    matched: int
    mismatched: int
    missing_in_target: int
    missing_in_source: int
    mismatches: List[RowMismatch]
    match_percentage: float
