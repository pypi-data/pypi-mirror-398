"""Reconciliation jobs API router."""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from ..database import get_db
from ..services.job_service import JobService
from ..services.recon_service import ReconService
from ..schemas.job import (
    TableReference, PartitionConfig, CheckConfig, ReconJobCreate,
    ReconJobResponse, JobStatusResponse, JobResultsResponse,
    RowCountCheckRequest, RowCountCheckResponse,
    AggregateCheckRequest, AggregateCheckResponse,
    SchemaCheckRequest, SchemaCheckResponse,
    SampleCheckRequest, SampleCheckResponse,
    AggregateType
)

router = APIRouter(prefix="/jobs", tags=["Reconciliation Jobs"])


def get_job_service(db: Session = Depends(get_db)) -> JobService:
    return JobService(db)


def get_recon_service(db: Session = Depends(get_db)) -> ReconService:
    return ReconService(db)


# Individual Check Endpoints

@router.post("/checks/row-count", response_model=RowCountCheckResponse)
def run_row_count_check(
    request: RowCountCheckRequest,
    service: ReconService = Depends(get_recon_service)
):
    """Run a quick row count comparison."""
    try:
        partition = request.partition_config.model_dump() if request.partition_config else None
        result = service.run_row_count_check(
            request.source.datasource, request.source.database, 
            request.source.table, request.source.schema_name,
            request.target.datasource, request.target.database,
            request.target.table, request.target.schema_name,
            partition
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checks/aggregates", response_model=AggregateCheckResponse)
def run_aggregate_check(
    request: AggregateCheckRequest,
    service: ReconService = Depends(get_recon_service)
):
    """Run column-level aggregate comparison."""
    try:
        partition = request.partition_config.model_dump() if request.partition_config else None
        aggregates = [a.value for a in request.aggregates]
        result = service.run_aggregate_check(
            request.source.datasource, request.source.database,
            request.source.table, request.source.schema_name,
            request.target.datasource, request.target.database,
            request.target.table, request.target.schema_name,
            request.columns, aggregates, partition
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checks/schema", response_model=SchemaCheckResponse)
def run_schema_check(
    request: SchemaCheckRequest,
    service: ReconService = Depends(get_recon_service)
):
    """Run schema comparison."""
    try:
        result = service.run_schema_check(
            request.source.datasource, request.source.database,
            request.source.table, request.source.schema_name,
            request.target.datasource, request.target.database,
            request.target.table, request.target.schema_name
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checks/sample", response_model=SampleCheckResponse)
def run_sample_check(
    request: SampleCheckRequest,
    service: ReconService = Depends(get_recon_service)
):
    """Run sample row comparison."""
    try:
        result = service.run_sample_check(
            request.source.datasource, request.source.database,
            request.source.table, request.source.schema_name,
            request.target.datasource, request.target.database,
            request.target.table, request.target.schema_name,
            request.primary_key, request.sample_size, request.columns
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Job Management Endpoints

@router.post("", response_model=ReconJobResponse)
async def create_job(
    request: ReconJobCreate,
    background_tasks: BackgroundTasks,
    service: JobService = Depends(get_job_service)
):
    """Create a new reconciliation job with multiple checks."""
    try:
        source_config = request.source.model_dump()
        target_config = request.target.model_dump()
        checks = [c.model_dump() for c in request.checks]
        partition = request.partition_config.model_dump() if request.partition_config else None
        
        job = service.create_job(source_config, target_config, checks, partition)
        
        # Schedule async execution with independent session
        import asyncio
        from ..database import SessionLocal
        
        async def run_job_background(job_id: str):
            """Run job with its own database session."""
            db = SessionLocal()
            try:
                svc = JobService(db)
                await svc.execute_job(job_id)
            finally:
                db.close()
        
        background_tasks.add_task(run_job_background, job.id)
        
        return {
            "id": job.id,
            "status": job.status.value,
            "source": source_config,
            "target": target_config,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[dict])
def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    service: JobService = Depends(get_job_service)
):
    """List recent reconciliation jobs."""
    jobs = service.list_jobs(limit, status)
    return [
        {
            "id": j.id,
            "status": j.status.value,
            "progress_percent": j.progress_percent,
            "created_at": j.created_at.isoformat(),
            "completed_at": j.completed_at.isoformat() if j.completed_at else None
        }
        for j in jobs
    ]


@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str, service: JobService = Depends(get_job_service)):
    """Get job status with progress indicator."""
    try:
        return service.get_job_status(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{job_id}/results", response_model=JobResultsResponse)
def get_job_results(job_id: str, service: JobService = Depends(get_job_service)):
    """Get detailed job results."""
    try:
        return service.get_job_results(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{job_id}/cancel")
def cancel_job(job_id: str, service: JobService = Depends(get_job_service)):
    """Cancel a running job."""
    try:
        if service.cancel_job(job_id):
            return {"message": f"Job '{job_id}' cancelled"}
        return {"message": f"Job '{job_id}' could not be cancelled (already completed/failed)"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
