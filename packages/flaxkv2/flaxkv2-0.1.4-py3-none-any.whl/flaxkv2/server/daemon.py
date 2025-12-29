"""
FlaxKV2 守护进程服务器管理器

提供服务器的后台启动、状态检查、自动启动等功能。
解决多进程访问 LevelDB 的问题 - 一次启动，多处使用。

用法:
    from flaxkv2.server.daemon import DaemonServerManager

    # 确保服务器运行（如果未运行则启动）
    manager = DaemonServerManager("/tmp/flaxkv.sock", "./data")
    manager.ensure_running()

    # 现在可以安全地连接
    db = FlaxKV("mydb", "ipc:///tmp/flaxkv.sock")
"""

import os
import sys
import time
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import zmq

from flaxkv2.utils.log import get_logger

logger = get_logger(__name__)


class DaemonServerManager:
    """
    守护进程服务器管理器

    负责启动、停止、检查 FlaxKV 服务器的守护进程。
    支持 Unix Socket (IPC) 和 TCP 两种模式。
    """

    def __init__(
        self,
        socket_path: Optional[str] = None,
        data_dir: str = ".",
        host: str = "127.0.0.1",
        port: int = 5555,
        pid_file: Optional[str] = None,
        log_file: Optional[str] = None,
        enable_encryption: bool = False,
        password: Optional[str] = None,
    ):
        """
        初始化守护进程管理器

        Args:
            socket_path: Unix Socket 路径（IPC 模式，推荐）
            data_dir: 数据存储目录
            host: 服务器地址（TCP 模式）
            port: 服务器端口（TCP 模式）
            pid_file: PID 文件路径（默认自动生成）
            log_file: 日志文件路径（默认自动生成）
            enable_encryption: 启用加密
            password: 加密密码
        """
        self.socket_path = socket_path
        self.data_dir = os.path.abspath(data_dir)
        self.host = host
        self.port = port
        self.enable_encryption = enable_encryption
        self.password = password

        # 确定连接 URL
        if socket_path:
            self.url = f"ipc://{socket_path}"
            self.mode = "ipc"
        else:
            self.url = f"tcp://{host}:{port}"
            self.mode = "tcp"

        # PID 文件和日志文件路径
        if pid_file:
            self.pid_file = pid_file
        else:
            # 根据连接信息生成唯一的 PID 文件名
            if socket_path:
                safe_name = socket_path.replace("/", "_").replace(".", "_")
            else:
                safe_name = f"{host}_{port}"
            self.pid_file = os.path.join(tempfile.gettempdir(), f"flaxkv2_{safe_name}.pid")

        if log_file:
            self.log_file = log_file
        else:
            self.log_file = os.path.join(tempfile.gettempdir(), f"flaxkv2_{safe_name}.log")

    def is_running(self) -> bool:
        """
        检查服务器是否正在运行

        通过两种方式检查：
        1. PID 文件存在且进程存活
        2. 能够成功 ping 服务器
        """
        # 首先检查 PID 文件
        pid = self._read_pid()
        if pid and self._is_process_alive(pid):
            # 进程存活，尝试 ping 确认服务正常
            if self._ping_server():
                return True

        # PID 检查失败，直接尝试 ping
        return self._ping_server()

    def _read_pid(self) -> Optional[int]:
        """读取 PID 文件"""
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
        except (ValueError, IOError):
            pass
        return None

    def _write_pid(self, pid: int):
        """写入 PID 文件"""
        with open(self.pid_file, 'w') as f:
            f.write(str(pid))

    def _remove_pid(self):
        """删除 PID 文件"""
        try:
            if os.path.exists(self.pid_file):
                os.unlink(self.pid_file)
        except OSError:
            pass

    def _is_process_alive(self, pid: int) -> bool:
        """检查进程是否存活"""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def _ping_server(self, timeout: int = 1000) -> bool:
        """
        Ping 服务器检查是否响应

        Args:
            timeout: 超时时间（毫秒）
        """
        context = None
        socket = None
        try:
            context = zmq.Context()
            # 使用 DEALER socket（与服务器的 ROUTER 配合）
            # 注意：不能用 REQ socket，因为 REQ 会添加空分隔帧，
            # 而服务器期望的是 [identity, data] 格式
            socket = context.socket(zmq.DEALER)
            socket.setsockopt(zmq.LINGER, 0)
            socket.setsockopt(zmq.RCVTIMEO, timeout)
            socket.setsockopt(zmq.SNDTIMEO, timeout)

            # 如果启用加密，需要配置客户端
            if self.enable_encryption and self.password:
                from flaxkv2.utils.key_manager import get_keypair_from_password
                # 生成客户端密钥对
                client_public, client_secret = zmq.curve_keypair()
                # 获取服务器公钥
                keypair = get_keypair_from_password(self.password, derive_from_password=True)
                server_public = keypair['public_key']

                socket.curve_secretkey = client_secret
                socket.curve_publickey = client_public
                socket.curve_serverkey = server_public.encode('utf-8')

            socket.connect(self.url)

            # 发送 PING（格式与异步客户端一致）
            import msgpack
            # request_id=0, command=PING, db_name=空
            request = msgpack.packb([0, b'PING', b''], use_bin_type=True)
            socket.send(b'\x00' + request)  # 添加压缩标志

            # 接收响应
            response = socket.recv()
            # 响应格式：[压缩标志][msgpack([request_id, status, result])]
            if len(response) > 1:
                response_data = response[1:]  # 跳过压缩标志
                result = msgpack.unpackb(response_data, raw=True)
                # result = [request_id, status, result]
                if len(result) >= 2 and result[1] == b'OK':
                    return True
            return False

        except zmq.ZMQError:
            return False
        except Exception as e:
            logger.debug(f"Ping failed: {e}")
            return False
        finally:
            if socket:
                socket.close()
            if context:
                context.term()

    def start(self, wait: bool = True, timeout: float = 5.0) -> bool:
        """
        启动服务器守护进程

        Args:
            wait: 是否等待服务器就绪
            timeout: 等待超时时间（秒）

        Returns:
            True 如果启动成功
        """
        if self.is_running():
            logger.info(f"Server already running at {self.url}")
            return True

        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        # 构建启动命令
        cmd = [
            sys.executable, "-m", "flaxkv2.server.daemon_runner",
            "--data-dir", self.data_dir,
            "--pid-file", self.pid_file,
            "--log-file", self.log_file,
        ]

        if self.socket_path:
            cmd.extend(["--socket-path", self.socket_path])
        else:
            cmd.extend(["--host", self.host, "--port", str(self.port)])

        if self.enable_encryption:
            cmd.append("--enable-encryption")
            if self.password:
                cmd.extend(["--password", self.password])

        logger.info(f"Starting FlaxKV server daemon at {self.url}")
        logger.debug(f"Command: {' '.join(cmd)}")

        # 启动守护进程
        try:
            # 使用 subprocess 启动，脱离父进程
            with open(self.log_file, 'a') as log_f:
                process = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,  # 脱离父进程会话
                    close_fds=True,
                )

            # 记录 PID
            self._write_pid(process.pid)
            logger.info(f"Server daemon started with PID {process.pid}")

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

        # 等待服务器就绪
        if wait:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self._ping_server():
                    logger.info(f"Server is ready at {self.url}")
                    return True
                time.sleep(0.1)

            logger.warning(f"Server started but not responding within {timeout}s")
            return False

        return True

    def stop(self, timeout: float = 5.0) -> bool:
        """
        停止服务器守护进程

        Args:
            timeout: 等待进程退出的超时时间（秒）

        Returns:
            True 如果停止成功
        """
        pid = self._read_pid()
        if not pid:
            logger.info("No PID file found, server may not be running")
            return True

        if not self._is_process_alive(pid):
            logger.info("Server process not running")
            self._remove_pid()
            return True

        logger.info(f"Stopping server (PID {pid})...")

        try:
            # 发送 SIGTERM
            os.kill(pid, signal.SIGTERM)

            # 等待进程退出
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self._is_process_alive(pid):
                    logger.info("Server stopped gracefully")
                    self._remove_pid()
                    return True
                time.sleep(0.1)

            # 超时，强制 kill
            logger.warning(f"Server not responding to SIGTERM, sending SIGKILL")
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)

            self._remove_pid()
            return True

        except ProcessLookupError:
            logger.info("Server process already terminated")
            self._remove_pid()
            return True
        except Exception as e:
            logger.error(f"Failed to stop server: {e}")
            return False

    def ensure_running(self, timeout: float = 5.0) -> bool:
        """
        确保服务器正在运行（核心方法）

        如果服务器未运行，自动启动它。
        如果已运行，直接返回。

        Args:
            timeout: 启动超时时间（秒）

        Returns:
            True 如果服务器正在运行
        """
        if self.is_running():
            logger.debug(f"Server already running at {self.url}")
            return True

        return self.start(wait=True, timeout=timeout)

    def status(self) -> dict:
        """
        获取服务器状态

        Returns:
            状态信息字典
        """
        pid = self._read_pid()
        running = self.is_running()

        return {
            'running': running,
            'pid': pid if running else None,
            'url': self.url,
            'mode': self.mode,
            'data_dir': self.data_dir,
            'pid_file': self.pid_file,
            'log_file': self.log_file,
        }


