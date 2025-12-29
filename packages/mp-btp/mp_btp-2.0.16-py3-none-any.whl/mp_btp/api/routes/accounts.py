from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from models import get_db, Account, KymaRuntime, CFOrg
from api.schemas import AccountCreate, AccountResponse
from mp_btp.integrations.btp_cli import verify_account

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("", response_model=List[AccountResponse])
def list_accounts(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Account)
    if status:
        query = query.filter(Account.status == status)
    accounts = query.all()
    return [AccountResponse(
        account_id=a.id, subdomain=a.subdomain, email=a.email,
        status=a.status, created_at=a.created_at, expires_at=a.expires_at
    ) for a in accounts]

@router.post("", response_model=AccountResponse)
def create_account(req: AccountCreate, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.subdomain == req.subdomain).first()
    if existing:
        raise HTTPException(400, "Account with this subdomain already exists")
    
    account = Account(
        subdomain=req.subdomain, email=req.email, password=req.password,
        subaccount_id=req.subaccount_id, expires_at=req.expires_at, tags=req.tags
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return AccountResponse(
        account_id=account.id, subdomain=account.subdomain, email=account.email,
        status=account.status, created_at=account.created_at, expires_at=account.expires_at
    )

@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    return AccountResponse(
        account_id=account.id, subdomain=account.subdomain, email=account.email,
        status=account.status, created_at=account.created_at, expires_at=account.expires_at
    )

@router.patch("/{account_id}")
def update_account(account_id: str, status: Optional[str] = None, notes: Optional[str] = None, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    if status:
        account.status = status
    if notes:
        account.notes = notes
    db.commit()
    return {"message": "Account updated"}

@router.post("/{account_id}/verify")
def verify_account_endpoint(account_id: str, db: Session = Depends(get_db)):
    """Verify account credentials and sync runtime info."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    
    result = verify_account(account.subdomain, account.email, account.password)
    
    if not result["valid"]:
        account.status = "FAILED"
        account.notes = result.get("error", "Verification failed")
        db.commit()
        return {"valid": False, "error": result.get("error")}
    
    # Update subaccount_id
    if result["subaccount_id"]:
        account.subaccount_id = result["subaccount_id"]
    
    # Sync Kyma runtime
    if result["kyma"]:
        kyma_data = result["kyma"]
        kyma = db.query(KymaRuntime).filter(
            KymaRuntime.account_id == account.id
        ).first()
        
        if not kyma:
            kyma = KymaRuntime(account_id=account.id)
            db.add(kyma)
        
        kyma.instance_id = kyma_data["instance_id"]
        kyma.cluster_name = kyma_data["name"]
        kyma.status = "OK" if kyma_data["state"] == "OK" else "FAILED"
        if not kyma.expires_at:
            kyma.expires_at = datetime.now(timezone) + timedelta(days=14)
    
    # Sync CF org
    cf_quota_info = None
    if result["cf"]:
        cf_data = result["cf"]
        cf = db.query(CFOrg).filter(CFOrg.account_id == account.id).first()
        
        if not cf:
            cf = CFOrg(account_id=account.id)
            db.add(cf)
        
        cf.instance_id = cf_data["instance_id"]
        cf.org_name = cf_data["org_name"]
        cf.api_endpoint = cf_data.get("api_endpoint")
        
        # Check CF quota - mark as INVALID if quota is 0
        if cf_data["state"] == "OK" and cf.api_endpoint:
            from mp_btp.integrations.cf import cf_login, cf_get_quota
            # Login without specifying org to auto-select
            if cf_login(cf.api_endpoint, account.email, account.password):
                # Get actual org name from cf target
                import subprocess
                r = subprocess.run(['cf', 'target'], capture_output=True, text=True, timeout=10)
                actual_org = None
                for line in r.stdout.split('\n'):
                    if 'org:' in line.lower():
                        actual_org = line.split(':')[-1].strip()
                        break
                
                if actual_org:
                    cf.org_name = actual_org  # Update to real org name
                    quota = cf_get_quota(actual_org)
                    cf_quota_info = quota
                    if quota.get("valid") and quota.get("memory_mb", 0) == 0:
                        cf.status = "INVALID"  # No quota, cannot deploy
                        cf.memory_quota_mb = 0
                    elif quota.get("valid"):
                        cf.status = "OK"
                        cf.memory_quota_mb = quota.get("memory_mb", 4096)
                    else:
                        cf.status = "OK"
                else:
                    cf.status = "OK"
            else:
                cf.status = "OK" if cf_data["state"] == "OK" else "FAILED"
        else:
            cf.status = "OK" if cf_data["state"] == "OK" else "FAILED"
    
    account.status = "ACTIVE"
    db.commit()
    
    resp = {
        "valid": True,
        "subaccount_id": result["subaccount_id"],
        "kyma": result["kyma"],
        "cf": result["cf"]
    }
    if cf_quota_info:
        resp["cf_quota"] = cf_quota_info
    return resp

@router.get("/{account_id}/runtimes")
def get_account_runtimes(account_id: str, db: Session = Depends(get_db)):
    """Get all runtimes for an account."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "Account not found")
    
    kyma_list = db.query(KymaRuntime).filter(KymaRuntime.account_id == account.id).all()
    cf_list = db.query(CFOrg).filter(CFOrg.account_id == account.id).all()
    
    return {
        "account_id": str(account.id),
        "subdomain": account.subdomain,
        "kyma_runtimes": [{
            "id": str(k.id),
            "instance_id": k.instance_id,
            "cluster_name": k.cluster_name,
            "status": k.status,
            "memory_limit_mb": k.memory_limit_mb,
            "memory_used_mb": k.memory_used_mb,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None
        } for k in kyma_list],
        "cf_orgs": [{
            "id": str(c.id),
            "instance_id": c.instance_id,
            "org_name": c.org_name,
            "status": c.status,
            "memory_quota_mb": c.memory_quota_mb,
            "memory_used_mb": c.memory_used_mb
        } for c in cf_list]
    }
