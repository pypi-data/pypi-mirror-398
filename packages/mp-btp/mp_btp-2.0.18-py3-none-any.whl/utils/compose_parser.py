#!/usr/bin/env python3
"""
Docker Compose 和 K8s YAML 解析工具
"""
import yaml
from typing import Dict, List, Optional

def parse_docker_compose(compose_file: str) -> List[Dict]:
    """
    解析 docker-compose.yml，提取基本配置
    
    返回: [{'name': 'web', 'image': 'nginx', 'port': 80, ...}, ...]
    """
    with open(compose_file) as f:
        compose = yaml.safe_load(f)
    
    services = compose.get('services', {})
    deployments = []
    
    for name, config in services.items():
        deployment = {
            'name': name,
            'image': config.get('image'),
            'env_vars': {},
            'memory_mb': 256,  # 默认
            'replicas': 1,
            'port': None,
            'shm_size': None
        }
        
        # 环境变量
        env = config.get('environment', [])
        if isinstance(env, list):
            for item in env:
                if '=' in item:
                    k, v = item.split('=', 1)
                    deployment['env_vars'][k] = v
        elif isinstance(env, dict):
            deployment['env_vars'] = env
        
        # 端口 (取第一个)
        ports = config.get('ports', [])
        if ports:
            port_str = str(ports[0])
            if ':' in port_str:
                deployment['port'] = int(port_str.split(':')[-1])
            else:
                deployment['port'] = int(port_str)
        
        # 资源限制
        deploy_config = config.get('deploy', {})
        resources = deploy_config.get('resources', {})
        limits = resources.get('limits', {})
        
        if 'memory' in limits:
            mem_str = limits['memory']
            if mem_str.endswith('M'):
                deployment['memory_mb'] = int(mem_str[:-1])
            elif mem_str.endswith('G'):
                deployment['memory_mb'] = int(float(mem_str[:-1]) * 1024)
        
        # 副本数
        deployment['replicas'] = deploy_config.get('replicas', 1)
        
        # shm_size (浏览器需要)
        shm_size = config.get('shm_size')
        if shm_size:
            if shm_size.endswith('gb'):
                deployment['shm_size'] = int(shm_size[:-2])
            elif shm_size.endswith('g'):
                deployment['shm_size'] = int(shm_size[:-1])
        
        deployments.append(deployment)
    
    return deployments


def compose_to_k8s_yaml(deployments: List[Dict], project: str) -> str:
    """
    将 compose 配置转换为 K8s YAML
    所有服务部署到同一个 namespace
    """
    resources = []
    
    for dep in deployments:
        name = f"{project}-{dep['name']}"
        
        # Deployment
        containers = [{
            'name': dep['name'],
            'image': dep['image'],
            'resources': {
                'requests': {'memory': f"{dep['memory_mb']}Mi"},
                'limits': {'memory': f"{dep['memory_mb']}Mi"}
            }
        }]
        
        # 端口
        if dep['port']:
            containers[0]['ports'] = [{'containerPort': dep['port']}]
        
        # 环境变量
        if dep['env_vars']:
            containers[0]['env'] = [
                {'name': k, 'value': str(v)} 
                for k, v in dep['env_vars'].items()
            ]
        
        # volumeMounts (shm)
        volumes = []
        if dep['shm_size']:
            containers[0]['volumeMounts'] = [{
                'mountPath': '/dev/shm',
                'name': 'dshm'
            }]
            volumes.append({
                'name': 'dshm',
                'emptyDir': {
                    'medium': 'Memory',
                    'sizeLimit': f"{dep['shm_size']}Gi"
                }
            })
        
        deployment_obj = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': name,
                'labels': {'app': name, 'project': project}
            },
            'spec': {
                'replicas': dep['replicas'],
                'selector': {'matchLabels': {'app': name}},
                'template': {
                    'metadata': {'labels': {'app': name, 'project': project}},
                    'spec': {
                        'containers': containers
                    }
                }
            }
        }
        
        if volumes:
            deployment_obj['spec']['template']['spec']['volumes'] = volumes
        
        resources.append(deployment_obj)
        
        # Service (如果有端口)
        if dep['port']:
            service_obj = {
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': name,
                    'labels': {'app': name, 'project': project}
                },
                'spec': {
                    'selector': {'app': name},
                    'ports': [{
                        'port': dep['port'],
                        'targetPort': dep['port']
                    }],
                    'type': 'ClusterIP'
                }
            }
            resources.append(service_obj)
    
    # 合并为一个 YAML
    return '---\n'.join(yaml.dump(r, default_flow_style=False) for r in resources)


def validate_k8s_yaml(yaml_file: str) -> bool:
    """验证 K8s YAML 格式"""
    try:
        with open(yaml_file) as f:
            docs = list(yaml.safe_load_all(f))
        
        for doc in docs:
            if not doc:
                continue
            if 'apiVersion' not in doc or 'kind' not in doc:
                return False
        
        return True
    except:
        return False
