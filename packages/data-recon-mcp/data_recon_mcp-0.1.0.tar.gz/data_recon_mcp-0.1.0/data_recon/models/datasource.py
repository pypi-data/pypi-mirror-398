"""DataSource model."""

from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from ..database import Base


class DataSourceType(str, enum.Enum):
    """Supported database types."""
    MYSQL = "mysql"
    SNOWFLAKE = "snowflake"


class DataSource(Base):
    """Data source configuration model."""
    
    __tablename__ = "datasources"
    
    name = Column(String(255), primary_key=True)
    type = Column(SQLEnum(DataSourceType), nullable=False)
    connection_config = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DataSource(name={self.name}, type={self.type})>"
