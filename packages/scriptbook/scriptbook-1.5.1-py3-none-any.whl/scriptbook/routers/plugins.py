from fastapi import APIRouter, HTTPException, Request
from scriptbook.models.schemas import PluginInfo
import os
import json
from pathlib import Path

router = APIRouter(tags=["plugins"])


def get_plugins_dir(request: Request) -> Path:
    """从请求中获取插件目录"""
    return Path(request.app.state.plugins_dir)

@router.get("/", response_model=list[PluginInfo])
async def get_plugins(request: Request):
    """
    获取所有可用插件
    """
    plugins_dir = get_plugins_dir(request)
    plugins = []
    try:
        for plugin_name in plugins_dir.iterdir():
            if not plugin_name.is_dir():
                continue
            manifest_path = plugin_name / "manifest.json"

            if manifest_path.exists():
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)

                plugin_info = PluginInfo(
                    name=manifest.get("name", plugin_name.name),
                    version=manifest.get("version", "1.0.0"),
                    description=manifest.get("description", ""),
                    type=manifest.get("type", "theme"),
                    css=manifest.get("css"),
                    js=manifest.get("js"),
                    terminalTheme=manifest.get("terminalTheme")
                )
                plugins.append(plugin_info)

        return plugins
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取插件失败: {str(e)}")

@router.post("/{plugin_name}/activate")
async def activate_plugin(plugin_name: str):
    """
    激活指定插件
    """
    # 这里应该实现插件激活逻辑
    # 暂时只返回成功消息
    return {"message": f"插件 {plugin_name} 已激活", "active": True}

@router.get("/active")
async def get_active_plugins():
    """
    获取当前激活的插件
    """
    # 这里应该返回当前激活的插件列表
    # 暂时返回空列表
    return {"active_plugins": []}