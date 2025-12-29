from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone.utc, timedelta
from models import get_db, Account, KymaRuntime, CFOrg, Deployment, DeploymentReplica
from config import get_config
from tasks.scheduled import trigger_cleanup, trigger_cf_check

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

config = get_config()

@router.post("/cleanup")
def run_cleanup(background_tasks: BackgroundTasks):
    """Manually trigger cleanup and Kyma rebuild."""
    background_tasks.add_task(trigger_cleanup)
    return {"message": "Cleanup and rebuild started"}

@router.post("/cf-daily-check")
def run_cf_check(background_tasks: BackgroundTasks):
    """Manually trigger CF daily check."""
    background_tasks.add_task(trigger_cf_check)
    return {"message": "CF daily check started"}

@router.post("/check-expirations")
def check_expirations(db: Session = Depends(get_db)):
    """Check and update expiration status."""
    now = datetime.now(timezone.utc)
    threshold_days = config.get("scheduling", {}).get("kyma", {}).get("expiring_threshold_days", 2)
    
    updated = {"kyma_expiring": 0, "kyma_expired": 0, "deployments_expired": 0}
    
    kyma_runtimes = db.query(KymaRuntime).filter(KymaRuntime.status.in_(["OK", "EXPIRING"])).all()
    for runtime in kyma_runtimes:
        if runtime.expires_at:
            expires = runtime.expires_at.replace(tzinfo=timezone.utc) if runtime.expires_at.tzinfo is None else runtime.expires_at
            days_left = (expires - now).days
            
            if days_left < 0:
                runtime.status = "EXPIRED"
                updated["kyma_expired"] += 1
            elif days_left < threshold_days and runtime.status == "OK":
                runtime.status = "EXPIRING"
                updated["kyma_expiring"] += 1
    
    deployments = db.query(Deployment).filter(
        Deployment.status == "RUNNING",
        Deployment.expires_at != None
    ).all()
    
    for deployment in deployments:
        expires = deployment.expires_at.replace(tzinfo=timezone.utc) if deployment.expires_at.tzinfo is None else deployment.expires_at
        if expires < now:
            deployment.status = "STOPPED"
            for replica in deployment.replicas_list:
                replica.status = "STOPPED"
                replica.stopped_at = now
            updated["deployments_expired"] += 1
    
    db.commit()
    return {"message": "Expiration check completed", "updated": updated}

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get system statistics."""
    accounts = db.query(Account).all()
    kyma_runtimes = db.query(KymaRuntime).all()
    cf_orgs = db.query(CFOrg).all()
    deployments = db.query(Deployment).all()
    
    return {
        "accounts": {
            "total": len(accounts),
            "active": sum(1 for a in accounts if a.status == "ACTIVE"),
            "banned": sum(1 for a in accounts if a.status == "BANNED")
        },
        "kyma": {
            "total": len(kyma_runtimes),
            "ok": sum(1 for k in kyma_runtimes if k.status == "OK"),
            "expiring": sum(1 for k in kyma_runtimes if k.status == "EXPIRING"),
            "expired": sum(1 for k in kyma_runtimes if k.status == "EXPIRED"),
            "creating": sum(1 for k in kyma_runtimes if k.status == "CREATING"),
            "cooling": sum(1 for k in kyma_runtimes if k.status == "COOLING")
        },
        "cf": {
            "total": len(cf_orgs),
            "ok": sum(1 for c in cf_orgs if c.status == "OK")
        },
        "deployments": {
            "total": len(deployments),
            "running": sum(1 for d in deployments if d.status == "RUNNING"),
            "pending": sum(1 for d in deployments if d.status == "PENDING"),
            "stopped": sum(1 for d in deployments if d.status == "STOPPED")
        }
    }

@router.get("/scheduled-jobs")
def get_scheduled_jobs():
    """Get scheduled jobs configuration."""
    jobs_config = config.get("scheduled_jobs", {})
    return {
        "cf_daily_check": jobs_config.get("cf_daily_check", {}),
        "cleanup": jobs_config.get("cleanup", {})
    }
