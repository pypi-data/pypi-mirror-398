"""Data sources API router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from ..services.datasource_service import DataSourceService
from ..schemas.datasource import (
    DataSourceCreate, DataSourceResponse, ConnectionTestResult,
    TableInfo, ColumnInfo, MetadataCatalog, TableSearchResult,
    SampleDataResult, TableStatsResult, TableStructureComparison
)

router = APIRouter(prefix="/datasources", tags=["Data Sources"])


def get_service(db: Session = Depends(get_db)) -> DataSourceService:
    return DataSourceService(db)


@router.post("", response_model=DataSourceResponse)
def create_datasource(
    data: DataSourceCreate,
    service: DataSourceService = Depends(get_service)
):
    """Register a new data source."""
    try:
        ds = service.create(
            name=data.name,
            ds_type=data.type.value,
            connection_config=data.connection_config.model_dump()
        )
        return ds
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[DataSourceResponse])
def list_datasources(service: DataSourceService = Depends(get_service)):
    """List all registered data sources."""
    return service.get_all()


@router.get("/{name}", response_model=DataSourceResponse)
def get_datasource(name: str, service: DataSourceService = Depends(get_service)):
    """Get data source by name."""
    ds = service.get_by_name(name)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Data source '{name}' not found")
    return ds


@router.delete("/{name}")
def delete_datasource(name: str, service: DataSourceService = Depends(get_service)):
    """Remove a data source."""
    if not service.delete(name):
        raise HTTPException(status_code=404, detail=f"Data source '{name}' not found")
    return {"message": f"Data source '{name}' deleted"}


@router.post("/{name}/test", response_model=ConnectionTestResult)
def test_connection(name: str, service: DataSourceService = Depends(get_service)):
    """Test connection to a data source."""
    result = service.test_connection(name)
    return result


@router.get("/{name}/databases")
def get_databases(name: str, service: DataSourceService = Depends(get_service)):
    """List databases in a data source."""
    try:
        databases = service.get_databases(name)
        return {"datasource": name, "databases": databases}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/tables")
def get_tables(
    name: str,
    database: str = Query(...),
    schema: Optional[str] = Query(None),
    service: DataSourceService = Depends(get_service)
):
    """List tables in a database/schema."""
    try:
        tables = service.get_tables(name, database, schema)
        return {"datasource": name, "database": database, "tables": tables}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/schema")
def get_table_schema(
    name: str,
    database: str = Query(...),
    table: str = Query(...),
    schema: Optional[str] = Query(None),
    service: DataSourceService = Depends(get_service)
):
    """Get column definitions for a table."""
    try:
        columns = service.get_table_schema(name, database, table, schema)
        return {"datasource": name, "table": table, "columns": columns}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/catalog")
def get_metadata_catalog(name: str, service: DataSourceService = Depends(get_service)):
    """Get full metadata catalog for a data source."""
    try:
        return service.get_metadata_catalog(name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/search")
def search_tables(
    name: str,
    pattern: str = Query(...),
    database: Optional[str] = Query(None),
    service: DataSourceService = Depends(get_service)
):
    """Search for tables matching a pattern."""
    try:
        return service.search_tables(name, pattern, database)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/sample")
def get_sample_data(
    name: str,
    database: str = Query(...),
    table: str = Query(...),
    schema: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=1000),
    service: DataSourceService = Depends(get_service)
):
    """Get sample data from a table."""
    try:
        return service.get_sample_data(name, database, table, schema, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/validate/table")
def validate_table_exists(
    name: str,
    database: str = Query(...),
    table: str = Query(...),
    schema: Optional[str] = Query(None),
    service: DataSourceService = Depends(get_service)
):
    """Validate that a table exists."""
    try:
        return service.validate_table_exists(name, database, table, schema)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}/validate/columns")
def validate_columns_exist(
    name: str,
    database: str = Query(...),
    table: str = Query(...),
    columns: List[str] = Query(...),
    schema: Optional[str] = Query(None),
    service: DataSourceService = Depends(get_service)
):
    """Validate that columns exist in a table."""
    try:
        return service.validate_columns_exist(name, database, table, columns, schema)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/stats")
def get_table_stats(
    name: str,
    database: str = Query(...),
    table: str = Query(...),
    schema: Optional[str] = Query(None),
    service: DataSourceService = Depends(get_service)
):
    """Get table statistics."""
    try:
        return service.get_table_stats(name, database, table, schema)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare-structures")
def compare_table_structures(
    source_datasource: str = Query(...),
    source_database: str = Query(...),
    source_table: str = Query(...),
    source_schema: Optional[str] = Query(None),
    target_datasource: str = Query(...),
    target_database: str = Query(...),
    target_table: str = Query(...),
    target_schema: Optional[str] = Query(None),
    service: DataSourceService = Depends(get_service)
):
    """Compare table structures side by side."""
    try:
        return service.compare_table_structures(
            source_datasource, source_database, source_table, source_schema,
            target_datasource, target_database, target_table, target_schema
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
