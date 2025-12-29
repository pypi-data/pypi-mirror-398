#!/usr/bin/env python3
"""
BTP Scheduler Admin CLI
管理命令行工具

Usage:
    btp-admin deploy create --image nginx:alpine --type kyma --name myapp
    btp-admin deploy list [--project xxx]
    btp-admin deploy info <name>
    btp-admin deploy logs <name>
    btp-admin deploy restart <name>
    btp-admin deploy delete <name>
    btp-admin shell <name>
    btp-admin accounts list
    btp-admin accounts status
    btp-admin stats
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
import yaml
from mp_btp.models.database import SessionLocal
from mp_btp.models import Account, Deployment, KymaRuntime, CFOrg, DeploymentReplica
from mp_btp.integrations.btp_cli import verify_account
from mp_btp.scheduler.core import select_account_for_deployment
from mp_btp.tasks.deployment import execute_deployment
from datetime import datetime, timezone
import uuid


def generate_name(image: str) -> str:
    """生成友好名称: image基础名-随机6位"""
    base = image.split(':')[0].split('/')[-1][:20]
    return f"{base}-{uuid.uuid4().hex[:6]}"


def find_deployment(db, name_or_id: str):
    """模糊匹配部署，支持 name/id 前缀"""
    from sqlalchemy import cast, String
    
    # 精确匹配 name
    d = db.query(Deployment).filter(Deployment.name == name_or_id).first()
    if d:
        return d
    
    # 尝试精确匹配 id (如果是有效 UUID)
    try:
        import uuid as uuid_mod
        uuid_mod.UUID(name_or_id)
        d = db.query(Deployment).filter(Deployment.id == name_or_id).first()
        if d:
            return d
    except ValueError:
        pass
    
    # 前缀匹配 name
    matches = db.query(Deployment).filter(Deployment.name.startswith(name_or_id)).all()
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        names = [f"{m.name}" for m in matches]
        raise click.ClickException(f"匹配到多个部署: {', '.join(names)}")
    
    # 前缀匹配 id (转为字符串比较)
    matches = db.query(Deployment).filter(
        cast(Deployment.id, String).startswith(name_or_id)
    ).all()
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        names = [f"{m.name}({str(m.id)[:8]})" for m in matches]
        raise click.ClickException(f"匹配到多个部署: {', '.join(names)}")
    
    return None


def get_runtime_context(db, replica):
    """获取运行时上下文（kubeconfig 或 CF 登录）"""
    import tempfile
    from mp_btp.integrations.kyma import download_kubeconfig, kyma_login
    from mp_btp.integrations.cf import cf_login, cf_target
    
    account = db.query(Account).filter(Account.id == replica.account_id).first()
    if not account:
        return None, None, "账号不存在"
    
    if replica.runtime_type == "kyma":
        runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
        if not runtime or not runtime.instance_id:
            return None, None, "Kyma 运行时不存在"
        
        fd, kubeconfig = tempfile.mkstemp(suffix='.yaml')
        os.close(fd)
        
        if not download_kubeconfig(runtime.instance_id, kubeconfig):
            return None, None, "下载 kubeconfig 失败"
        
        if not kyma_login(kubeconfig, account.email, account.password):
            os.unlink(kubeconfig)
            return None, None, "Kyma 登录失败"
        
        return kubeconfig, account, None
    else:
        runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
        if not runtime:
            return None, None, "CF 运行时不存在"
        
        if not cf_login(runtime.api_endpoint, account.email, account.password, org=runtime.org_name):
            return None, None, "CF 登录失败"
        
        cf_target(runtime.org_name, "dev")
        return None, account, None


@click.group()
def cli():
    """BTP Scheduler 管理工具"""
    pass

# ============ 账号管理 ============
@cli.group()
def accounts():
    """账号管理"""
    pass

@accounts.command('list')
@click.option('--status', help='过滤状态 (ACTIVE/BANNED/EXPIRED)')
def accounts_list(status):
    """列出所有账号"""
    db = SessionLocal()
    try:
        query = db.query(Account)
        if status:
            query = query.filter(Account.status == status.upper())
        
        accounts = query.all()
        
        if not accounts:
            click.echo("没有账号")
            return
        
        click.echo(f"\n{'邮箱':<28} {'状态':<8} {'区域':<6} {'Kyma':<12} {'CF':<12} {'账号过期'}")
        click.echo("-" * 90)
        
        for acc in accounts:
            # Kyma 信息
            kyma = db.query(KymaRuntime).filter(KymaRuntime.account_id == acc.id).first()
            if kyma and kyma.status == 'OK':
                kyma_days = (kyma.expires_at - datetime.now(timezone.utc).replace(tzinfo=None)).days if kyma.expires_at else '?'
                kyma_str = f"OK({kyma_days}天)"
            elif kyma:
                kyma_str = kyma.status
            else:
                kyma_str = "-"
            
            # CF 信息
            cf = db.query(CFOrg).filter(CFOrg.account_id == acc.id).first()
            if cf and cf.status == 'OK':
                cf_str = f"{cf.memory_quota_mb or 0}M"
            elif cf:
                cf_str = cf.status
            else:
                cf_str = "-"
            
            # 区域 (从 Kyma 或 CF 获取)
            region = (kyma.region if kyma else None) or (cf.region if cf else None) or "-"
            
            # 账号过期
            acc_expires = acc.expires_at.strftime('%m-%d') if acc.expires_at else '-'
            
            click.echo(f"{acc.email:<28} {acc.status:<8} {region:<6} {kyma_str:<12} {cf_str:<12} {acc_expires}")
        
        click.echo(f"\n总计: {len(accounts)} 个账号")
    finally:
        db.close()

@accounts.command('verify')
@click.argument('account_identifier')
def accounts_verify(account_identifier):
    """验证账号并同步资源到数据库（通过 email 或 subdomain 查找）"""
    db = SessionLocal()
    try:
        account = db.query(Account).filter(
            (Account.email == account_identifier) | (Account.subdomain == account_identifier)
        ).first()
        if not account:
            click.echo(f"❌ 账号不存在: {account_identifier}")
            return
        
        click.echo(f"验证账号: {account.email} ({account.subdomain})")
        click.echo("登录 BTP...")
        
        from mp_btp.integrations.btp_cli import BTPClient
        client = BTPClient(account.subdomain, account.email, account.password)
        
        if not client.login():
            click.echo("❌ BTP 登录失败")
            account.status = 'FAILED'
            db.commit()
            return
        
        # 获取 subaccount 详情
        subaccount_id = client.get_subaccount_id()
        if subaccount_id:
            account.subaccount_id = subaccount_id
            # 获取账号过期时间和区域
            sa_info = client.get_subaccount_info(subaccount_id)
            if sa_info:
                if sa_info.get('expires_at'):
                    account.expires_at = sa_info['expires_at']
                click.echo(f"✓ Subaccount: {subaccount_id}")
                if sa_info.get('region'):
                    click.echo(f"  区域: {sa_info['region']}")
                if account.expires_at:
                    days_left = (account.expires_at - datetime.now(timezone.utc).replace(tzinfo=None)).days
                    click.echo(f"  过期: {account.expires_at.strftime('%Y-%m-%d')} ({days_left}天)")
        
        # 获取所有环境实例
        instances = client.list_environment_instances(subaccount_id) if subaccount_id else []
        
        # 更新 Kyma (一般只有一个)
        kyma_instances = [i for i in instances if i.get('type') == 'kyma']
        if kyma_instances:
            kyma_info = kyma_instances[0]
            kyma = db.query(KymaRuntime).filter(KymaRuntime.account_id == account.id).first()
            if not kyma:
                kyma = KymaRuntime(account_id=account.id)
                db.add(kyma)
            kyma.instance_id = kyma_info.get('id')
            kyma.cluster_name = kyma_info.get('name')
            kyma.status = kyma_info.get('state', 'UNKNOWN')
            if kyma_info.get('landscape'):
                kyma.region = kyma_info['landscape']
            # 获取详细信息（过期时间、kubeconfig URL）
            if kyma.instance_id and subaccount_id:
                kyma_detail = client.get_environment_instance(kyma.instance_id, subaccount_id)
                if kyma_detail:
                    if kyma_detail.get('expires_at'):
                        kyma.expires_at = kyma_detail['expires_at']
                    if kyma_detail.get('kubeconfig_url'):
                        kyma.kubeconfig_url = kyma_detail['kubeconfig_url']
            
            days_left = (kyma.expires_at - datetime.now(timezone.utc).replace(tzinfo=None)).days if kyma.expires_at else '?'
            click.echo(f"✓ Kyma: {kyma.cluster_name} ({kyma.status})")
            click.echo(f"    区域: {kyma.region or '?'}, 过期: {days_left}天")
        else:
            click.echo("✗ Kyma: 未创建")
        
        # 更新 CF (可能有多个区域)
        cf_instances = [i for i in instances if i.get('type') == 'cloudfoundry']
        if cf_instances:
            for cf_info in cf_instances:
                cf = db.query(CFOrg).filter(
                    CFOrg.account_id == account.id,
                    CFOrg.instance_id == cf_info.get('id')
                ).first()
                if not cf:
                    cf = CFOrg(account_id=account.id)
                    db.add(cf)
                cf.instance_id = cf_info.get('id')
                cf.org_name = cf_info.get('name')
                cf.api_endpoint = cf_info.get('api_endpoint')
                cf.status = cf_info.get('state', 'UNKNOWN')
                if cf_info.get('landscape'):
                    cf.region = cf_info['landscape'].replace('cf-', '')
                
                # 获取 quota
                quota_str = "?"
                if cf.api_endpoint and cf.status == 'OK':
                    from mp_btp.integrations.cf import cf_login, cf_get_quota
                    if cf_login(cf.api_endpoint, account.email, account.password, org=cf.org_name):
                        quota = cf_get_quota(cf.org_name)
                        if quota:
                            cf.memory_quota_mb = quota.get('memory_limit', 0)
                            cf.memory_used_mb = quota.get('memory_used', 0)
                            quota_str = f"{cf.memory_used_mb}/{cf.memory_quota_mb}M"
                            if cf.memory_quota_mb == 0:
                                cf.status = 'INVALID'
                
                click.echo(f"✓ CF: {cf.org_name} ({cf.status})")
                click.echo(f"    区域: {cf.region or '?'}, 配额: {quota_str}")
        else:
            click.echo("✗ CF: 未创建")
        
        account.status = 'ACTIVE'
        account.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        click.echo("\n✓ 数据库已更新")
        
    finally:
        db.close()

@accounts.command('add')
@click.option('--subdomain', required=True)
@click.option('--email', required=True)
@click.option('--password', required=True)
def accounts_add(subdomain, email, password):
    """添加新账号"""
    db = SessionLocal()
    try:
        existing = db.query(Account).filter(Account.subdomain == subdomain).first()
        if existing:
            click.echo(f"❌ 账号已存在: {subdomain}")
            return
        
        account = Account(
            subdomain=subdomain,
            email=email,
            password=password,
            status='ACTIVE',
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + __import__('datetime').timedelta(days=90)
        )
        db.add(account)
        db.commit()
        
        click.echo(f"✓ 添加账号: {subdomain}")
    finally:
        db.close()


@accounts.command('status')
def accounts_status():
    """查看账号资源状态（从缓存读取，不触发登录）"""
    db = SessionLocal()
    try:
        accounts = db.query(Account).filter(Account.status == 'ACTIVE').all()
        
        if not accounts:
            click.echo("没有活跃账号")
            return
        
        click.echo(f"\n{'账号':<25} {'Kyma':<20} {'CF':<20}")
        click.echo("-" * 70)
        
        for acc in accounts:
            # Kyma 状态
            kyma = db.query(KymaRuntime).filter(KymaRuntime.account_id == acc.id).first()
            if kyma:
                days_left = (kyma.expires_at - datetime.now(timezone.utc).replace(tzinfo=None)).days if kyma.expires_at else '?'
                kyma_str = f"{kyma.status} ({days_left}天)"
            else:
                kyma_str = "未创建"
            
            # CF 状态
            cf = db.query(CFOrg).filter(CFOrg.account_id == acc.id).first()
            if cf:
                quota = f"{cf.memory_used_mb or 0}/{cf.memory_quota_mb}M"
                cf_str = f"{cf.status} {quota}"
            else:
                cf_str = "未创建"
            
            click.echo(f"{acc.subdomain:<25} {kyma_str:<20} {cf_str:<20}")
        
        click.echo(f"\n总计: {len(accounts)} 个活跃账号")
        click.echo("提示: 数据来自缓存，使用 'accounts verify <subdomain>' 更新单个账号")
    finally:
        db.close()


# ============ 部署管理 ============
@cli.group()
def deploy():
    """部署管理"""
    pass

@deploy.command('create')
@click.option('--image', required=True, help='Docker 镜像')
@click.option('--type', 'env_type', type=click.Choice(['kyma', 'cf']), default='kyma', help='环境类型 (默认 kyma)')
@click.option('--name', 'deploy_name', help='部署名称 (不指定则自动生成)')
@click.option('--memory', type=int, default=256, help='内存 (MB)')
@click.option('--replicas', type=int, default=1, help='副本数')
@click.option('--port', type=int, help='端口')
@click.option('--disk', type=int, help='磁盘 (MB, 仅 CF)')
@click.option('--env', 'env_vars', multiple=True, help='环境变量 KEY=VALUE')
@click.option('--project', default='default', help='项目名称')
@click.option('--expires', type=int, help='过期天数')
def deploy_create(image, env_type, deploy_name, memory, replicas, port, disk, env_vars, project, expires):
    """创建部署
    
    示例:
      btp-admin deploy create --image nginx:alpine --type kyma --name myapp
      btp-admin deploy create --image myapp:latest --type cf --memory 512 --env DB_HOST=localhost
    """
    db = SessionLocal()
    try:
        # 自动生成名称
        if not deploy_name:
            deploy_name = generate_name(image)
        
        # 检查名称是否已存在
        existing = db.query(Deployment).filter(
            Deployment.name == deploy_name, Deployment.project == project
        ).first()
        if existing:
            click.echo(f"❌ 名称已存在: {deploy_name} (project={project})")
            return
        
        # 解析环境变量
        parsed_env = {}
        for env in env_vars:
            if '=' in env:
                key, value = env.split('=', 1)
                parsed_env[key] = value
            else:
                click.echo(f"⚠️  忽略无效环境变量: {env}")
        
        # 选择账号
        account, runtime = select_account_for_deployment(db, env_type, memory, wait_for_creating=True)
        
        if not account:
            click.echo("❌ 没有可用账号")
            return
        
        # 计算过期时间
        expires_at = None
        if expires:
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=expires)
        
        # 创建部署
        deployment = Deployment(
            id=str(uuid.uuid4()),
            name=deploy_name,
            project=project,
            env_type=env_type,
            image=image,
            replicas=replicas,
            memory_mb=memory,
            disk_mb=disk,
            port=port,
            env_vars=parsed_env,
            status='PENDING',
            expires_at=expires_at
        )
        db.add(deployment)
        
        for i in range(replicas):
            replica = DeploymentReplica(
                id=str(uuid.uuid4()),
                deployment_id=deployment.id,
                replica_index=i,
                account_id=account.id,
                runtime_id=runtime.id,
                runtime_type=env_type,
                container_name=f"{deploy_name}-{i}" if replicas > 1 else deploy_name,
                status='PENDING'
            )
            db.add(replica)
        
        db.commit()
        
        click.echo(f"✓ 创建部署: {deploy_name}")
        click.echo(f"  ID: {deployment.id}")
        click.echo(f"  镜像: {image}")
        click.echo(f"  类型: {env_type}")
        click.echo(f"  账号: {account.subdomain}")
        click.echo(f"  副本: {replicas}")
        click.echo(f"  内存: {memory}M")
        if port:
            click.echo(f"  端口: {port}")
        if disk:
            click.echo(f"  磁盘: {disk}M")
        if parsed_env:
            click.echo(f"  环境变量: {len(parsed_env)} 个")
            for k, v in parsed_env.items():
                click.echo(f"    {k}={v}")
        if expires:
            click.echo(f"  过期: {expires} 天后")
        
        # 启动独立进程执行部署
        import subprocess
        import shutil
        
        btp_admin = shutil.which('btp-admin')
        if btp_admin:
            subprocess.Popen(
                [btp_admin, 'deploy', 'execute', str(deployment.id)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            click.echo(f"\n后台部署中，使用以下命令查看状态:")
            click.echo(f"  btp-admin deploy info {deploy_name}")
        else:
            click.echo(f"\n⚠️  无法启动后台进程，请手动执行:")
            click.echo(f"  btp-admin deploy execute {deployment.id}")
        
    finally:
        db.close()

@deploy.command('list')
@click.option('--status', help='过滤状态')
@click.option('--project', help='过滤项目')
def deploy_list(status, project):
    """列出部署"""
    db = SessionLocal()
    try:
        query = db.query(Deployment)
        if status:
            query = query.filter(Deployment.status == status.upper())
        if project:
            query = query.filter(Deployment.project == project)
        
        deployments = query.order_by(Deployment.created_at.desc()).limit(20).all()
        
        if not deployments:
            click.echo("没有部署")
            return
        
        click.echo(f"\n{'名称':<20} {'镜像':<25} {'类型':<6} {'状态':<10} {'账号'}")
        click.echo("-" * 90)
        
        for dep in deployments:
            name = dep.name or dep.id[:8]
            image = dep.image[:24] if len(dep.image) > 24 else dep.image
            account_sub = ""
            if dep.replicas_list:
                replica = dep.replicas_list[0]
                account = db.query(Account).filter(Account.id == replica.account_id).first()
                if account:
                    account_sub = account.subdomain
            
            click.echo(f"{name:<20} {image:<25} {dep.env_type:<6} {dep.status:<10} {account_sub}")
        
        click.echo(f"\n总计: {len(deployments)} 个部署")
    finally:
        db.close()

@deploy.command('info')
@click.argument('name_or_id')
def deploy_info(name_or_id):
    """查看部署详情"""
    db = SessionLocal()
    try:
        deployment = find_deployment(db, name_or_id)
        if not deployment:
            click.echo(f"❌ 部署不存在: {name_or_id}")
            return
        
        click.echo(f"\n名称: {deployment.name or 'N/A'}")
        click.echo(f"ID: {deployment.id}")
        click.echo(f"项目: {deployment.project}")
        click.echo(f"镜像: {deployment.image}")
        click.echo(f"类型: {deployment.env_type}")
        click.echo(f"状态: {deployment.status}")
        click.echo(f"副本数: {deployment.replicas}")
        click.echo(f"内存: {deployment.memory_mb}M")
        if deployment.disk_mb:
            click.echo(f"磁盘: {deployment.disk_mb}M")
        if deployment.port:
            click.echo(f"端口: {deployment.port}")
        
        if deployment.env_vars:
            click.echo(f"\n环境变量:")
            for k, v in deployment.env_vars.items():
                click.echo(f"  {k}={v}")
        if deployment.expires_at:
            click.echo(f"\n过期时间: {deployment.expires_at}")
        
        click.echo(f"\n副本列表:")
        for replica in deployment.replicas_list:
            account = db.query(Account).filter(Account.id == replica.account_id).first()
            click.echo(f"  [{replica.replica_index}] {replica.container_name}")
            click.echo(f"      账号: {account.subdomain if account else 'N/A'}")
            click.echo(f"      状态: {replica.status}")
            if replica.access_url:
                click.echo(f"      URL: {replica.access_url}")
        
    finally:
        db.close()

@deploy.command('execute')
@click.argument('deployment_id')
def deploy_execute(deployment_id):
    """手动执行部署"""
    from mp_btp.tasks.deployment import execute_deployment
    
    click.echo(f"执行部署: {deployment_id}")
    try:
        execute_deployment(deployment_id)
        click.echo("✓ 部署执行完成")
    except Exception as e:
        click.echo(f"❌ 部署失败: {e}")

@deploy.command('delete')
@click.argument('name_or_id')
@click.option('--force', '-f', is_flag=True, help='跳过确认')
def deploy_delete(name_or_id, force):
    """删除部署（包括远程资源）"""
    db = SessionLocal()
    try:
        deployment = find_deployment(db, name_or_id)
        if not deployment:
            click.echo(f"❌ 部署不存在: {name_or_id}")
            return
        
        if not force:
            click.confirm(f"确认删除 {deployment.name or deployment.id}?", abort=True)
        
        # 清理远程资源
        from mp_btp.tasks.cleanup import cleanup_replica
        
        for replica in deployment.replicas_list:
            click.echo(f"清理副本 [{replica.replica_index}] {replica.container_name}...")
            if cleanup_replica(db, replica):
                click.echo(f"  ✓ 已清理")
            else:
                click.echo(f"  ⚠️  清理失败（可能已不存在）")
        
        db.delete(deployment)
        db.commit()
        
        click.echo(f"✓ 已删除: {deployment.name or deployment.id}")
    finally:
        db.close()


@deploy.command('logs')
@click.argument('name_or_id')
@click.option('--tail', '-n', default=100, help='显示最后 N 行')
def deploy_logs(name_or_id, tail):
    """查看部署日志"""
    db = SessionLocal()
    try:
        deployment = find_deployment(db, name_or_id)
        if not deployment:
            click.echo(f"❌ 部署不存在: {name_or_id}")
            return
        
        replica = deployment.replicas_list[0] if deployment.replicas_list else None
        if not replica:
            click.echo("❌ 没有副本")
            return
        
        kubeconfig, account, err = get_runtime_context(db, replica)
        if err:
            click.echo(f"❌ {err}")
            return
        
        if replica.runtime_type == "kyma":
            from mp_btp.integrations.kyma import kyma_logs
            logs = kyma_logs(kubeconfig, replica.container_name, tail=tail)
            os.unlink(kubeconfig)
        else:
            from mp_btp.integrations.cf import cf_logs
            logs = cf_logs(replica.container_name)
        
        click.echo(logs or "（无日志）")
    finally:
        db.close()


@deploy.command('restart')
@click.argument('name_or_id')
def deploy_restart(name_or_id):
    """重启部署"""
    db = SessionLocal()
    try:
        deployment = find_deployment(db, name_or_id)
        if not deployment:
            click.echo(f"❌ 部署不存在: {name_or_id}")
            return
        
        replica = deployment.replicas_list[0] if deployment.replicas_list else None
        if not replica:
            click.echo("❌ 没有副本")
            return
        
        kubeconfig, account, err = get_runtime_context(db, replica)
        if err:
            click.echo(f"❌ {err}")
            return
        
        click.echo(f"重启 {deployment.name or deployment.id}...")
        
        if replica.runtime_type == "kyma":
            from mp_btp.integrations.kyma import kyma_restart
            ok = kyma_restart(kubeconfig, replica.container_name)
            os.unlink(kubeconfig)
        else:
            from mp_btp.integrations.cf import cf_restart
            ok = cf_restart(replica.container_name)
        
        if ok:
            click.echo("✓ 重启成功")
        else:
            click.echo("❌ 重启失败")
    finally:
        db.close()


@deploy.command('scale')
@click.argument('name_or_id')
@click.option('--replicas', '-r', type=int, required=True, help='副本数')
def deploy_scale(name_or_id, replicas):
    """调整副本数（仅 Kyma）"""
    db = SessionLocal()
    try:
        deployment = find_deployment(db, name_or_id)
        if not deployment:
            click.echo(f"❌ 部署不存在: {name_or_id}")
            return
        
        replica = deployment.replicas_list[0] if deployment.replicas_list else None
        if not replica:
            click.echo("❌ 没有副本")
            return
        
        if replica.runtime_type != "kyma":
            click.echo("❌ scale 仅支持 Kyma 部署")
            return
        
        kubeconfig, account, err = get_runtime_context(db, replica)
        if err:
            click.echo(f"❌ {err}")
            return
        
        from mp_btp.integrations.kyma import kyma_scale
        click.echo(f"调整 {deployment.name or deployment.id} 副本数为 {replicas}...")
        
        ok = kyma_scale(kubeconfig, replica.container_name, replicas)
        os.unlink(kubeconfig)
        
        if ok:
            click.echo("✓ 调整成功")
        else:
            click.echo("❌ 调整失败")
    finally:
        db.close()


@deploy.command('update')
@click.argument('name_or_id')
@click.option('--memory', type=int, help='内存 (MB)')
@click.option('--env', 'env_vars', multiple=True, help='环境变量 KEY=VALUE')
@click.option('--image', help='镜像')
def deploy_update(name_or_id, memory, env_vars, image):
    """更新部署参数（删除重建）"""
    db = SessionLocal()
    try:
        deployment = find_deployment(db, name_or_id)
        if not deployment:
            click.echo(f"❌ 部署不存在: {name_or_id}")
            return
        
        # 记录原参数
        old_name = deployment.name
        old_image = deployment.image
        old_memory = deployment.memory_mb
        old_env = deployment.env_vars or {}
        
        # 更新参数
        new_image = image or old_image
        new_memory = memory or old_memory
        new_env = dict(old_env)
        for env in env_vars:
            if '=' in env:
                k, v = env.split('=', 1)
                new_env[k] = v
        
        click.echo(f"更新 {old_name}:")
        if image:
            click.echo(f"  镜像: {old_image} → {new_image}")
        if memory:
            click.echo(f"  内存: {old_memory}M → {new_memory}M")
        if env_vars:
            click.echo(f"  环境变量: +{len(env_vars)} 个")
        
        # 清理旧资源
        from mp_btp.tasks.cleanup import cleanup_replica
        for replica in deployment.replicas_list:
            cleanup_replica(db, replica)
        
        # 更新数据库
        deployment.image = new_image
        deployment.memory_mb = new_memory
        deployment.env_vars = new_env
        deployment.status = 'PENDING'
        for replica in deployment.replicas_list:
            replica.status = 'PENDING'
        db.commit()
        
        # 重新部署
        import subprocess
        import shutil
        btp_admin = shutil.which('btp-admin')
        if btp_admin:
            subprocess.Popen(
                [btp_admin, 'deploy', 'execute', str(deployment.id)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
            )
            click.echo(f"\n后台重新部署中...")
        else:
            click.echo(f"\n请手动执行: btp-admin deploy execute {deployment.id}")
    finally:
        db.close()


@deploy.command('exec')
@click.argument('name_or_id')
@click.argument('command', nargs=-1, required=True)
def deploy_exec(name_or_id, command):
    """在容器中执行命令
    
    示例: btp-admin deploy exec myapp -- ls -la
    """
    db = SessionLocal()
    try:
        deployment = find_deployment(db, name_or_id)
        if not deployment:
            click.echo(f"❌ 部署不存在: {name_or_id}")
            return
        
        replica = deployment.replicas_list[0] if deployment.replicas_list else None
        if not replica:
            click.echo("❌ 没有副本")
            return
        
        kubeconfig, account, err = get_runtime_context(db, replica)
        if err:
            click.echo(f"❌ {err}")
            return
        
        if replica.runtime_type == "kyma":
            from mp_btp.integrations.kyma import kyma_exec
            ok, output = kyma_exec(kubeconfig, replica.container_name, list(command))
            os.unlink(kubeconfig)
        else:
            from mp_btp.integrations.cf import cf_ssh_exec
            ok, output = cf_ssh_exec(replica.container_name, ' '.join(command))
        
        click.echo(output)
    finally:
        db.close()


# ============ Shell 命令 ============
@cli.command('shell')
@click.argument('name_or_id')
@click.option('--replica', '-r', default=0, help='副本索引')
def shell_cmd(name_or_id, replica):
    """进入容器 Shell（自动判断 Kyma/CF）"""
    db = SessionLocal()
    try:
        deployment = find_deployment(db, name_or_id)
        if not deployment:
            click.echo(f"❌ 部署不存在: {name_or_id}")
            return
        
        rep = None
        for r in deployment.replicas_list:
            if r.replica_index == replica:
                rep = r
                break
        
        if not rep:
            click.echo(f"❌ 副本 {replica} 不存在")
            return
        
        account = db.query(Account).filter(Account.id == rep.account_id).first()
        if not account:
            click.echo("❌ 账号不存在")
            return
        
        if rep.runtime_type == "kyma":
            _shell_kyma(db, rep, account)
        else:
            _shell_cf(db, rep, account)
    finally:
        db.close()


def _shell_kyma(db, replica, account):
    """进入 Kyma Pod Shell"""
    import subprocess
    import tempfile
    from mp_btp.integrations.kyma import download_kubeconfig, kyma_login
    
    runtime = db.query(KymaRuntime).filter(KymaRuntime.id == replica.runtime_id).first()
    if not runtime or not runtime.instance_id:
        click.echo("❌ Kyma 运行时不存在")
        return
    
    fd, kubeconfig = tempfile.mkstemp(suffix='.yaml')
    os.close(fd)
    
    click.echo("下载 kubeconfig...")
    if not download_kubeconfig(runtime.instance_id, kubeconfig):
        click.echo("❌ 下载失败")
        return
    
    click.echo(f"登录 Kyma ({account.email})...")
    if not kyma_login(kubeconfig, account.email, account.password):
        os.unlink(kubeconfig)
        click.echo("❌ 登录失败")
        return
    
    os.environ["KUBECONFIG"] = kubeconfig
    
    # 获取 pod 名称
    r = subprocess.run(
        ["kubectl", "get", "pods", "-l", f"app={replica.container_name}", "-o", "jsonpath={.items[0].metadata.name}"],
        capture_output=True, text=True
    )
    if r.returncode != 0 or not r.stdout:
        click.echo(f"❌ Pod 不存在: {replica.container_name}")
        os.unlink(kubeconfig)
        return
    
    pod = r.stdout.strip()
    click.echo(f"连接到 {pod}...")
    os.execvp("kubectl", ["kubectl", "exec", "-it", pod, "--", "/bin/sh"])


def _shell_cf(db, replica, account):
    """进入 CF App Shell"""
    import subprocess
    from mp_btp.integrations.cf import cf_login, cf_target
    
    runtime = db.query(CFOrg).filter(CFOrg.id == replica.runtime_id).first()
    if not runtime:
        click.echo("❌ CF 运行时不存在")
        return
    
    click.echo(f"登录 CF ({account.email})...")
    if not cf_login(runtime.api_endpoint, account.email, account.password, org=runtime.org_name):
        click.echo("❌ 登录失败")
        return
    
    cf_target(runtime.org_name, "dev")
    
    click.echo(f"连接到 {replica.container_name}...")
    os.execvp("cf", ["cf", "ssh", replica.container_name])


# ============ 统计信息 ============
@cli.command()
def stats():
    """显示统计信息"""
    db = SessionLocal()
    try:
        total_accounts = db.query(Account).count()
        active_accounts = db.query(Account).filter(Account.status == 'ACTIVE').count()
        
        total_kyma = db.query(KymaRuntime).count()
        ok_kyma = db.query(KymaRuntime).filter(KymaRuntime.status == 'OK').count()
        
        total_cf = db.query(CFOrg).count()
        ok_cf = db.query(CFOrg).filter(CFOrg.status == 'OK').count()
        
        total_deployments = db.query(Deployment).count()
        running_deployments = db.query(Deployment).filter(Deployment.status == 'RUNNING').count()
        
        click.echo("\n=== BTP Scheduler 统计 ===\n")
        click.echo(f"账号: {active_accounts}/{total_accounts} 活跃")
        click.echo(f"Kyma: {ok_kyma}/{total_kyma} 可用")
        click.echo(f"CF: {ok_cf}/{total_cf} 可用")
        click.echo(f"部署: {running_deployments}/{total_deployments} 运行中")
        
    finally:
        db.close()

# ============ 维护 ============
@cli.group()
def maintenance():
    """维护任务"""
    pass

@maintenance.command('cleanup')
def maintenance_cleanup():
    """清理过期资源"""
    from mp_btp.tasks.cleanup import cleanup_expired_resources
    click.echo("开始清理过期资源...")
    cleanup_expired_resources()
    click.echo("✓ 清理完成")

@maintenance.command('cf-check')
def maintenance_cf_check():
    """CF 日检"""
    from mp_btp.tasks.scheduled import update_cf_active_history
    click.echo("开始 CF 日检...")
    update_cf_active_history()
    click.echo("✓ 日检完成")

@deploy.command('from-compose')
@click.option('--file', 'compose_file', required=True, help='docker-compose.yml 文件')
@click.option('--project', default='default', help='项目名称')
def deploy_from_compose(compose_file, project):
    """从 docker-compose.yml 部署到 Kyma
    
    示例:
      python admin.py deploy from-compose --file docker-compose.yml --project myapp
    
    注意: 所有服务部署到同一个 Kyma
    """
    from utils.compose_parser import parse_docker_compose, compose_to_k8s_yaml
    
    if not os.path.exists(compose_file):
        click.echo(f"❌ 文件不存在: {compose_file}")
        return
    
    click.echo(f"解析 {compose_file}...")
    
    try:
        deployments = parse_docker_compose(compose_file)
    except Exception as e:
        click.echo(f"❌ 解析失败: {e}")
        return
    
    if not deployments:
        click.echo("❌ 没有找到服务")
        return
    
    click.echo(f"✓ 发现 {len(deployments)} 个服务\n")
    
    # 计算总内存
    total_memory = sum(d['memory_mb'] for d in deployments)
    
    db = SessionLocal()
    try:
        # 选择一个 Kyma 账号
        account, runtime = select_account_for_deployment(db, "kyma", total_memory, wait_for_creating=False)
        
        if not account:
            click.echo("❌ 没有可用 Kyma 账号")
            return
        
        click.echo(f"选择账号: {account.subdomain}")
        click.echo(f"总内存: {total_memory}M\n")
        
        # 生成 K8s YAML
        k8s_yaml = compose_to_k8s_yaml(deployments, project)
        
        # 创建部署记录
        deployment = Deployment(
            id=str(uuid.uuid4()),
            project=project,
            env_type='kyma',
            image=f"compose:{len(deployments)}services",
            replicas=len(deployments),
            memory_mb=total_memory,
            status='PENDING',
            raw_yaml=k8s_yaml,
            deploy_type='compose'
        )
        db.add(deployment)
        
        from mp_btp.models import DeploymentReplica
        replica = DeploymentReplica(
            id=str(uuid.uuid4()),
            deployment_id=deployment.id,
            replica_index=0,
            account_id=account.id,
            runtime_id=runtime.id,
            runtime_type='kyma',
            container_name=f"{project}-compose",
            status='PENDING'
        )
        db.add(replica)
        db.commit()
        
        click.echo(f"创建部署:")
        for i, dep in enumerate(deployments, 1):
            click.echo(f"  [{i}/{len(deployments)}] {dep['name']}")
            click.echo(f"      镜像: {dep['image']}")
            click.echo(f"      内存: {dep['memory_mb']}M")
            if dep['port']:
                click.echo(f"      端口: {dep['port']}")
            if dep['shm_size']:
                click.echo(f"      SHM: {dep['shm_size']}G")
        
        click.echo(f"\n部署ID: {deployment.id}")
        click.echo(f"后台部署中...")
        
        # 异步执行
        import threading
        threading.Thread(target=execute_deployment, args=(deployment.id,), daemon=True).start()
        
    finally:
        db.close()


@deploy.command('from-k8s')
@click.option('--file', 'k8s_file', required=True, help='K8s YAML 文件 (或 - 表示 stdin)')
@click.option('--project', default='default', help='项目名称')
def deploy_from_k8s(k8s_file, project):
    """从 K8s YAML 直接部署到 Kyma
    
    示例:
      python admin.py deploy from-k8s --file deployment.yaml --project myapp
      cat deployment.yaml | python admin.py deploy from-k8s --file - --project myapp
    
    支持完整 K8s 特性 (volumeMounts, resources, 等)
    """
    from utils.compose_parser import validate_k8s_yaml
    
    # 读取 YAML
    if k8s_file == '-':
        k8s_yaml = sys.stdin.read()
    else:
        if not os.path.exists(k8s_file):
            click.echo(f"❌ 文件不存在: {k8s_file}")
            return
        with open(k8s_file) as f:
            k8s_yaml = f.read()
    
    # 简单验证
    try:
        docs = list(yaml.safe_load_all(k8s_yaml))
        if not docs:
            click.echo("❌ YAML 为空")
            return
    except Exception as e:
        click.echo(f"❌ YAML 格式错误: {e}")
        return
    
    click.echo(f"✓ 解析 {len(docs)} 个 K8s 资源\n")
    
    db = SessionLocal()
    try:
        # 选择 Kyma 账号 (默认 512M)
        account, runtime = select_account_for_deployment(db, "kyma", 512, wait_for_creating=False)
        
        if not account:
            click.echo("❌ 没有可用 Kyma 账号")
            return
        
        click.echo(f"选择账号: {account.subdomain}\n")
        
        # 创建部署记录
        deployment = Deployment(
            id=str(uuid.uuid4()),
            project=project,
            env_type='kyma',
            image='k8s-yaml',
            replicas=1,
            memory_mb=512,
            status='PENDING',
            raw_yaml=k8s_yaml,
            deploy_type='k8s-yaml'
        )
        db.add(deployment)
        
        from mp_btp.models import DeploymentReplica
        replica = DeploymentReplica(
            id=str(uuid.uuid4()),
            deployment_id=deployment.id,
            replica_index=0,
            account_id=account.id,
            runtime_id=runtime.id,
            runtime_type='kyma',
            container_name=f"{project}-k8s",
            status='PENDING'
        )
        db.add(replica)
        db.commit()
        
        click.echo(f"✓ 创建部署: {deployment.id}")
        click.echo(f"  项目: {project}")
        click.echo(f"  资源数: {len(docs)}")
        click.echo(f"\n后台部署中...")
        
        # 异步执行
        import threading
        threading.Thread(target=execute_deployment, args=(deployment.id,), daemon=True).start()
        
    finally:
        db.close()


if __name__ == '__main__':
    cli()
