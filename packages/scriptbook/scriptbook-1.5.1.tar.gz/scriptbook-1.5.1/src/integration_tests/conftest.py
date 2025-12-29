"""
集成测试公共配置和fixture

提供服务器管理和其他公共工具
"""
import subprocess
import time
import os
import signal
import atexit
import pytest
from pathlib import Path


def cleanup_processes():
    """清理所有可能的残留进程"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "scriptbook"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"  🧹 已清理残留进程 PID: {pid}")
                except (OSError, ValueError):
                    pass
    except Exception:
        pass


# 注册退出时清理
atexit.register(cleanup_processes)


class TestServer:
    """测试服务器管理器"""

    def __init__(self, content_dir: str, port: int = 8000):
        # 使用相对于项目根目录的路径
        base_path = Path(__file__).parent.parent.parent
        self.content_dir = str((base_path / content_dir).resolve())
        self.port = port
        self.process = None
        self.base_url = f"http://127.0.0.1:{port}"

    def start(self):
        """启动服务器"""
        print(f"\n🚀 启动服务器 (端口: {self.port})...")

        # 启动前清理端口占用
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{self.port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        print(f"  🧹 已清理端口 {self.port} 上的进程 PID: {pid}")
                        time.sleep(0.2)
                    except (OSError, ValueError):
                        pass
        except Exception:
            pass

        # 获取scriptbook命令路径
        venv_path = Path(__file__).parent.parent.parent / ".venv" / "bin" / "scriptbook"
        scriptbook_cmd = str(venv_path)

        cmd = [
            scriptbook_cmd,
            self.content_dir,
            "--port", str(self.port),
            "--host", "127.0.0.1"
        ]

        print(f"  命令: {' '.join(cmd)}")

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "PATH": f"{Path(scriptbook_cmd).parent}:{os.environ.get('PATH', '')}"}
        )

        print(f"  进程已启动 PID: {self.process.pid}")
        time.sleep(0.5)  # 等待一下让进程启动

        # 检查进程是否立即退出
        if self.process.poll() is not None:
            stdout, stderr = self.process.communicate()
            print(f"  ❌ 进程立即退出")
            if stdout:
                print(f"  STDOUT: {stdout}")
            if stderr:
                print(f"  STDERR: {stderr}")
            return False

        print(f"  ✅ 进程正常运行")

        # 注册退出时清理
        atexit.register(self._safe_kill)

        # 等待服务器启动
        max_attempts = 30
        for i in range(max_attempts):
            try:
                import urllib.request
                response = urllib.request.urlopen(f"{self.base_url}/health", timeout=1)
                if response.status == 200:
                    print(f"✅ 服务器启动成功 (尝试 {i+1}/{max_attempts})")
                    return True
            except Exception as e:
                if i == 0:
                    print(f"    首次连接失败，正在重试...")
                time.sleep(0.5)

        print(f"❌ 服务器启动失败")
        self.stop()
        return False

    def _safe_kill(self):
        """安全杀死进程"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass

    def stop(self):
        """停止服务器"""
        if self.process:
            print(f"\n🛑 停止服务器...")
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                print(f"✅ 服务器已停止")
            except subprocess.TimeoutExpired:
                try:
                    self.process.kill()
                    self.process.wait(timeout=2)
                    print(f"✅ 服务器已强制停止")
                except:
                    pass
            finally:
                self.process = None


@pytest.fixture(scope="session")
def test_server():
    """会话级fixture，管理测试服务器生命周期"""
    server = TestServer("content", port=8015)

    # 启动服务器
    if not server.start():
        pytest.fail("无法启动测试服务器")

    yield server

    # 清理：停止服务器
    server.stop()


@pytest.fixture(scope="session")
def test_server_8016():
    """会话级fixture，管理测试服务器生命周期（端口8016）"""
    server = TestServer("content", port=8016)

    # 启动服务器
    if not server.start():
        pytest.fail("无法启动测试服务器")

    yield server

    # 清理：停止服务器
    server.stop()
