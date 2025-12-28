"""ReconJob model."""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import uuid

from ..database import Base


class JobStatus(str, enum.Enum):
    """Job status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CheckType(str, enum.Enum):
    """Reconciliation check types."""
    ROW_COUNT = "row_count"
    AGGREGATES = "aggregates"
    SCHEMA = "schema"
    SAMPLE_ROWS = "sample_rows"


def generate_uuid():
    return str(uuid.uuid4())


class ReconJob(Base):
    """Reconciliation job model."""
    
    __tablename__ = "recon_jobs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    
    # Source and target config (JSON strings)
    source_config = Column(Text, nullable=False)
    target_config = Column(Text, nullable=False)
    
    # Partition config for incremental recon (JSON string, optional)
    partition_config = Column(Text, nullable=True)
    
    # Progress tracking
    progress_percent = Column(Float, default=0.0)
    progress_message = Column(String(255), nullable=True)
    
    # Results (JSON string)
    results = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Related checks
    checks = relationship("JobCheck", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ReconJob(id={self.id}, status={self.status})>"


class JobCheck(Base):
    """Individual check within a job."""
    
    __tablename__ = "job_checks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("recon_jobs.id"), nullable=False)
    check_type = Column(SQLEnum(CheckType), nullable=False)
    
    # Check-specific config (JSON string)
    config = Column(Text, nullable=True)
    
    # Status and results
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    result = Column(Text, nullable=True)  # JSON string
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    job = relationship("ReconJob", back_populates="checks")
    
    def __repr__(self):
        return f"<JobCheck(id={self.id}, type={self.check_type}, status={self.status})>"