def get_default_socket_path() -> str:
    """
    获取默认的 Unix Socket 路径

    Returns:
        ~/.flaxkv2/server.sock
    """
    user_dir = os.path.join(Path.home(), ".flaxkv2")
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "server.sock")


def get_default_data_dir() -> str:
    """获取默认的数据目录"""
    return os.path.join(Path.home(), ".flaxkv2", "data")


# 全局默认管理器（懒加载）
_default_manager: Optional[DaemonServerManager] = None


def get_default_manager() -> DaemonServerManager:
    """获取默认的守护进程管理器"""
    global _default_manager
    if _default_manager is None:
        _default_manager = DaemonServerManager(
            socket_path=get_default_socket_path(),
            data_dir=get_default_data_dir(),
        )
    return _default_manager


def ensure_server_running(
    socket_path: Optional[str] = None,
    data_dir: Optional[str] = None,
    **kwargs
) -> str:
    """
    便捷函数：确保服务器运行并返回连接 URL

    Args:
        socket_path: Unix Socket 路径（默认使用系统临时目录）
        data_dir: 数据目录（默认使用 ~/.flaxkv2/data）
        **kwargs: 其他参数传递给 DaemonServerManager

    Returns:
        服务器 URL (ipc://... 或 tcp://...)

    示例:
        url = ensure_server_running()
        db = FlaxKV("mydb", url)
    """
    if socket_path is None:
        socket_path = get_default_socket_path()
    if data_dir is None:
        data_dir = get_default_data_dir()

    manager = DaemonServerManager(
        socket_path=socket_path,
        data_dir=data_dir,
        **kwargs
    )

    if not manager.ensure_running():
        raise RuntimeError(f"Failed to start FlaxKV server at {manager.url}")

    return manager.url
