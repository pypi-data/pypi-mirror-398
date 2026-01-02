"""
Android View Scope Backend
FastAPI服务主入口
"""

import os
import sys

# 确保当前目录在路径中
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

# 使用绝对导入
from core.device_manager import DeviceManager
from core.ui_analyzer import UIAnalyzer
from core.code_generator import CodeGenerator
from api.devices import router as devices_router
from api.screenshot import router as screenshot_router
from api.ui_hierarchy import router as ui_router
from api.element import router as element_router
from api.code import router as code_router
from api.device_actions import router as device_actions_router
from api.recorder import router as recorder_router

# 全局实例
device_manager = DeviceManager()
ui_analyzer = UIAnalyzer(device_manager)
code_generator = CodeGenerator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await device_manager.initialize()
    yield
    await device_manager.cleanup()

# 创建FastAPI应用
app = FastAPI(
    title="Android View Scope API",
    description="Android UI元素检查器后端服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:8060"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(devices_router, prefix="/api", tags=["设备管理"])
app.include_router(screenshot_router, prefix="/api", tags=["屏幕截图"])
app.include_router(ui_router, prefix="/api", tags=["UI层次"])
app.include_router(element_router, prefix="/api", tags=["元素操作"])
app.include_router(code_router, prefix="/api", tags=["代码生成"])
app.include_router(device_actions_router, prefix="/api", tags=["设备操作"])
app.include_router(recorder_router, prefix="/api", tags=["操作录制"])

# 静态文件服务
from pathlib import Path

# 查找静态文件目录
static_paths = [
    Path("static"),  # 当前目录 (backend/static)
    Path(__file__).parent.parent / "viewscope" / "static",  # 打包后的位置
    Path("../viewscope/static"),  # 相对位置
]

static_dir = None
for path in static_paths:
    if path.exists():
        static_dir = path
        break

if static_dir:
    # 挂载静态文件
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # 服务前端应用的主页面
    @app.get("/app")
    async def serve_app():
        """服务前端应用主页"""
        from fastapi.responses import FileResponse
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"error": "Frontend not available"}

    # 根路径直接服务前端应用
    @app.get("/")
    async def root():
        """根路径服务前端应用"""
        from fastapi.responses import FileResponse
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"error": "Frontend not available"}

else:
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "Android View Scope API",
            "version": "1.0.0",
            "status": "running"
        }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "devices_count": len(device_manager.get_all_devices()),
        "timestamp": device_manager.get_timestamp()
    }

@app.get("/api/routes")
async def list_routes():
    """列出所有注册的路由（调试用）"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
    return routes

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='ViewScope Backend Server')
    parser.add_argument('--port', type=int, default=8060, help='Port to run the server on')
    args = parser.parse_args()

    port = args.port

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=False
    )
