import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from scriptbook.core.script_executor import ScriptExecutor


class TestScriptExecutor:
    """测试脚本执行器"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.executor = ScriptExecutor()

    def test_initialization(self):
        """测试初始化"""
        assert self.executor._processes == {}
        assert self.executor._master_fds == {}
        assert self.executor._output_queues == {}

    def test_kill_process_no_process(self):
        """测试终止不存在的进程"""
        # 不应该抛出异常
        self.executor.kill_process("nonexistent")

    def test_kill_process_running(self):
        """测试终止运行中的进程"""
        script_id = "running_script"

        # 模拟一个运行中的进程
        mock_process = MagicMock()
        mock_process.returncode = None
        mock_process.terminate = MagicMock()

        self.executor._processes[script_id] = mock_process
        self.executor._master_fds[script_id] = 5  # 模拟 fd

        self.executor.kill_process(script_id)

        mock_process.terminate.assert_called_once()
        assert script_id not in self.executor._processes
        assert script_id not in self.executor._master_fds

    def test_kill_process_already_finished(self):
        """测试终止已完成的进程"""
        script_id = "finished_script"

        # 模拟已完成的进程
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.terminate = MagicMock()

        self.executor._processes[script_id] = mock_process

        self.executor.kill_process(script_id)

        # 不应该调用terminate，因为进程已结束
        mock_process.terminate.assert_not_called()
        assert script_id not in self.executor._processes

    @pytest.mark.asyncio
    async def test_wait_for_output(self):
        """测试 _wait_for_output 方法"""
        queue = asyncio.Queue()
        outputs = []

        async def put_outputs():
            await queue.put({"type": "stdout", "content": "1", "timestamp": "1"})
            await queue.put({"type": "stdout", "content": "2", "timestamp": "2"})
            await queue.put(None)  # 结束标记

        # 并发放入输出
        put_task = asyncio.create_task(put_outputs())

        async for output in self.executor._wait_for_output(queue):
            outputs.append(output)

        await put_task

        assert len(outputs) == 2
        assert outputs[0]["content"] == "1"
        assert outputs[1]["content"] == "2"

    def test_processes_dict_management(self):
        """测试进程字典管理"""
        # 添加进程
        mock_process1 = MagicMock()
        mock_process2 = MagicMock()

        self.executor._processes["p1"] = mock_process1
        self.executor._processes["p2"] = mock_process2

        assert len(self.executor._processes) == 2
        assert "p1" in self.executor._processes
        assert "p2" in self.executor._processes

        # 移除进程
        del self.executor._processes["p1"]
        assert "p1" not in self.executor._processes
        assert "p2" in self.executor._processes

        # 清空
        self.executor._processes.clear()
        assert len(self.executor._processes) == 0

    @pytest.mark.asyncio
    async def test_write_stdin(self):
        """测试 write_stdin 方法"""
        script_id = "test_stdin"
        mock_fd = 5

        self.executor._master_fds[script_id] = mock_fd

        with patch('os.write') as mock_write:
            mock_write.return_value = 5
            self.executor.write_stdin(script_id, "test input")
            mock_write.assert_called_once_with(mock_fd, b"test input")

    @pytest.mark.asyncio
    async def test_write_stdin_no_process(self):
        """测试 write_stdin 对于不存在的进程"""
        # 不应该抛出异常
        self.executor.write_stdin("nonexistent", "test input")
