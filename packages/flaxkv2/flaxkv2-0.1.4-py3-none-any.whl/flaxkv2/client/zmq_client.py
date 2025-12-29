"""
FlaxKV2 ZeroMQ 客户端
高性能的远程数据库客户端实现

设计理念：
- 同步包装器 (RemoteDBDict) 内部使用异步客户端 (AsyncRemoteDBDict)
- 只维护一套核心代码（异步实现），同步接口通过包装器提供
- 保持向后兼容性
"""

import asyncio
import time
import threading
from typing import Any, Dict, List, Tuple, Optional

from flaxkv2.client.async_zmq_client import AsyncRemoteDBDict
from flaxkv2.utils.log import get_logger
from flaxkv2.auto_close import db_close_manager
from flaxkv2.display import DisplayMixin

logger = get_logger(__name__)


class RemoteDBDict(DisplayMixin):
    """
    同步远程数据库客户端（AsyncRemoteDBDict 的包装器）

    设计：
    - 内部使用 AsyncRemoteDBDict（异步实现）
    - 通过事件循环提供同步接口
    - 保持向后兼容性

    提供与本地数据库相同的字典接口，但数据存储在远程服务器

    支持两种连接模式：
    - TCP: tcp://host:port 或 host:port
    - Unix Socket (IPC): ipc:///path/to/socket
    """

    def __init__(
        self,
        db_name: str,
        host: str = "127.0.0.1",
        port: int = 5555,
        timeout: int = 5000,  # 毫秒
        connect_timeout: int = 5000,  # 毫秒
        max_retries: int = 3,
        retry_delay: float = 0.1,  # 秒
        read_cache_size: int = 0,  # 读缓存大小（已废弃，保留用于兼容性）
        enable_encryption: bool = False,  # 启用CurveZMQ加密
        server_public_key: Optional[str] = None,  # 服务器公钥（Z85编码）
        password: Optional[str] = None,  # 密码（自动管理密钥）
        derive_from_password: bool = True,  # 从密码派生密钥
        enable_compression: bool = False,  # 启用LZ4压缩（已废弃，保留用于兼容性）
        # 写缓冲参数（已废弃，保留用于兼容性）
        enable_write_buffer: bool = False,
        write_buffer_size: int = 100,
        write_buffer_flush_interval: int = 60,
        # 新增：直接传入 URL（优先于 host/port）
        url: Optional[str] = None,
    ):
        """
        初始化远程数据库客户端（同步包装器）

        Args:
            db_name: 数据库名称
            host: 服务器地址（TCP 模式）
            port: 服务器端口（TCP 模式）
            timeout: 数据请求超时时间（毫秒，0表示无限制）
            connect_timeout: 连接超时时间（毫秒）
            max_retries: 最大重试次数（已废弃，保留用于兼容性）
            retry_delay: 重试延迟（已废弃，保留用于兼容性）
            read_cache_size: 读缓存大小（已废弃，保留用于兼容性）
            enable_encryption: 启用CurveZMQ加密（默认False）
            server_public_key: 服务器公钥（Z85编码），与password二选一
            password: 密码（用于密钥管理），与server_public_key二选一
            derive_from_password: True=从密码直接派生密钥(推荐)，False=使用文件存储
            enable_compression: 启用LZ4压缩（已废弃，保留用于兼容性）
            enable_write_buffer: 是否启用写缓冲（已废弃，保留用于兼容性）
            write_buffer_size: 写缓冲区大小（已废弃，保留用于兼容性）
            write_buffer_flush_interval: 写缓冲刷新间隔（已废弃，保留用于兼容性）
            url: 完整的连接 URL（优先于 host/port）
                - TCP: "tcp://host:port"
                - Unix Socket: "ipc:///path/to/socket"

        注意：
            - 缓存和写缓冲功能已移除（简化设计）
            - 若需要缓存，请直接使用 AsyncRemoteDBDict
        """
        self.name = db_name
        self.db_name = db_name

        # 确定连接 URL
        if url:
            self.url = url
            self.db_path = f"{url}/{db_name}"
            # 解析 URL 以获取 host/port（用于显示）
            if url.startswith("ipc://"):
                self.host = url  # IPC 模式，host 保存完整 URL
                self.port = 0
            else:
                # TCP 模式，解析 host:port
                clean_url = url[6:] if url.startswith("tcp://") else url
                if ':' in clean_url:
                    self.host, port_str = clean_url.rsplit(':', 1)
                    try:
                        self.port = int(port_str)
                    except ValueError:
                        self.host = clean_url
                        self.port = 5555
                else:
                    self.host = clean_url
                    self.port = 5555
        else:
            self.url = f"tcp://{host}:{port}"
            self.db_path = f"tcp://{host}:{port}/{db_name}"
            self.host = host
            self.port = port

        self._closed = False

        # 创建后台事件循环线程
        self._loop = None
        self._loop_thread = None
        self._async_client = None

        # 启动后台事件循环
        self._start_event_loop(
            db_name=db_name,
            url=self.url,
            timeout=timeout,
            connect_timeout=connect_timeout,
            enable_encryption=enable_encryption,
            password=password,
            server_public_key=server_public_key,
            derive_from_password=derive_from_password
        )

        logger.info(f"RemoteDBDict (sync wrapper) connected to {self.url}, db={db_name}")
        logger.info(f"  Encryption: {'Enabled' if enable_encryption else 'Disabled'}")

        # 注册到自动关闭管理器（程序退出时自动清理）
        db_close_manager.register(self)
        logger.debug(f"远程数据库实例已注册到自动关闭管理器: {self.db_path}")

    def _start_event_loop(self, **kwargs):
        """启动后台事件循环线程"""
        # 用于同步启动状态
        self._ready_event = threading.Event()
        self._startup_error = None

        def run_loop():
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._loop = loop

                # 在事件循环中创建并连接异步客户端
                self._async_client = AsyncRemoteDBDict(
                    db_name=kwargs['db_name'],
                    url=kwargs['url'],
                    timeout=kwargs['timeout'],
                    connect_timeout=kwargs['connect_timeout'],
                    enable_encryption=kwargs['enable_encryption'],
                    password=kwargs['password'],
                    server_public_key=kwargs['server_public_key'],
                    derive_from_password=kwargs['derive_from_password']
                )

                # 连接到服务器
                loop.run_until_complete(self._async_client.connect())

                # 通知主线程已准备好
                self._ready_event.set()

                # 运行事件循环直到被停止
                loop.run_forever()

                # 清理：关闭异步客户端
                if self._async_client and not self._async_client._closed:
                    loop.run_until_complete(self._async_client.close())

                # 取消所有待处理的任务
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

                loop.close()
            except Exception as e:
                self._startup_error = e
                self._ready_event.set()  # 通知主线程（即使失败）

        # 启动后台线程
        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()

        # 等待事件循环启动（最多5秒）
        if not self._ready_event.wait(timeout=5.0):
            raise RuntimeError("Failed to start event loop: timeout")

        # 检查启动是否有错误
        if self._startup_error:
            raise RuntimeError(f"Failed to start event loop: {self._startup_error}")

    def _run_async(self, coro):
        """在后台事件循环中运行异步协程（线程安全）"""
        if self._closed:
            raise RuntimeError("Client is closed")

        # 使用 asyncio.run_coroutine_threadsafe 在后台循环中运行协程
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def __getitem__(self, key: Any) -> Any:
        """获取键值"""
        return self._run_async(self._async_client.get(key))

    def __setitem__(self, key: Any, value: Any):
        """设置键值（无TTL）"""
        self._run_async(self._async_client.set(key, value))

    def __delitem__(self, key: Any):
        """删除键"""
        self._run_async(self._async_client.delete(key))

    def __contains__(self, key: Any) -> bool:
        """检查键是否存在（单次请求，高效）"""
        return self._run_async(self._async_client.contains(key))

    def __len__(self) -> int:
        """返回数据库大小（单次请求，高效）"""
        return self._run_async(self._async_client.length())

    def get(self, key: Any, default: Any = None) -> Any:
        """获取键值，不存在返回默认值"""
        try:
            return self[key]
        except KeyError:
            return default

    def set(self, key: Any, value: Any, ttl: Optional[int] = None):
        """设置键值（支持指定TTL）"""
        self._run_async(self._async_client.set(key, value, ttl))

    def keys(self) -> List[Any]:
        """获取所有键"""
        return self._run_async(self._async_client.keys())

    def values(self, batch_size: int = 1000):
        """
        返回值的迭代器（分批获取，内存友好）

        Args:
            batch_size: 每批获取的数量

        Returns:
            迭代器，逐个返回值
        """
        return RemoteValuesIterator(self, batch_size)

    def items(self, batch_size: int = 1000):
        """
        返回键值对的迭代器（分批获取，内存友好）

        Args:
            batch_size: 每批获取的数量

        Returns:
            迭代器，逐个返回 (key, value) 元组
        """
        return RemoteItemsIterator(self, batch_size)

    def update(self, d: Dict[Any, Any]):
        """批量更新（单次请求，高效）"""
        self._run_async(self._async_client.update(d))

    # ========== SCAN 分页方法 ==========

    def scan_keys(self, start_key: Any = None, limit: int = 1000) -> Tuple[List[Any], Any]:
        """
        分页获取键

        Args:
            start_key: 起始键（None 表示从头开始）
            limit: 每批返回的数量

        Returns:
            (keys, next_key): keys 是本批的键列表，next_key 是下一批的起始键
        """
        return self._run_async(self._async_client.scan_keys(start_key, limit))

    def scan_values(self, start_key: Any = None, limit: int = 1000) -> Tuple[List[Any], Any]:
        """
        分页获取值

        Args:
            start_key: 起始键（None 表示从头开始）
            limit: 每批返回的数量

        Returns:
            (values, next_key): values 是本批的值列表，next_key 是下一批的起始键
        """
        return self._run_async(self._async_client.scan_values(start_key, limit))

    def scan_items(self, start_key: Any = None, limit: int = 1000) -> Tuple[List[Tuple[Any, Any]], Any]:
        """
        分页获取键值对

        Args:
            start_key: 起始键（None 表示从头开始）
            limit: 每批返回的数量

        Returns:
            (items, next_key): items 是本批的 (key, value) 列表，next_key 是下一批的起始键
        """
        return self._run_async(self._async_client.scan_items(start_key, limit))

    def iter_keys(self, batch_size: int = 1000):
        """
        迭代所有键（分批获取，内存友好）

        Args:
            batch_size: 每批获取的数量

        Returns:
            迭代器，逐个返回键
        """
        return RemoteKeysIterator(self, batch_size)

    def iter_values(self, batch_size: int = 1000):
        """
        迭代所有值（分批获取，内存友好）

        Args:
            batch_size: 每批获取的数量

        Returns:
            迭代器，逐个返回值
        """
        return RemoteValuesIterator(self, batch_size)

    def iter_items(self, batch_size: int = 1000):
        """
        迭代所有键值对（分批获取，内存友好）

        Args:
            batch_size: 每批获取的数量

        Returns:
            迭代器，逐个返回 (key, value) 元组
        """
        return RemoteItemsIterator(self, batch_size)

    def pop(self, key: Any, default: Any = None) -> Any:
        """弹出键值对"""
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            return default

    def batch_set(self, items: Dict[Any, Any], ttl: Optional[int] = None):
        """批量设置多个键值对（使用 WriteBatch）"""
        self._run_async(self._async_client.batch_set(items, ttl))

    def ping(self) -> bool:
        """测试连接"""
        return self._run_async(self._async_client.ping())

    def to_dict(self) -> Dict[Any, Any]:
        """转换为普通字典"""
        result = {}
        for k, v in self.items():
            result[k] = v
        return result

    def flush(self):
        """手动刷新缓存（兼容性方法，无实际作用）"""
        pass  # 异步客户端无缓存，保留此方法仅用于兼容性

    def close(self):
        """关闭连接"""
        if self._closed:
            return

        self._closed = True

        # 先在事件循环中关闭异步客户端
        if self._loop and self._loop.is_running() and self._async_client:
            try:
                # 使用 run_coroutine_threadsafe 确保异步客户端正确关闭
                future = asyncio.run_coroutine_threadsafe(
                    self._async_client.close(), self._loop
                )
                # 等待关闭完成（最多3秒）
                future.result(timeout=3.0)
            except Exception as e:
                logger.warning(f"Error closing async client: {e}")

        # 停止事件循环
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        # 等待线程结束（最多5秒，确保有足够时间清理）
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5.0)
            if self._loop_thread.is_alive():
                logger.warning("Event loop thread did not exit cleanly")

        # 从自动关闭管理器中移除
        db_close_manager.unregister(self)
        logger.debug(f"远程数据库实例已从自动关闭管理器移除: {self.db_path}")

        logger.info(f"RemoteDBDict closed: {self.db_name}")

    def nested(self, prefix: str) -> "NestedRemoteDBDict":
        """
        创建嵌套字典

        通过键前缀实现嵌套结构，与本地后端的 nested() API 兼容。

        Args:
            prefix: 嵌套前缀（例如 "user:1"）

        Returns:
            NestedRemoteDBDict 实例

        示例：
            db = FlaxKV("mydb", "ipc:///tmp/flaxkv.sock", auto_start=True, data_dir="./data")

            # 创建嵌套字典
            user = db.nested("user:1")
            user["name"] = "Alice"
            user["age"] = 30

            # 更深层嵌套
            profile = user.nested("profile")
            profile["bio"] = "Hello"

            # 读取
            print(db.nested("user:1")["name"])  # Alice
        """
        from flaxkv2.client.nested_remote import NestedRemoteDBDict
        # 设置嵌套标记
        self[f"__nested__:{prefix}"] = True
        return NestedRemoteDBDict(self, prefix)

    def nested_list(self, prefix: str) -> "NestedRemoteDBList":
        """
        创建嵌套列表

        通过键前缀实现嵌套列表，与本地后端的 nested_list() API 兼容。

        Args:
            prefix: 嵌套前缀（例如 "items"）

        Returns:
            NestedRemoteDBList 实例

        示例：
            db = FlaxKV("mydb", "ipc:///tmp/flaxkv.sock", auto_start=True, data_dir="./data")

            # 创建嵌套列表
            items = db.nested_list("items")
            items.append("item1")
            items.append("item2")

            # 读取
            print(items[0])  # item1
        """
        from flaxkv2.client.nested_remote import NestedRemoteDBList
        # 设置嵌套标记
        self[f"__list__:{prefix}"] = True
        return NestedRemoteDBList(self, prefix)

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
        return False

    def _get_display_info(self) -> dict:
        """
        返回展示信息（供 DisplayMixin 使用）

        Returns:
            dict 包含展示所需的所有信息
        """
        # 检查是否启用加密
        enable_encryption = False
        if self._async_client:
            enable_encryption = getattr(self._async_client, 'enable_encryption', False)

        info = {
            'class_name': 'RemoteDBDict',
            'name': self.name,
            'location': self.url,
            'closed': self._closed,
            'extras': {},
            'tags': ['remote'],
        }

        # 添加 IPC 标签
        if self.url.startswith("ipc://"):
            info['tags'].append('ipc')

        if enable_encryption:
            info['tags'].append('encrypted')

        return info


