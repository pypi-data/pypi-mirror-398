    from mp_btp.models import engine
    from instance_lock import update_heartbeat
    config = get_config()
    jobs_config = config.get("scheduled_jobs", {})
    scheduler.add_job(
        lambda: update_heartbeat(engine),
        'interval',
        seconds=10,
        id="heartbeat",
        replace_existing=True
    )
    logger.info("Heartbeat task scheduled every 10 seconds")
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
    Cleanup expired resources and rebuild Kyma:
    1. Delete expired deployment resources
    2. Delete expired Kyma runtime from BTP
    3. Rebuild Kyma after cooling period
    from mp_btp.integrations.btp_cli import BTPClient
    try:
        client = BTPClient(account.subdomain, account.email, account.password)
        if not client.login():
            logger.error(f"BTP login failed for {account.subdomain}")
            return False
        subaccount_id = client.get_subaccount_id()
        if not subaccount_id:
            return False
        result = client._run([
            "delete", "accounts/environment-instance", runtime.instance_id,
            "-sa", subaccount_id, "--confirm"
        ], timeout=120)
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Delete Kyma failed: {e}")
        return False
def rebuild_kyma(account: Account, runtime: KymaRuntime) -> bool:
    logger.info("Checking CREATING Kyma status")
    db = SessionLocal()
    try:
        creating = db.query(KymaRuntime).filter(KymaRuntime.status == "CREATING").all()
        for runtime in creating:
            account = db.query(Account).filter(Account.id == runtime.account_id).first()
            if not account:
                continue
            from mp_btp.integrations.btp_cli import BTPClient
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
                    runtime.expires_at = datetime.now(timezone.utc) + timedelta(days=14)
                    logger.info(f"Kyma {runtime.cluster_name} is now ready")
                elif kyma.get("state") == "FAILED":
                    runtime.status = "FAILED"
                    runtime.failed_count = (runtime.failed_count or 0) + 1
                    logger.error(f"Kyma creation failed for {account.subdomain}")
        db.commit()
    except Exception as e:
        logger.error(f"Check creating Kyma failed: {e}")
        db.rollback()
    finally:
        db.close()
def trigger_cleanup():
    cf_daily_check()