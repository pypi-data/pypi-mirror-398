from sqlalchemy.orm import Session
from mp_btp.models import Account, KymaRuntime, CFOrg
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List, Union
from mp_btp.config import get_config
import logging
config = get_config()
logger = logging.getLogger(__name__)
def select_account_for_deployment(
    db: Session, 
    env_type: str, 
    memory_mb: int,
    wait_for_creating: bool = True
) -> Tuple[Optional[Account], Optional[Union[KymaRuntime, CFOrg]]]:
    accounts = db.query(Account).filter(Account.status == "ACTIVE").all()
    if not accounts:
        return None, None
    best_account = None
    best_runtime = None
    best_score = -1
    for account in accounts:
        if env_type == "kyma":
            runtime = db.query(KymaRuntime).filter(
                KymaRuntime.account_id == account.id,
                KymaRuntime.status.in_(["OK", "EXPIRING"]),
                KymaRuntime.instance_id != None
            ).first()
            if not runtime:
                continue
            score = calculate_kyma_score(runtime, memory_mb)
        else:
            runtime = db.query(CFOrg).filter(
                CFOrg.account_id == account.id,
                CFOrg.status == "OK",
                CFOrg.memory_quota_mb > 0,
                CFOrg.instance_id != None
            ).first()
            if not runtime:
                continue
            score = calculate_cf_score(runtime, memory_mb)
        if score > 0 and score > best_score:
            best_score = score
            best_account = account
            best_runtime = runtime
    if best_runtime:
        return best_account, best_runtime
    if env_type == "kyma" and wait_for_creating:
        creating = db.query(KymaRuntime).filter(
            KymaRuntime.status == "CREATING"
        ).first()
        if creating:
            account = db.query(Account).filter(Account.id == creating.account_id).first()
            logger.info(f"Using CREATING Kyma for {account.subdomain}, deployment will wait")
            return account, creating
        for account in accounts:
            runtime = db.query(KymaRuntime).filter(
                KymaRuntime.account_id == account.id,
                KymaRuntime.status.in_(["EXPIRED", "FAILED"]),
                KymaRuntime.cooling_until == None
            ).first()
            if runtime:
                if trigger_kyma_creation(account, runtime, db):
                    logger.info(f"Triggered Kyma creation for {account.subdomain}")
                    return account, runtime
        for account in accounts:
            existing_kyma = db.query(KymaRuntime).filter(
                KymaRuntime.account_id == account.id
            ).first()
            if not existing_kyma:
                import uuid
                runtime = KymaRuntime(
                    id=str(uuid.uuid4()),
                    account_id=account.id,
                    cluster_name="kyma",
                    status="CREATING",
                    created_at=datetime.now()
                )
                db.add(runtime)
                db.commit()
                if trigger_kyma_creation(account, runtime, db):
                    logger.info(f"Created and triggered Kyma for {account.subdomain}")
                    return account, runtime
    if env_type == "cf":
        for account in accounts:
            existing_cf = db.query(CFOrg).filter(
                CFOrg.account_id == account.id
            ).first()
            if not existing_cf:
                import uuid
                cf_org = CFOrg(
                    id=str(uuid.uuid4()),
                    account_id=account.id,
                    org_name="default",
                    status="CREATING",
                    created_at=datetime.now()
                )
                db.add(cf_org)
                db.commit()
                logger.info(f"Created CF org for {account.subdomain}")
                return account, cf_org
    return None, None
def trigger_kyma_creation(account: Account, runtime: KymaRuntime, db: Session) -> bool:
    accounts = db.query(Account).filter(Account.status == "ACTIVE").all()
    if not accounts:
        return []
    scored = []
    for account in accounts:
        if env_type == "kyma":
            runtime = db.query(KymaRuntime).filter(
                KymaRuntime.account_id == account.id,
                KymaRuntime.status.in_(["OK", "EXPIRING"]),
                KymaRuntime.instance_id != None
            ).first()
            if not runtime:
                continue
            score = calculate_kyma_score(runtime, memory_mb)
        else:
            runtime = db.query(CFOrg).filter(
                CFOrg.account_id == account.id,
                CFOrg.status == "OK",
                CFOrg.memory_quota_mb > 0,
                CFOrg.instance_id != None
            ).first()
            if not runtime:
                continue
            score = calculate_cf_score(runtime, memory_mb)
        if score > 0:
            scored.append((account, runtime, score))
    if not scored:
        return []
    scored.sort(key=lambda x: x[2], reverse=True)
    if replica_count <= 3:
        selected_count = min(2, len(scored))
    else:
        selected_count = min(3, len(scored))
    selected = scored[:selected_count]
    assignments = []
    for i in range(replica_count):
        account, runtime, _ = selected[i % len(selected)]
        assignments.append((account, runtime))
    return assignments
def calculate_kyma_score(runtime: KymaRuntime, memory_mb: int) -> float:
    score = 100.0
    quota = runtime.memory_quota_mb or 0
    if quota == 0:
        return 0
    used = runtime.memory_used_mb or 0
    available = quota - used
    if available < memory_mb:
        return 0
    usage_ratio = used / quota
    if 0.4 <= usage_ratio <= 0.7:
        score += 20
    elif usage_ratio > 0.7:
        score -= 10
    else:
        score += 10
    return score