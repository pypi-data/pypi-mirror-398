"""
AutoCoder CLI SDK 进程管理器

提供进程管理功能，支持启动、监控和终止auto-coder.run进程。
"""

import asyncio
import subprocess
import threading
from typing import AsyncIterator, Callable, Iterator, Optional

import psutil

from .models import AutoCoderError


class ProcessManager:
    """进程管理器，负责管理auto-coder.run进程的生命周期"""

    def __init__(self):
        self._current_process: Optional[subprocess.Popen] = None
        self._is_running = False
        self._abort_requested = False
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """检查进程是否正在运行"""
        with self._lock:
            return self._is_running and self._current_process is not None

    @property
    def process_id(self) -> Optional[int]:
        """获取当前进程ID"""
        with self._lock:
            if self._current_process:
                return self._current_process.pid
            return None

    def start_process(
        self,
        cmd: list,
        input_data: str = "",
        cwd: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> subprocess.Popen:
        """
        启动进程

        Args:
            cmd: 命令参数列表
            input_data: 输入数据
            cwd: 工作目录
            timeout: 超时时间（秒）

        Returns:
            subprocess.Popen对象

        Raises:
            AutoCoderError: 当进程启动失败时
        """
        with self._lock:
            if self._is_running:
                # 尝试清理已完成的进程
                if (
                    self._current_process
                    and self._current_process.poll() is not None
                ):
                    self._is_running = False
                    self._current_process = None
                else:
                    raise AutoCoderError("进程已在运行中，请先停止当前进程")

            try:
                self._abort_requested = False
                self._current_process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=cwd,
                    bufsize=1,  # 行缓冲
                )
                self._is_running = True

                # 发送输入数据（如果有）
                if input_data:
                    self._current_process.stdin.write(input_data)
                    self._current_process.stdin.close()

                return self._current_process

            except Exception as e:
                self._is_running = False
                self._current_process = None
                raise AutoCoderError(f"启动进程失败: {str(e)}")

    def abort(self, force: bool = False) -> bool:
        """
        终止当前进程

        Args:
            force: 是否强制终止（使用SIGKILL）

        Returns:
            是否成功终止
        """
        with self._lock:
            if not self._is_running or not self._current_process:
                return True

            self._abort_requested = True

            try:
                # 首先尝试优雅关闭
                if not force:
                    self._current_process.terminate()
                    # 等待进程结束
                    try:
                        self._current_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # 如果5秒内没有结束，强制kill
                        force = True

                # 强制终止
                if force:
                    self._current_process.kill()
                    self._current_process.wait(timeout=2)

                # 清理状态
                self._is_running = False
                self._current_process = None
                return True

            except Exception:
                # 尝试使用psutil强制终止
                try:
                    if self._current_process and self._current_process.pid:
                        psutil.Process(self._current_process.pid).terminate()
                except Exception:
                    pass

                self._is_running = False
                self._current_process = None
                return False

    def wait_for_completion(
        self, timeout: Optional[float] = None
    ) -> Optional[int]:
        """
        等待进程完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            进程退出码，如果超时则返回None
        """
        with self._lock:
            if not self._current_process:
                return None

            process = self._current_process

        try:
            exit_code = process.wait(timeout=timeout)
            with self._lock:
                self._is_running = False
                self._current_process = None
            return exit_code
        except subprocess.TimeoutExpired:
            return None

    def read_output_sync(
        self,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
    ) -> tuple[str, str]:
        """
        同步读取进程输出

        Args:
            on_stdout: 标准输出回调函数
            on_stderr: 标准错误回调函数

        Returns:
            (stdout, stderr) 元组
        """
        if not self._current_process:
            return "", ""

        stdout_lines = []
        stderr_lines = []

        def read_stdout():
            try:
                for line in iter(self._current_process.stdout.readline, ""):
                    if self._abort_requested:
                        break
                    stdout_lines.append(line)
                    if on_stdout:
                        on_stdout(line.rstrip("\n"))
            except Exception:
                pass

        def read_stderr():
            try:
                for line in iter(self._current_process.stderr.readline, ""):
                    if self._abort_requested:
                        break
                    stderr_lines.append(line)
                    if on_stderr:
                        on_stderr(line.rstrip("\n"))
            except Exception:
                pass

        # 启动读取线程
        stdout_thread = threading.Thread(target=read_stdout)
        stderr_thread = threading.Thread(target=read_stderr)

        stdout_thread.start()
        stderr_thread.start()

        # 等待进程完成
        self.wait_for_completion()

        # 等待读取线程完成
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)

        return "".join(stdout_lines), "".join(stderr_lines)

    def stream_output_sync(self) -> Iterator[str]:
        """
        同步流式读取进程输出

        Yields:
            输出行
        """
        if not self._current_process:
            return

        try:
            for line in iter(self._current_process.stdout.readline, ""):
                if self._abort_requested:
                    break
                yield line.rstrip("\n")
        except Exception:
            pass
        finally:
            self.wait_for_completion()


