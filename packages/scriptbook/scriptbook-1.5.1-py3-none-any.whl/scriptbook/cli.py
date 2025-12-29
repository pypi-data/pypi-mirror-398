"""
命令行入口
"""
import argparse
import sys
import uvicorn
import os
from pathlib import Path


def create_app(content_dir: Path):
    """创建FastAPI应用实例"""
    from scriptbook.main import create_app as _create_app

    # 设置环境变量传递content目录
    os.environ['CONTENT_DIR'] = str(content_dir)

    return _create_app()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Scriptbook - 可执行脚本的 Markdown 服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s content/                    # 使用content目录启动服务
  %(prog)s /path/to/sop/documents      # 使用指定SOP目录
  %(prog)s content/ --port 9000        # 指定端口
  %(prog)s content/ --host 0.0.0.0     # 指定主机（允许外部访问）

默认端口: 8000
默认主机: 127.0.0.1

功能特点:
  - 在Markdown中嵌入可执行脚本
  - 每个脚本块可独立执行
  - 实时输出展示
  - 类似Jupyter Notebook的交互体验
        """
    )

    parser.add_argument(
        'content_dir',
        type=str,
        help='Markdown文件目录路径'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='服务端口 (默认: 8000)'
    )

    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='服务主机 (默认: 127.0.0.1)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    args = parser.parse_args()

    # 验证content目录
    content_path = Path(args.content_dir)
    if not content_path.exists():
        print(f"错误: 目录 '{args.content_dir}' 不存在", file=sys.stderr)
        sys.exit(1)

    if not content_path.is_dir():
        print(f"错误: '{args.content_dir}' 不是一个目录", file=sys.stderr)
        sys.exit(1)

    # 创建应用
    try:
        app = create_app(content_path)
    except Exception as e:
        print(f"错误: 创建应用失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 启动服务
    print(f"启动 Scriptbook - 可执行脚本的 Markdown 服务器")
    print(f"文档目录: {content_path.absolute()}")
    print(f"服务地址: http://{args.host}:{args.port}")
    print(f"访问地址: http://localhost:{args.port}")
    print(f"按 Ctrl+C 停止服务\n")

    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"错误: 启动服务失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