# ==================== 远程迭代器 ====================

def _is_internal_key(key: Any) -> bool:
    """检查是否是内部键"""
    if isinstance(key, str):
        return (key.startswith('__ttl_info__:') or
                key.startswith('__nested__:') or
                key.startswith('__list__:'))
    return False


class RemoteKeysIterator:
    """远程数据库键迭代器（分批获取，自动过滤内部键）"""

    def __init__(self, db: RemoteDBDict, batch_size: int = 1000, include_internal: bool = False):
        self._db = db
        self._batch_size = batch_size
        self._include_internal = include_internal
        self._start_key = None
        self._current_batch = []
        self._batch_index = 0
        self._exhausted = False

    def __iter__(self):
        return self

    def _fetch_next_batch(self):
        """获取下一批数据"""
        while True:
            keys, next_key = self._db.scan_keys(self._start_key, self._batch_size)

            # 过滤内部键
            if not self._include_internal:
                keys = [k for k in keys if not _is_internal_key(k)]

            if keys:
                self._current_batch = keys
                self._batch_index = 0
                if next_key is None:
                    self._exhausted = True
                else:
                    self._start_key = next_key
                return True
            elif next_key is None:
                # 没有更多数据
                self._exhausted = True
                return False
            else:
                # 当前批次全是内部键，继续获取下一批
                self._start_key = next_key

    def __next__(self):
        if self._batch_index < len(self._current_batch):
            key = self._current_batch[self._batch_index]
            self._batch_index += 1
            return key

        if self._exhausted:
            raise StopIteration

        if not self._fetch_next_batch():
            raise StopIteration

        key = self._current_batch[self._batch_index]
        self._batch_index += 1
        return key


