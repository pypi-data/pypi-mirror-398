#!/usr/bin/env python3
"""
单实例锁机制（基于数据库）
防止多个调度器实例同时运行（支持多机部署）
"""
import os
import sys
import time
import socket
from datetime import datetime, timedelta, UTC
from sqlalchemy import text

LOCK_NAME = "btp_scheduler_master"
LOCK_TIMEOUT = 30  # 锁超时时间（秒）

def get_instance_id():
    """获取实例标识"""
    hostname = socket.gethostname()
    pid = os.getpid()
    return f"{hostname}:{pid}"

def acquire_lock(engine):
    """获取单实例锁（数据库级别）"""
    instance_id = get_instance_id()
    
    try:
        with engine.begin() as conn:
            # 创建锁表（如果不存在）
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS scheduler_locks (
                    lock_name VARCHAR(100) PRIMARY KEY,
                    instance_id VARCHAR(200),
                    acquired_at TIMESTAMP,
                    heartbeat_at TIMESTAMP
                )
            """))
            
        # 尝试获取锁
        with engine.begin() as conn:
            now = datetime.now(UTC)
            timeout_threshold = now - timedelta(seconds=LOCK_TIMEOUT)
            
            # 清理过期锁
            conn.execute(text("""
                DELETE FROM scheduler_locks 
                WHERE lock_name = :lock_name 
                AND heartbeat_at < :threshold
            """), {"lock_name": LOCK_NAME, "threshold": timeout_threshold})
            
            # 尝试插入锁
            try:
                conn.execute(text("""
                    INSERT INTO scheduler_locks (lock_name, instance_id, acquired_at, heartbeat_at)
                    VALUES (:lock_name, :instance_id, :now, :now)
                """), {"lock_name": LOCK_NAME, "instance_id": instance_id, "now": now})
                print(f"✓ 获取调度器锁成功: {instance_id}")
                return True
            except:
                # 锁已被占用
                pass
        
        # 查询当前锁持有者
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT instance_id, heartbeat_at 
                FROM scheduler_locks 
                WHERE lock_name = :lock_name
            """), {"lock_name": LOCK_NAME})
            row = result.fetchone()
            if row:
                print(f"❌ 另一个调度器实例正在运行: {row[0]}")
                print(f"   最后心跳: {row[1]}")
        return False
                
    except Exception as e:
        print(f"❌ 获取锁失败: {e}")
        return False

def update_heartbeat(engine):
    """更新心跳时间"""
    instance_id = get_instance_id()
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE scheduler_locks 
                SET heartbeat_at = :now 
                WHERE lock_name = :lock_name AND instance_id = :instance_id
            """), {"now": datetime.now(UTC), "lock_name": LOCK_NAME, "instance_id": instance_id})
    except:
        pass

def release_lock(engine):
    """释放锁"""
    instance_id = get_instance_id()
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                DELETE FROM scheduler_locks 
                WHERE lock_name = :lock_name AND instance_id = :instance_id
            """), {"lock_name": LOCK_NAME, "instance_id": instance_id})
            print(f"✓ 释放调度器锁: {instance_id}")
    except:
        pass
