"""Scheduled tasks for CF daily check, cleanup, and Kyma rebuild."""
import logging
from datetime import date, datetime, UTC, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config import get_config
from models.database import SessionLocal
from models import Account, CFOrg, KymaRuntime, Deployment, DeploymentReplica
from scheduler.cf_pattern import should_be_active_today, update_history, parse_pattern
from tasks.cleanup import cleanup_replica

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def start_scheduler():
    """Start the background scheduler."""
    from models import engine
    from instance_lock import update_heartbeat
    
    config = get_config()
    jobs_config = config.get("scheduled_jobs", {})
    
    # 心跳任务（每 10 秒更新一次）
    scheduler.add_job(
        lambda: update_heartbeat(engine),
        'interval',
        seconds=10,
        id="heartbeat",
        replace_existing=True
    )
    logger.info("Heartbeat task scheduled every 10 seconds")
    
    # CF daily check
    cf_config = jobs_config.get("cf_daily_check", {})
    cf_time = cf_config.get("time", "08:30")
    cf_tz = cf_config.get("timezone", "Asia/Shanghai")
    hour, minute = map(int, cf_time.split(":"))
    
    scheduler.add_job(
        cf_daily_check,
        CronTrigger(hour=hour, minute=minute, timezone=pytz.timezone(cf_tz)),
        id="cf_daily_check",
        replace_existing=True
    )
    logger.info(f"CF daily check scheduled at {cf_time} {cf_tz}")
    
    # Cleanup + Kyma rebuild task
    cleanup_config = jobs_config.get("cleanup", {})
    cleanup_time = cleanup_config.get("time", "01:00")
    cleanup_tz = cleanup_config.get("timezone", "Asia/Shanghai")
    hour, minute = map(int, cleanup_time.split(":"))
    
    scheduler.add_job(
        cleanup_and_rebuild,
        CronTrigger(hour=hour, minute=minute, timezone=pytz.timezone(cleanup_tz)),
        id="cleanup_expired",
        replace_existing=True
    )
    logger.info(f"Cleanup scheduled at {cleanup_time} {cleanup_tz}")
    
    # Check CREATING Kyma every 5 minutes
    scheduler.add_job(
        check_creating_kyma,
        'interval',
        minutes=5,
        id="check_creating_kyma",
        replace_existing=True
    )
    logger.info("Kyma creation check scheduled every 5 minutes")
    
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    scheduler.shutdown()


def cf_daily_check():
    """Daily CF active pattern check and history update."""
    logger.info("Starting CF daily check")
    db = SessionLocal()
    
    try:
        today = date.today()
        cf_orgs = db.query(CFOrg).filter(CFOrg.status == "OK").all()
        
        for cf in cf_orgs:
            account = db.query(Account).filter(Account.id == cf.account_id).first()
            if not account or account.status != "ACTIVE":
                continue
            
            pattern = cf.active_pattern or "7-5"
            history = cf.active_days_history or {}
            
            # Check running deployments
            running = db.query(DeploymentReplica).filter(
                DeploymentReplica.runtime_id == cf.id,
                DeploymentReplica.runtime_type == "cf",
                DeploymentReplica.status == "RUNNING"
            ).count()
            
            was_active = running > 0
            
            # Update history
            window_days = parse_pattern(pattern)[0]
            cf.active_days_history = update_history(history, today, was_active, window_days)
            logger.info(f"CF {cf.org_name}: {'active' if was_active else 'idle'} (pattern: {pattern})")
        
        db.commit()
        logger.info(f"CF daily check completed: {len(cf_orgs)} orgs")
    except Exception as e:
        logger.error(f"CF daily check failed: {e}")
        db.rollback()
    finally:
        db.close()


def cleanup_and_rebuild():
    """
    Cleanup expired resources and rebuild Kyma:
    1. Delete expired deployment resources
    2. Delete expired Kyma runtime from BTP
    3. Rebuild Kyma after cooling period
    """
    logger.info("Starting cleanup and rebuild")
    db = SessionLocal()
    config = get_config()
    
    try:
        now = datetime.now(UTC)
        cooling_hours = config.get("cooling", {}).get("duration_hours", 24)
        
        # 1. Cleanup expired deployments (actually delete resources)
        expired_deployments = db.query(Deployment).filter(
            Deployment.status == "RUNNING",
            Deployment.expires_at != None,
            Deployment.expires_at <= now
        ).all()
        
        for deployment in expired_deployments:
            logger.info(f"Cleaning up expired deployment: {deployment.id}")
            for replica in deployment.replicas_list:
                if replica.status == "RUNNING":
                    cleanup_replica(db, replica)
                replica.status = "STOPPED"
                replica.stopped_at = now
            deployment.status = "STOPPED"
        
        # 2. Handle expiring Kyma (< 2 days) - mark as EXPIRING
        expiring_threshold = now + timedelta(days=2)
        expiring_kyma = db.query(KymaRuntime).filter(
            KymaRuntime.status == "OK",
            KymaRuntime.expires_at <= expiring_threshold,
            KymaRuntime.expires_at > now
        ).all()
        
        for runtime in expiring_kyma:
            runtime.status = "EXPIRING"
            logger.info(f"Kyma {runtime.cluster_name} marked as EXPIRING")
        
        # 3. Handle expired Kyma - delete from BTP and set COOLING
        expired_kyma = db.query(KymaRuntime).filter(
            KymaRuntime.status.in_(["OK", "EXPIRING"]),
            KymaRuntime.expires_at <= now
        ).all()
        
        for runtime in expired_kyma:
            account = db.query(Account).filter(Account.id == runtime.account_id).first()
            if account:
                # Delete from BTP
                delete_kyma_from_btp(account, runtime)
            
            runtime.status = "COOLING"
            runtime.cooling_until = now + timedelta(hours=cooling_hours)
            runtime.memory_used_mb = 0
            logger.info(f"Kyma {runtime.cluster_name} deleted and set to COOLING")
        
        # 4. Rebuild Kyma after cooling period
        cooling_done = db.query(KymaRuntime).filter(
            KymaRuntime.status == "COOLING",
            KymaRuntime.cooling_until <= now
        ).all()
        
        for runtime in cooling_done:
            account = db.query(Account).filter(Account.id == runtime.account_id).first()
            if account and account.status == "ACTIVE":
                # Rebuild Kyma
                success = rebuild_kyma(account, runtime)
                if success:
                    runtime.status = "CREATING"
                    logger.info(f"Kyma rebuild initiated for {account.subdomain}")
                else:
                    runtime.status = "FAILED"
                    runtime.failed_count = (runtime.failed_count or 0) + 1
                    logger.error(f"Kyma rebuild failed for {account.subdomain}")
            else:
                runtime.status = "EXPIRED"
            runtime.cooling_until = None
        
        db.commit()
        logger.info(f"Cleanup done: {len(expired_deployments)} deployments, {len(expired_kyma)} kyma deleted, {len(cooling_done)} kyma rebuilding")
    
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()


