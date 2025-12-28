"""Job management service."""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..models.job import ReconJob, JobCheck, JobStatus, CheckType
from .recon_service import ReconService


class JobService:
    """Service for managing reconciliation jobs."""
    
    def __init__(self, db: Session):
        self.db = db
        self.recon_service = ReconService(db)
    
    def create_job(
        self,
        source_config: Dict[str, Any],
        target_config: Dict[str, Any],
        checks: List[Dict[str, Any]],
        partition_config: Optional[Dict[str, Any]] = None
    ) -> ReconJob:
        """Create a new reconciliation job."""
        job = ReconJob(
            source_config=json.dumps(source_config),
            target_config=json.dumps(target_config),
            partition_config=json.dumps(partition_config) if partition_config else None,
            status=JobStatus.PENDING
        )
        
        # Create check records
        for check_config in checks:
            check = JobCheck(
                check_type=CheckType(check_config["type"]),
                config=json.dumps(check_config),
                status=JobStatus.PENDING
            )
            job.checks.append(check)
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def get_job(self, job_id: str) -> Optional[ReconJob]:
        """Get job by ID."""
        return self.db.query(ReconJob).filter(ReconJob.id == job_id).first()
    
    def list_jobs(
        self, limit: int = 20, status_filter: Optional[str] = None
    ) -> List[ReconJob]:
        """List recent jobs."""
        query = self.db.query(ReconJob)
        
        if status_filter:
            query = query.filter(ReconJob.status == JobStatus(status_filter))
        
        return query.order_by(ReconJob.created_at.desc()).limit(limit).all()
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status with progress."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found")
        
        checks_total = len(job.checks)
        checks_completed = sum(
            1 for c in job.checks 
            if c.status in [JobStatus.COMPLETED, JobStatus.FAILED]
        )
        
        return {
            "id": job.id,
            "status": job.status.value,
            "progress_percent": job.progress_percent,
            "progress_message": job.progress_message,
            "checks_completed": checks_completed,
            "checks_total": checks_total,
            "estimated_time_remaining": None  # Could calculate based on elapsed time
        }
    
    def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """Get detailed job results."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found")
        
        source = json.loads(job.source_config)
        target = json.loads(job.target_config)
        
        check_results = []
        summary = {"passed": 0, "failed": 0, "errors": 0}
        
        for check in job.checks:
            result = json.loads(check.result) if check.result else None
            
            if check.status == JobStatus.COMPLETED:
                if result and result.get("match", True):
                    summary["passed"] += 1
                else:
                    summary["failed"] += 1
            elif check.status == JobStatus.FAILED:
                summary["errors"] += 1
            
            check_results.append({
                "check_type": check.check_type.value,
                "status": check.status.value,
                "result": result,
                "error_message": check.error_message,
                "started_at": check.started_at.isoformat() if check.started_at else None,
                "completed_at": check.completed_at.isoformat() if check.completed_at else None
            })
        
        return {
            "id": job.id,
            "status": job.status.value,
            "source": source,
            "target": target,
            "checks": check_results,
            "summary": summary,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found")
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return False
        
        job.status = JobStatus.CANCELLED
        job.progress_message = "Job cancelled by user"
        self.db.commit()
        return True
    
    def _update_progress(
        self, job: ReconJob, check_index: int, total_checks: int, message: str
    ):
        """Update job progress."""
        job.progress_percent = (check_index / total_checks) * 100
        job.progress_message = message
        self.db.commit()
    
    async def execute_job(self, job_id: str):
        """Execute a reconciliation job asynchronously."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found")
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        self.db.commit()
        
        source = json.loads(job.source_config)
        target = json.loads(job.target_config)
        partition = json.loads(job.partition_config) if job.partition_config else None
        
        total_checks = len(job.checks)
        
        for i, check in enumerate(job.checks):
            if job.status == JobStatus.CANCELLED:
                break
            
            check.status = JobStatus.RUNNING
            check.started_at = datetime.utcnow()
            self._update_progress(job, i, total_checks, f"Running {check.check_type.value} check...")
            
            try:
                config = json.loads(check.config) if check.config else {}
                
                if check.check_type == CheckType.ROW_COUNT:
                    result = self.recon_service.run_row_count_check(
                        source["datasource"], source["database"], source["table"], source.get("schema"),
                        target["datasource"], target["database"], target["table"], target.get("schema"),
                        partition
                    )
                elif check.check_type == CheckType.AGGREGATES:
                    result = self.recon_service.run_aggregate_check(
                        source["datasource"], source["database"], source["table"], source.get("schema"),
                        target["datasource"], target["database"], target["table"], target.get("schema"),
                        config.get("columns", []),
                        config.get("aggregates", ["SUM"]),
                        partition
                    )
                elif check.check_type == CheckType.SCHEMA:
                    result = self.recon_service.run_schema_check(
                        source["datasource"], source["database"], source["table"], source.get("schema"),
                        target["datasource"], target["database"], target["table"], target.get("schema")
                    )
                elif check.check_type == CheckType.SAMPLE_ROWS:
                    result = self.recon_service.run_sample_check(
                        source["datasource"], source["database"], source["table"], source.get("schema"),
                        target["datasource"], target["database"], target["table"], target.get("schema"),
                        config.get("primary_key", []),
                        config.get("sample_size", 100),
                        config.get("columns")
                    )
                else:
                    result = {"error": f"Unknown check type: {check.check_type}"}
                
                check.result = json.dumps(result)
                check.status = JobStatus.COMPLETED
                
            except Exception as e:
                check.error_message = str(e)
                check.status = JobStatus.FAILED
            
            check.completed_at = datetime.utcnow()
            self.db.commit()
            
            # Small delay to allow cancellation checks
            await asyncio.sleep(0.1)
        
        # Finalize job
        if job.status != JobStatus.CANCELLED:
            failed_checks = sum(1 for c in job.checks if c.status == JobStatus.FAILED)
            job.status = JobStatus.FAILED if failed_checks == total_checks else JobStatus.COMPLETED
        
        job.completed_at = datetime.utcnow()
        job.progress_percent = 100.0
        job.progress_message = "Job completed"
        self.db.commit()
