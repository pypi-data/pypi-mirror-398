#!/usr/bin/env python3
"""
BTP Scheduler Admin CLI
管理命令行工具

Usage:
    python admin.py accounts list
    python admin.py accounts verify <subdomain>
    python admin.py deploy create --image nginx:alpine --env kyma --memory 256
    python admin.py deploy list
    python admin.py deploy delete <id>
    python admin.py stats
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
import yaml
from mp_btp.models.database import SessionLocal
from mp_btp.models import Account, Deployment, KymaRuntime, CFOrg
from mp_btp.integrations.btp_cli import verify_account
from mp_btp.scheduler.core import select_account_for_deployment
from mp_btp.tasks.deployment import execute_deployment
from datetime import datetime, timezone
import uuid

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
        
        click.echo(f"\n{'子域名':<25} {'邮箱':<30} {'状态':<10} {'过期时间'}")
        click.echo("-" * 80)
        
        for acc in accounts:
            expires = acc.expires_at.strftime('%Y-%m-%d') if acc.expires_at else 'N/A'
            click.echo(f"{acc.subdomain:<25} {acc.email:<30} {acc.status:<10} {expires}")
        
        click.echo(f"\n总计: {len(accounts)} 个账号")
    finally:
        db.close()

@accounts.command('verify')
@click.argument('subdomain')
def accounts_verify(subdomain):
    """验证账号并同步资源"""
    db = SessionLocal()
    try:
        account = db.query(Account).filter(Account.subdomain == subdomain).first()
        if not account:
            click.echo(f"❌ 账号不存在: {subdomain}")
            return
        
        click.echo(f"验证账号: {subdomain}")
        result = verify_account(account.subdomain, account.email, account.password)
        
        # Kyma
        kyma_info = result.get('kyma')
        if kyma_info:
            click.echo(f"\n✓ Kyma: {kyma_info.get('name')} ({kyma_info.get('state')})")
        else:
            click.echo(f"\n✗ Kyma: 不可用")
        
        # CF
        cf_info = result.get('cf')
        if cf_info:
            click.echo(f"✓ CF: {cf_info.get('org_name')} ({cf_info.get('state')})")
        else:
            click.echo(f"✗ CF: 不可用")
        
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

# ============ 部署管理 ============
@cli.group()
def deploy():
    """部署管理"""
    pass

@deploy.command('create')
@click.option('--image', required=True, help='Docker 镜像')
@click.option('--type', 'env_type', type=click.Choice(['kyma', 'cf']), required=True, help='环境类型')
@click.option('--memory', type=int, default=256, help='内存 (MB)')
@click.option('--replicas', type=int, default=1, help='副本数')
@click.option('--port', type=int, help='端口')
@click.option('--disk', type=int, help='磁盘 (MB, 仅 CF)')
@click.option('--env', 'env_vars', multiple=True, help='环境变量 KEY=VALUE')
@click.option('--project', default='default', help='项目名称')
@click.option('--expires', type=int, help='过期天数')
def deploy_create(image, env_type, memory, replicas, port, disk, env_vars, project, expires):
    """创建部署
    
    示例:
      python admin.py deploy create --image nginx:alpine --type kyma --memory 256 --port 80
      python admin.py deploy create --image myapp:latest --type cf --memory 512 --env DB_HOST=localhost --env DB_PORT=5432
    """
    db = SessionLocal()
    try:
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
        
        from mp_btp.models import DeploymentReplica
        for i in range(replicas):
            replica = DeploymentReplica(
                id=str(uuid.uuid4()),
                deployment_id=deployment.id,
                replica_index=i,
                account_id=account.id,
                runtime_id=runtime.id,
                runtime_type=env_type,
                container_name=f"{image.split(':')[0].split('/')[-1]}-{uuid.uuid4().hex[:6]}",
                status='PENDING'
            )
            db.add(replica)
        
        db.commit()
        
        click.echo(f"✓ 创建部署: {deployment.id}")
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
        
        # 异步执行
        import threading
        threading.Thread(target=execute_deployment, args=(deployment.id,), daemon=True).start()
        click.echo(f"\n后台部署中...")
        
    finally:
        db.close()

@deploy.command('list')
@click.option('--status', help='过滤状态')
def deploy_list(status):
    """列出部署"""
    db = SessionLocal()
    try:
        query = db.query(Deployment)
        if status:
            query = query.filter(Deployment.status == status.upper())
        
        deployments = query.order_by(Deployment.created_at.desc()).limit(20).all()
        
        if not deployments:
            click.echo("没有部署")
            return
        
        click.echo(f"\n{'ID':<38} {'镜像':<25} {'环境':<6} {'状态':<10} {'副本'}")
        click.echo("-" * 90)
        
        for dep in deployments:
            click.echo(f"{dep.id} {dep.image:<25} {dep.env_type:<6} {dep.status:<10} {dep.replicas}")
        
        click.echo(f"\n总计: {len(deployments)} 个部署")
    finally:
        db.close()

@deploy.command('info')
@click.argument('deployment_id')
def deploy_info(deployment_id):
    """查看部署详情"""
    db = SessionLocal()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            click.echo(f"❌ 部署不存在: {deployment_id}")
            return
        
        click.echo(f"\n部署ID: {deployment.id}")
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
            click.echo(f"      账号: {account.subdomain}")
            click.echo(f"      状态: {replica.status}")
            if replica.access_url:
                click.echo(f"      URL: {replica.access_url}")
        
    finally:
        db.close()

@deploy.command('delete')
@click.argument('deployment_id')
@click.confirmation_option(prompt='确认删除?')
def deploy_delete(deployment_id):
    """删除部署"""
    db = SessionLocal()
    try:
        deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
        if not deployment:
            click.echo(f"❌ 部署不存在: {deployment_id}")
            return
        
        db.delete(deployment)
        db.commit()
        
        click.echo(f"✓ 已删除: {deployment_id}")
    finally:
        db.close()

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
