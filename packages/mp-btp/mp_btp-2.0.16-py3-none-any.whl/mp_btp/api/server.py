import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import atexit

from mp_btp.config import get_settings, get_config
from models import Base, engine
from api.routes import health, accounts, deployments, kyma, maintenance
from mp_btp.tasks.scheduled import start_scheduler, stop_scheduler
from instance_lock import acquire_lock, release_lock, update_heartbeat

# Setup logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize schema and create tables
from mp_btp.models.database import init_schema
init_schema()
Base.metadata.create_all(bind=engine)

# 单实例检查（数据库锁）
if not acquire_lock(engine):
    logger.error("❌ 另一个调度器实例正在运行")
    logger.error("   如果确认没有其他实例，请等待 30 秒后重试")
    sys.exit(1)

# 注册退出时释放锁
atexit.register(lambda: release_lock(engine))

logger.info("✓ 调度器锁已获取")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

# Create app
app = FastAPI(title="BTP Scheduler", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router, prefix="/api/v1")
app.include_router(accounts.router, prefix="/api/v1")
app.include_router(deployments.router, prefix="/api/v1")
app.include_router(kyma.router, prefix="/api/v1")
app.include_router(maintenance.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "BTP Scheduler API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(
        "server:app",
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=True
    )