def delete_kyma_from_btp(account: Account, runtime: KymaRuntime) -> bool:
    """Delete Kyma runtime from BTP."""
    from integrations.btp_cli import BTPClient
    
    try:
        client = BTPClient(account.subdomain, account.email, account.password)
        if not client.login():
            logger.error(f"BTP login failed for {account.subdomain}")
            return False
        
        subaccount_id = client.get_subaccount_id()
        if not subaccount_id:
            return False
        
        # Delete environment instance
        result = client._run([
            "delete", "accounts/environment-instance", runtime.instance_id,
            "-sa", subaccount_id, "--confirm"
        ], timeout=120)
        
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Delete Kyma failed: {e}")
        return False


def rebuild_kyma(account: Account, runtime: KymaRuntime) -> bool:
    """Rebuild Kyma runtime in BTP (async, takes 20-30 min)."""
    from integrations.btp_cli import BTPClient
    
    try:
        client = BTPClient(account.subdomain, account.email, account.password)
        if not client.login():
            logger.error(f"BTP login failed for {account.subdomain}")
            return False
        
        subaccount_id = account.subaccount_id or client.get_subaccount_id()
        if not subaccount_id:
            return False
        
        # Check if already exists (maybe created manually)
        existing = client.get_kyma_instance(subaccount_id)
        if existing and existing.get("state") == "OK":
            runtime.instance_id = existing.get("id")
            runtime.cluster_name = existing.get("name")
            runtime.status = "OK"
            runtime.expires_at = datetime.now(UTC) + timedelta(days=14)
            logger.info(f"Kyma already exists for {account.subdomain}")
            return True
        
        # Create new Kyma (async, will be CREATING)
        name = runtime.cluster_name or "kyma"
        result = client.create_kyma_runtime(subaccount_id, name)
        
        if result.get("success"):
            runtime.expires_at = datetime.now(UTC) + timedelta(days=14)
            return True
        return False
    except Exception as e:
        logger.error(f"Rebuild Kyma failed: {e}")
        return False


def check_creating_kyma():
    """Check CREATING Kyma status and update when ready."""
    logger.info("Checking CREATING Kyma status")
    db = SessionLocal()
    
    try:
        creating = db.query(KymaRuntime).filter(KymaRuntime.status == "CREATING").all()
        
        for runtime in creating:
            account = db.query(Account).filter(Account.id == runtime.account_id).first()
            if not account:
                continue
            
            from integrations.btp_cli import BTPClient
            client = BTPClient(account.subdomain, account.email, account.password)
            
            if not client.login():
                continue
            
            subaccount_id = account.subaccount_id or client.get_subaccount_id()
            if not subaccount_id:
                continue
            
            kyma = client.get_kyma_instance(subaccount_id)
            if kyma:
                if kyma.get("state") == "OK":
                    runtime.instance_id = kyma.get("id")
                    runtime.cluster_name = kyma.get("name")
                    runtime.status = "OK"
                    runtime.expires_at = datetime.now(UTC) + timedelta(days=14)
                    logger.info(f"Kyma {runtime.cluster_name} is now ready")
                elif kyma.get("state") == "FAILED":
                    runtime.status = "FAILED"
                    runtime.failed_count = (runtime.failed_count or 0) + 1
                    logger.error(f"Kyma creation failed for {account.subdomain}")
                # else still CREATING, do nothing
        
        db.commit()
    except Exception as e:
        logger.error(f"Check creating Kyma failed: {e}")
        db.rollback()
    finally:
        db.close()


# Manual trigger functions for API
def trigger_cleanup():
    """Manually trigger cleanup."""
    cleanup_and_rebuild()


def trigger_cf_check():
    """Manually trigger CF daily check."""
    cf_daily_check()
