from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, UTC, timedelta
from models import get_db, Account, KymaRuntime
from integrations.btp_cli import BTPClient

router = APIRouter(prefix="/kyma", tags=["kyma"])

@router.get("")
def list_kyma_runtimes(status: str = None, db: Session = Depends(get_db)):
    """List all Kyma runtimes."""
    query = db.query(KymaRuntime)
    if status:
        query = query.filter(KymaRuntime.status == status)
    
    runtimes = query.all()
    return [{
        "id": str(r.id),
        "account_id": str(r.account_id),
        "instance_id": r.instance_id,
        "cluster_name": r.cluster_name,
        "status": r.status,
        "memory_limit_mb": r.memory_limit_mb,
        "memory_used_mb": r.memory_used_mb,
        "expires_at": r.expires_at.isoformat() if r.expires_at else None,
        "cooling_until": r.cooling_until.isoformat() if r.cooling_until else None
    } for r in runtimes]

@router.get("/pool")
def get_pool_status(db: Session = Depends(get_db)):
    """Get Kyma pool status summary."""
    all_runtimes = db.query(KymaRuntime).all()
    
    status_counts = {}
    for r in all_runtimes:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
    
    # Available = OK or EXPIRING with enough time
    now = datetime.now(UTC)
    available = 0
    expiring_soon = 0
    
    for r in all_runtimes:
        if r.status == "OK":
            if r.expires_at:
                expires = r.expires_at.replace(tzinfo=UTC) if r.expires_at.tzinfo is None else r.expires_at
                days_left = (expires - now).days
                if days_left >= 2:
                    available += 1
                elif days_left >= 0:
                    expiring_soon += 1
            else:
                available += 1
    
    return {
        "total": len(all_runtimes),
        "available": available,
        "expiring_soon": expiring_soon,
        "by_status": status_counts
    }

@router.post("/{runtime_id}/recreate")
def recreate_kyma(runtime_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger Kyma recreation."""
    runtime = db.query(KymaRuntime).filter(KymaRuntime.id == runtime_id).first()
    if not runtime:
        raise HTTPException(404, "Kyma runtime not found")
    
    account = db.query(Account).filter(Account.id == runtime.account_id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    
    if runtime.status not in ["EXPIRED", "FAILED", "COOLING"]:
        raise HTTPException(400, f"Cannot recreate runtime in {runtime.status} status")
    
    if runtime.cooling_until:
        cooling = runtime.cooling_until.replace(tzinfo=UTC) if runtime.cooling_until.tzinfo is None else runtime.cooling_until
        if cooling > datetime.now(UTC):
            raise HTTPException(400, f"Runtime is cooling until {runtime.cooling_until}")
    
    # Mark as creating
    runtime.status = "CREATING"
    runtime.cooling_until = None
    db.commit()
    
    # Trigger creation in background
    background_tasks.add_task(create_kyma_background, str(account.id), str(runtime.id))
    
    return {"message": "Kyma recreation started", "runtime_id": runtime_id}


def create_kyma_background(account_id: str, runtime_id: str):
    """Background task to create Kyma runtime."""
    from models.database import SessionLocal
    import logging
    
    logger = logging.getLogger(__name__)
    db = SessionLocal()
    
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        runtime = db.query(KymaRuntime).filter(KymaRuntime.id == runtime_id).first()
        
        if not account or not runtime:
            logger.error(f"Account or runtime not found")
            return
        
        client = BTPClient(account.subdomain, account.email, account.password)
        
        if not client.login():
            runtime.status = "FAILED"
            runtime.failed_count = (runtime.failed_count or 0) + 1
            db.commit()
            logger.error(f"Login failed for {account.subdomain}")
            return
        
        subaccount_id = account.subaccount_id or client.get_subaccount_id()
        if not subaccount_id:
            runtime.status = "FAILED"
            db.commit()
            return
        
        # Check if Kyma already exists
        existing = client.get_kyma_instance(subaccount_id)
        if existing:
            runtime.instance_id = existing.get("id")
            runtime.cluster_name = existing.get("name")
            runtime.status = "OK" if existing.get("state") == "OK" else "CREATING"
            runtime.expires_at = datetime.now(UTC) + timedelta(days=14)
            db.commit()
            logger.info(f"Kyma already exists for {account.subdomain}")
            return
        
        # Create new Kyma
        try:
            result = client.create_kyma_runtime(subaccount_id)
            runtime.status = "CREATING"
            db.commit()
            logger.info(f"Kyma creation started for {account.subdomain}")
        except Exception as e:
            runtime.status = "FAILED"
            runtime.failed_count = (runtime.failed_count or 0) + 1
            db.commit()
            logger.error(f"Kyma creation failed: {e}")
    
    finally:
        db.close()