class RemoteValuesIterator:
    """远程数据库值迭代器（分批获取，自动过滤内部键对应的值）"""

    def __init__(self, db: RemoteDBDict, batch_size: int = 1000, include_internal: bool = False):
        self._db = db
        self._batch_size = batch_size
        self._include_internal = include_internal
        self._start_key = None
        self._current_batch = []
        self._batch_index = 0
        self._exhausted = False

    def __iter__(self):
        return self

    def _fetch_next_batch(self):
        """获取下一批数据（使用 scan_items 来过滤内部键）"""
        while True:
            items, next_key = self._db.scan_items(self._start_key, self._batch_size)

            # 过滤内部键，只保留值
            if not self._include_internal:
                values = [v for k, v in items if not _is_internal_key(k)]
            else:
                values = [v for k, v in items]

            if values:
                self._current_batch = values
                self._batch_index = 0
                if next_key is None:
                    self._exhausted = True
                else:
                    self._start_key = next_key
                return True
            elif next_key is None:
                self._exhausted = True
                return False
            else:
                self._start_key = next_key

    def __next__(self):
        if self._batch_index < len(self._current_batch):
            value = self._current_batch[self._batch_index]
            self._batch_index += 1
            return value

        if self._exhausted:
            raise StopIteration

        if not self._fetch_next_batch():
            raise StopIteration

        value = self._current_batch[self._batch_index]
        self._batch_index += 1
        return value


