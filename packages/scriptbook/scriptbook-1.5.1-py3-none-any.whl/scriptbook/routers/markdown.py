from fastapi import APIRouter, HTTPException, Request
from scriptbook.models.schemas import FileListResponse, MarkdownContentResponse
import os
import re
import markdown as md_lib
from pathlib import Path
import html

router = APIRouter(tags=["markdown"])


def get_content_dir(request: Request) -> Path:
    """从请求中获取content目录"""
    return Path(request.app.state.content_dir)


def extract_script_blocks(content: str):
    """
    提取 markdown 中的脚本块
    返回脚本块列表，包含在原文中的位置
    """
    # 支持可选的缩进（用于列表中的代码块）
    # 使用负向前瞻确保不会匹配到代码内容中的 ```
    script_pattern = re.compile(
        r'^[ \t]*```(bash|sh|shell)\s*(\{[^}]*\})?\s*\n((?:(?!```).)*)[ \t]*\n[ \t]*```',
        re.MULTILINE | re.DOTALL
    )

    scripts = []
    for match in script_pattern.finditer(content):
        language = match.group(1) or 'unknown'
        metadata_str = match.group(2) or '{}'
        code = match.group(3).strip()

        # 只处理 bash/sh/shell 脚本
        if language not in ['bash', 'sh', 'shell']:
            continue

        # 解析元数据
        import json
        try:
            metadata = json.loads(metadata_str)
        except:
            metadata = {}

        script_id = metadata.get('id', f'script_{len(scripts)}')
        title = metadata.get('title', f'{language}脚本')

        scripts.append({
            'id': script_id,
            'title': title,
            'language': language,
            'code': code,
            'start': match.start(),
            'end': match.end(),
            'full_match': match.group(0)
        })

    return scripts


def render_script_block(script):
    """
    渲染单个脚本块为 HTML（嵌入版）
    """
    # 转义所有动态内容以防止XSS和HTML解析错误
    script_id = html.escape(script['id'], quote=True)
    script_title = html.escape(script['title'], quote=True)
    script_language = html.escape(script['language'], quote=True)
    script_code = html.escape(script['code'], quote=False)

    html_content = f'''
    <div class="script-block" data-script-id="{script_id}">
        <div class="script-header">
            <div class="script-info">
                <span class="script-title">{script_title}</span>
                <span class="script-language">{script_language}</span>
            </div>
            <div class="script-actions">
                <button class="execute-btn" onclick="executeScript('{script_id}')">执行脚本</button>
                <button class="copy-btn" onclick="copyCode('{script_id}')">复制代码</button>
                <button class="stop-btn" disabled>停止执行</button>
            </div>
        </div>
        <pre class="script-code"><code>{script_code}</code></pre>
        <div class="script-output" id="output-{script_id}">
            <div class="output-placeholder">点击"执行脚本"查看输出...</div>
        </div>
        <div class="script-input-container" id="input-container-{script_id}" style="display: none;">
            <div class="input-label">输入:</div>
            <input type="text" class="script-input" id="input-{script_id}" placeholder="输入命令所需内容，按Enter发送">
            <button class="input-send-btn" onclick="sendInput('{script_id}')">发送</button>
        </div>
    </div>
    '''
    return html_content


def embed_scripts_in_markdown(content: str, scripts: list):
    """
    将脚本块嵌入到markdown内容中
    """
    if not scripts:
        # 没有脚本块，直接渲染markdown
        html = md_lib.markdown(content, extensions=['fenced_code', 'tables', 'toc'])
        return html

    # 按位置从后往前替换，避免位置偏移
    scripts_sorted = sorted(scripts, key=lambda x: x['start'], reverse=True)

    # 先将脚本块替换为特殊标记，避免被markdown处理
    modified_content = content
    placeholders = {}

    # 从后往前替换，收集脚本块HTML
    for i, script in enumerate(scripts_sorted):
        script_html = render_script_block(script)
        # 使用不会被markdown处理的占位符格式（使用双方括号避免被解释）
        placeholder = f"[[SCRIPT_BLOCK_{i}]]"
        placeholders[placeholder] = script_html

        modified_content = (
            modified_content[:script['start']] +
            placeholder +
            modified_content[script['end']:]
        )

    # 渲染markdown
    html = md_lib.markdown(
        modified_content,
        extensions=['fenced_code', 'tables', 'toc']
    )

    # 将占位符替换回脚本块HTML
    for placeholder, script_html in placeholders.items():
        html = html.replace(placeholder, script_html)

    return html


@router.get("/files", response_model=FileListResponse)
async def get_markdown_files(request: Request):
    """
    获取content目录下的所有markdown文件列表
    """
    try:
        content_dir = get_content_dir(request)
        files = []
        for item in content_dir.iterdir():
            if item.name.endswith(".md"):
                stat = item.stat()
                files.append({
                    "name": item.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })

        return FileListResponse(files=files, directory=str(content_dir))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件列表失败: {str(e)}")


@router.get("/content", response_model=MarkdownContentResponse)
async def get_markdown_content(file: str, request: Request):
    """
    获取指定markdown文件的内容
    """
    try:
        # 安全检查：确保文件在content目录内
        if not file.endswith(".md"):
            raise HTTPException(status_code=400, detail="文件必须是markdown文件 (.md)")

        content_dir = get_content_dir(request)
        filepath = content_dir / file
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return MarkdownContentResponse(content=content, file=file)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@router.get("/render")
async def render_markdown(file: str, request: Request):
    """
    渲染markdown文件为完整的HTML（脚本块嵌入到markdown中）
    """
    try:
        # 安全检查
        if not file.endswith(".md"):
            raise HTTPException(status_code=400, detail="文件必须是markdown文件")

        content_dir = get_content_dir(request)
        filepath = content_dir / file
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取脚本块
        scripts = extract_script_blocks(content)

        # 将脚本块嵌入到markdown中并渲染
        final_html = embed_scripts_in_markdown(content, scripts)

        return {"html": final_html, "scripts": scripts, "file": file}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"渲染文件失败: {str(e)}")
