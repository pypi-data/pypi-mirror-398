"""
FastAPI应用入口
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os

from scriptbook import __version__


def create_app(content_dir: Path = None) -> FastAPI:
    """
    创建FastAPI应用实例

    Args:
        content_dir: Markdown文件目录，如果为None则使用环境变量CONTENT_DIR或默认content目录

    Returns:
        FastAPI应用实例
    """
    # 确定content目录
    if content_dir is None:
        content_dir = os.environ.get('CONTENT_DIR', 'content')
    content_dir = Path(content_dir)

    # 创建FastAPI应用
    app = FastAPI(
        title="Scriptbook - 可执行脚本的 Markdown 服务器",
        description="支持脚本执行的在线 Markdown 服务器，可用于SOP自动化和交互式文档",
        version=__version__
    )

    # 设置content目录到应用状态
    app.state.content_dir = str(content_dir)

    # 设置插件目录到应用状态
    # 优先使用环境变量，否则使用相对于当前模块目录的路径
    base_dir = Path(__file__).parent
    plugins_dir = base_dir / "static" / "plugins"
    app.state.plugins_dir = str(plugins_dir)

    # 导入路由
    from scriptbook.routers import markdown, scripts, plugins

    # 包含路由
    app.include_router(markdown.router, prefix="/api/markdown")
    app.include_router(scripts.router, prefix="/api")
    app.include_router(plugins.router, prefix="/api/plugins")

    # 静态文件目录
    static_dir = base_dir / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # 根路由 - 返回主页面
    @app.get("/")
    async def read_root():
        return FileResponse(str(static_dir / "index.html"))

    # 健康检查端点
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": "scriptbook",
            "version": __version__,
            "description": "Scriptbook - 可执行脚本的 Markdown 服务器"
        }

    return app