class RemoteItemsIterator:
    """远程数据库键值对迭代器（分批获取，自动过滤内部键）"""

    def __init__(self, db: RemoteDBDict, batch_size: int = 1000, include_internal: bool = False):
        self._db = db
        self._batch_size = batch_size
        self._include_internal = include_internal
        self._start_key = None
        self._current_batch = []
        self._batch_index = 0
        self._exhausted = False

    def __iter__(self):
        return self

    def _fetch_next_batch(self):
        """获取下一批数据"""
        while True:
            items, next_key = self._db.scan_items(self._start_key, self._batch_size)

            # 过滤内部键
            if not self._include_internal:
                items = [(k, v) for k, v in items if not _is_internal_key(k)]

            if items:
                self._current_batch = items
                self._batch_index = 0
                if next_key is None:
                    self._exhausted = True
                else:
                    self._start_key = next_key
                return True
            elif next_key is None:
                self._exhausted = True
                return False
            else:
                self._start_key = next_key

    def __next__(self):
        if self._batch_index < len(self._current_batch):
            item = self._current_batch[self._batch_index]
            self._batch_index += 1
            return item

        if self._exhausted:
            raise StopIteration

        if not self._fetch_next_batch():
            raise StopIteration

        item = self._current_batch[self._batch_index]
        self._batch_index += 1
        return item


# ==================== 兼容性别名 ====================
# 保留旧的类名以便向后兼容
ZMQRemoteDict = RemoteDBDict