class AsyncProcessManager:
    """异步进程管理器"""

    def __init__(self):
        self._current_process: Optional[asyncio.subprocess.Process] = None
        self._is_running = False
        self._abort_requested = False
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        """检查进程是否正在运行"""
        return self._is_running and self._current_process is not None

    @property
    def process_id(self) -> Optional[int]:
        """获取当前进程ID"""
        if self._current_process:
            return self._current_process.pid
        return None

    async def start_process(
        self, cmd: list, input_data: str = "", cwd: Optional[str] = None
    ) -> asyncio.subprocess.Process:
        """
        启动异步进程

        Args:
            cmd: 命令参数列表
            input_data: 输入数据
            cwd: 工作目录

        Returns:
            asyncio.subprocess.Process对象

        Raises:
            AutoCoderError: 当进程启动失败时
        """
        async with self._lock:
            if self._is_running:
                raise AutoCoderError("进程已在运行中，请先停止当前进程")

            try:
                self._abort_requested = False
                self._current_process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )
                self._is_running = True

                # 发送输入数据（如果有）
                if input_data:
                    self._current_process.stdin.write(
                        input_data.encode("utf-8")
                    )
                    await self._current_process.stdin.drain()
                    self._current_process.stdin.close()
                    await self._current_process.stdin.wait_closed()

                return self._current_process

            except Exception as e:
                self._is_running = False
                self._current_process = None
                raise AutoCoderError(f"启动异步进程失败: {str(e)}")

    async def abort(self, force: bool = False) -> bool:
        """
        终止当前进程

        Args:
            force: 是否强制终止

        Returns:
            是否成功终止
        """
        async with self._lock:
            if not self._is_running or not self._current_process:
                return True

            self._abort_requested = True

            try:
                # 首先尝试优雅关闭
                if not force:
                    self._current_process.terminate()
                    try:
                        await asyncio.wait_for(
                            self._current_process.wait(), timeout=5
                        )
                    except asyncio.TimeoutError:
                        force = True

                # 强制终止
                if force:
                    self._current_process.kill()
                    await asyncio.wait_for(
                        self._current_process.wait(), timeout=2
                    )

                # 清理状态
                self._is_running = False
                self._current_process = None
                return True

            except Exception:
                self._is_running = False
                self._current_process = None
                return False

    async def wait_for_completion(
        self, timeout: Optional[float] = None
    ) -> Optional[int]:
        """
        等待进程完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            进程退出码，如果超时则返回None
        """
        if not self._current_process:
            return None

        try:
            if timeout:
                exit_code = await asyncio.wait_for(
                    self._current_process.wait(), timeout=timeout
                )
            else:
                exit_code = await self._current_process.wait()

            async with self._lock:
                self._is_running = False
                self._current_process = None
            return exit_code
        except asyncio.TimeoutError:
            return None

    async def stream_output_async(self) -> AsyncIterator[str]:
        """
        异步流式读取进程输出

        Yields:
            输出行
        """
        if not self._current_process:
            return

        try:
            while True:
                if self._abort_requested:
                    break

                line = await self._current_process.stdout.readline()
                if not line:
                    break

                yield line.decode("utf-8").rstrip("\n")
        except Exception:
            pass
        finally:
            await self.wait_for_completion()
