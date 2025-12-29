"""
远程嵌套字典/列表实现

基于键前缀的简单包装，无需修改服务端协议。
利用服务端 RawLevelDBDict 的键值存储能力实现嵌套结构。

设计理念：
- 客户端负责键前缀管理
- 服务端透明存储，无需感知嵌套结构
- 与本地嵌套结构 API 兼容
"""

from typing import Any, Iterator, Optional, List, TYPE_CHECKING
from collections.abc import MutableMapping

from flaxkv2.display import DisplayMixin

if TYPE_CHECKING:
    from flaxkv2.client.zmq_client import RemoteDBDict


class NestedRemoteDBDict(DisplayMixin, MutableMapping):
    """
    远程嵌套字典实现

    通过键前缀包装 RemoteDBDict，实现嵌套字典功能。
    API 与本地 NestedDBDict 兼容。

    使用示例：
        db = FlaxKV("mydb", "ipc:///tmp/flaxkv.sock", auto_start=True, data_dir="./data")

        # 创建嵌套字典
        user = db.nested("user:1")

        # 像普通字典一样使用
        user["name"] = "Alice"
        user["age"] = 30
        user["city"] = "NYC"

        # 读取
        print(user["name"])  # Alice

        # 迭代
        for key, value in user.items():
            print(key, value)

        # 更深层嵌套
        profile = user.nested("profile")
        profile["bio"] = "Hello world"
    """

    def __init__(self, remote_db: "RemoteDBDict", prefix: str):
        """
        初始化远程嵌套字典

        Args:
            remote_db: 远程数据库客户端
            prefix: 键前缀（不含末尾冒号）
        """
        self._db = remote_db
        self._prefix = prefix.rstrip(":")  # 确保无末尾冒号

    def _full_key(self, key: str) -> str:
        """生成完整的键（带前缀）"""
        return f"{self._prefix}:{key}"

    def _is_nested_key(self, key: str) -> bool:
        """检查是否是嵌套标记键"""
        return self._db.get(f"__nested__:{self._full_key(key)}") is not None

    def __getitem__(self, key: str) -> Any:
        """获取字段值"""
        if not isinstance(key, str):
            raise TypeError(f"Key must be str, not {type(key).__name__}")

        full_key = self._full_key(key)

        # 检查是否是嵌套字典
        if self._db.get(f"__nested__:{full_key}") is not None:
            return NestedRemoteDBDict(self._db, full_key)

        # 检查是否是嵌套列表
        if self._db.get(f"__list__:{full_key}") is not None:
            return NestedRemoteDBList(self._db, full_key)

        # 普通值
        value = self._db.get(full_key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """设置字段值（支持自动嵌套）"""
        if not isinstance(key, str):
            raise TypeError(f"Key must be str, not {type(key).__name__}")

        full_key = self._full_key(key)

        if isinstance(value, dict):
            # 字典类型：递归存储为嵌套字典
            # 1. 设置嵌套标记
            self._db[f"__nested__:{full_key}"] = True
            # 清除可能的列表标记
            try:
                del self._db[f"__list__:{full_key}"]
            except KeyError:
                pass

            # 2. 创建嵌套字典并递归写入
            nested = NestedRemoteDBDict(self._db, full_key)
            nested.clear()
            for k, v in value.items():
                nested[k] = v

        elif isinstance(value, list):
            # 列表类型：递归存储为嵌套列表
            # 1. 设置嵌套标记
            self._db[f"__list__:{full_key}"] = True
            # 清除可能的字典标记
            try:
                del self._db[f"__nested__:{full_key}"]
            except KeyError:
                pass

            # 2. 创建嵌套列表并递归写入
            nested = NestedRemoteDBList(self._db, full_key)
            nested.clear()
            for item in value:
                nested.append(item)

        else:
            # 普通值：直接存储
            # 清除可能的嵌套标记
            try:
                del self._db[f"__nested__:{full_key}"]
            except KeyError:
                pass
            try:
                del self._db[f"__list__:{full_key}"]
            except KeyError:
                pass

            self._db[full_key] = value

    def __delitem__(self, key: str) -> None:
        """删除字段"""
        if not isinstance(key, str):
            raise TypeError(f"Key must be str, not {type(key).__name__}")

        full_key = self._full_key(key)

        # 检查是否是嵌套字典
        if self._db.get(f"__nested__:{full_key}") is not None:
            nested = NestedRemoteDBDict(self._db, full_key)
            nested.clear()
            del self._db[f"__nested__:{full_key}"]
            return

        # 检查是否是嵌套列表
        if self._db.get(f"__list__:{full_key}") is not None:
            nested = NestedRemoteDBList(self._db, full_key)
            nested.clear()
            del self._db[f"__list__:{full_key}"]
            return

        # 普通值
        if self._db.get(full_key) is None:
            raise KeyError(key)
        del self._db[full_key]

    def __contains__(self, key: str) -> bool:
        """检查字段是否存在"""
        if not isinstance(key, str):
            return False

        full_key = self._full_key(key)

        # 检查普通值
        if self._db.get(full_key) is not None:
            return True

        # 检查嵌套字典
        if self._db.get(f"__nested__:{full_key}") is not None:
            return True

        # 检查嵌套列表
        if self._db.get(f"__list__:{full_key}") is not None:
            return True

        return False

    def __len__(self) -> int:
        """返回字段数量"""
        return len(list(self.keys()))

    def __iter__(self) -> Iterator[str]:
        """迭代所有字段名"""
        prefix_with_colon = f"{self._prefix}:"
        prefix_len = len(prefix_with_colon)

        seen_keys = set()
        for key in self._db.keys():
            if isinstance(key, str) and key.startswith(prefix_with_colon):
                # 提取前缀后的部分
                suffix = key[prefix_len:]
                # 只取第一层的键（冒号分隔的第一部分）
                first_level_key = suffix.split(":")[0]

                # 跳过内部键
                if first_level_key.startswith("__"):
                    continue

                if first_level_key not in seen_keys:
                    seen_keys.add(first_level_key)
                    yield first_level_key

    def keys(self) -> List[str]:
        """返回所有字段名"""
        return list(iter(self))

    def values(self) -> List[Any]:
        """返回所有字段值"""
        return [self[key] for key in self.keys()]

    def items(self) -> List[tuple]:
        """返回所有字段的键值对"""
        return [(key, self[key]) for key in self.keys()]

    def get(self, key: str, default=None) -> Any:
        """获取字段值，如果不存在返回默认值"""
        try:
            return self[key]
        except KeyError:
            return default

    def set(self, key: str, value: Any) -> None:
        """设置字段值（等同于 __setitem__）"""
        self[key] = value

    def pop(self, key: str, *args) -> Any:
        """删除并返回字段值"""
        try:
            value = self[key]
            del self[key]
            return value
        except KeyError:
            if args:
                return args[0]
            raise

    def update(self, *args, **kwargs) -> None:
        """批量更新字段"""
        if args:
            other = args[0]
            if hasattr(other, "items"):
                for key, value in other.items():
                    self[key] = value
            else:
                for key, value in other:
                    self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def clear(self) -> None:
        """清空所有字段"""
        keys_to_delete = list(self.keys())
        for key in keys_to_delete:
            del self[key]

    def to_dict(self) -> dict:
        """递归转换为普通 Python 字典"""
        result = {}
        for key in self.keys():
            value = self[key]
            if isinstance(value, NestedRemoteDBDict):
                result[key] = value.to_dict()
            elif isinstance(value, NestedRemoteDBList):
                result[key] = value.to_list()
            else:
                result[key] = value
        return result

    def nested(self, key: str) -> "NestedRemoteDBDict":
        """
        创建更深层的嵌套字典

        Args:
            key: 嵌套键名

        Returns:
            NestedRemoteDBDict 实例
        """
        full_key = self._full_key(key)
        # 设置嵌套标记
        self._db[f"__nested__:{full_key}"] = True
        return NestedRemoteDBDict(self._db, full_key)

    def nested_list(self, key: str) -> "NestedRemoteDBList":
        """
        创建更深层的嵌套列表

        Args:
            key: 嵌套键名

        Returns:
            NestedRemoteDBList 实例
        """
        full_key = self._full_key(key)
        # 设置嵌套标记
        self._db[f"__list__:{full_key}"] = True
        return NestedRemoteDBList(self._db, full_key)

    def _get_display_info(self) -> dict:
        """返回展示信息"""
        return {
            "class_name": "NestedRemoteDBDict",
            "name": self._prefix,
            "location": None,
            "closed": False,
            "extras": {},
            "tags": ["nested", "remote"],
        }

    @property
    def name(self) -> str:
        """兼容 DisplayMixin 的 name 属性"""
        return self._prefix

    def __repr__(self) -> str:
        try:
            items = list(self.items())
            count = len(items)

            if count == 0:
                return f"NestedRemoteDBDict('{self._prefix}', {{}})"

            max_show = 5
            pairs = []
            for key, value in items[:max_show]:
                if isinstance(value, (NestedRemoteDBDict, NestedRemoteDBList)):
                    value_str = "{...}" if isinstance(value, NestedRemoteDBDict) else "[...]"
                else:
                    value_str = repr(value)
                    if len(value_str) > 30:
                        value_str = value_str[:27] + "..."
                pairs.append(f"{key!r}: {value_str}")

            content = ", ".join(pairs)
            if count > max_show:
                content += f", ... {count - max_show} more"

            return f"NestedRemoteDBDict('{self._prefix}', {{{content}}})"
        except Exception as e:
            return f"NestedRemoteDBDict('{self._prefix}', error={e!r})"

    def __str__(self) -> str:
        try:
            count = len(self)
            return f"<NestedRemoteDBDict '{self._prefix}' [{count} keys]>"
        except Exception:
            return f"<NestedRemoteDBDict '{self._prefix}' [nested]>"


class NestedRemoteDBList(DisplayMixin):
    """
    远程嵌套列表实现

    通过键前缀包装 RemoteDBDict，实现嵌套列表功能。
    API 与本地 NestedDBList 兼容。

    使用示例：
        db = FlaxKV("mydb", "ipc:///tmp/flaxkv.sock", auto_start=True, data_dir="./data")

        # 创建嵌套列表
        items = db.nested_list("items")

        # 像普通列表一样使用
        items.append("item1")
        items.append("item2")

        # 读取
        print(items[0])  # item1

        # 迭代
        for item in items:
            print(item)
    """

    def __init__(self, remote_db: "RemoteDBDict", prefix: str):
        """
        初始化远程嵌套列表

        Args:
            remote_db: 远程数据库客户端
            prefix: 键前缀（不含末尾冒号）
        """
        self._db = remote_db
        self._prefix = prefix.rstrip(":")
        self._length_key = f"{self._prefix}:__len__"

    def _index_key(self, index: int) -> str:
        """生成索引对应的键"""
        return f"{self._prefix}:{index:010d}"

    def _get_length(self) -> int:
        """获取列表长度"""
        length = self._db.get(self._length_key)
        return length if length is not None else 0

    def _set_length(self, length: int) -> None:
        """设置列表长度"""
        self._db[self._length_key] = length

    def __len__(self) -> int:
        return self._get_length()

    def __getitem__(self, index: int) -> Any:
        if not isinstance(index, int):
            raise TypeError(f"List indices must be integers, not {type(index).__name__}")

        length = self._get_length()

        # 支持负索引
        if index < 0:
            index = length + index

        if index < 0 or index >= length:
            raise IndexError("list index out of range")

        key = self._index_key(index)
        full_key = f"{self._prefix}:{index}"

        # 检查是否是嵌套字典
        if self._db.get(f"__nested__:{full_key}") is not None:
            return NestedRemoteDBDict(self._db, full_key)

        # 检查是否是嵌套列表
        if self._db.get(f"__list__:{full_key}") is not None:
            return NestedRemoteDBList(self._db, full_key)

        # 普通值
        value = self._db.get(key)
        if value is None:
            raise IndexError(f"list index {index} not found in storage")
        return value

    def __setitem__(self, index: int, value: Any) -> None:
        if not isinstance(index, int):
            raise TypeError(f"List indices must be integers, not {type(index).__name__}")

        length = self._get_length()

        # 支持负索引
        if index < 0:
            index = length + index

        if index < 0 or index >= length:
            raise IndexError("list assignment index out of range")

        key = self._index_key(index)
        full_key = f"{self._prefix}:{index}"

        if isinstance(value, dict):
            # 字典类型：递归存储
            self._db[f"__nested__:{full_key}"] = True
            try:
                del self._db[f"__list__:{full_key}"]
            except KeyError:
                pass

            nested = NestedRemoteDBDict(self._db, full_key)
            nested.clear()
            for k, v in value.items():
                nested[k] = v

            # 存储占位符
            self._db[key] = True

        elif isinstance(value, list):
            # 列表类型：递归存储
            self._db[f"__list__:{full_key}"] = True
            try:
                del self._db[f"__nested__:{full_key}"]
            except KeyError:
                pass

            nested = NestedRemoteDBList(self._db, full_key)
            nested.clear()
            for item in value:
                nested.append(item)

            # 存储占位符
            self._db[key] = True

        else:
            # 普通值
            try:
                del self._db[f"__nested__:{full_key}"]
            except KeyError:
                pass
            try:
                del self._db[f"__list__:{full_key}"]
            except KeyError:
                pass

            self._db[key] = value

    def __delitem__(self, index: int) -> None:
        if not isinstance(index, int):
            raise TypeError(f"List indices must be integers, not {type(index).__name__}")

        length = self._get_length()

        if index < 0:
            index = length + index

        if index < 0 or index >= length:
            raise IndexError("list index out of range")

        full_key = f"{self._prefix}:{index}"

        # 清理嵌套数据
        if self._db.get(f"__nested__:{full_key}") is not None:
            nested = NestedRemoteDBDict(self._db, full_key)
            nested.clear()
            del self._db[f"__nested__:{full_key}"]
        elif self._db.get(f"__list__:{full_key}") is not None:
            nested = NestedRemoteDBList(self._db, full_key)
            nested.clear()
            del self._db[f"__list__:{full_key}"]

        # 移动后续元素
        for i in range(index, length - 1):
            next_key = self._index_key(i + 1)
            next_value = self._db.get(next_key)
            if next_value is not None:
                current_key = self._index_key(i)
                self._db[current_key] = next_value

        # 删除最后一个元素
        last_key = self._index_key(length - 1)
        try:
            del self._db[last_key]
        except KeyError:
            pass

        # 更新长度
        self._set_length(length - 1)

    def __iter__(self):
        length = self._get_length()
        for i in range(length):
            yield self[i]

    def __contains__(self, value: Any) -> bool:
        for item in self:
            if item == value:
                return True
        return False

    def append(self, value: Any) -> None:
        """在列表末尾添加元素"""
        length = self._get_length()
        self._set_length(length + 1)
        self[length] = value

    def extend(self, values) -> None:
        """扩展列表"""
        for value in values:
            self.append(value)

    def insert(self, index: int, value: Any) -> None:
        """在指定位置插入元素"""
        length = self._get_length()

        if index < 0:
            index = max(0, length + index)
        else:
            index = min(index, length)

        # 后移元素
        for i in range(length - 1, index - 1, -1):
            current_key = self._index_key(i)
            current_value = self._db.get(current_key)
            if current_value is not None:
                next_key = self._index_key(i + 1)
                self._db[next_key] = current_value

        # 更新长度
        self._set_length(length + 1)

        # 设置新元素
        self[index] = value

    def pop(self, index: int = -1) -> Any:
        """删除并返回指定位置的元素"""
        if self._get_length() == 0:
            raise IndexError("pop from empty list")

        value = self[index]
        del self[index]
        return value

    def clear(self) -> None:
        """清空列表"""
        length = self._get_length()

        for i in range(length):
            full_key = f"{self._prefix}:{i}"
            key = self._index_key(i)

            # 清理嵌套标记和数据
            if self._db.get(f"__nested__:{full_key}") is not None:
                nested = NestedRemoteDBDict(self._db, full_key)
                nested.clear()
                try:
                    del self._db[f"__nested__:{full_key}"]
                except KeyError:
                    pass
            elif self._db.get(f"__list__:{full_key}") is not None:
                nested = NestedRemoteDBList(self._db, full_key)
                nested.clear()
                try:
                    del self._db[f"__list__:{full_key}"]
                except KeyError:
                    pass

            # 删除元素
            try:
                del self._db[key]
            except KeyError:
                pass

        # 重置长度
        self._set_length(0)

    def index(self, value: Any, start: int = 0, stop: Optional[int] = None) -> int:
        """返回值的索引"""
        length = self._get_length()
        if stop is None:
            stop = length

        for i in range(start, min(stop, length)):
            if self[i] == value:
                return i

        raise ValueError(f"{value} is not in list")

    def count(self, value: Any) -> int:
        """计算值出现的次数"""
        count = 0
        for item in self:
            if item == value:
                count += 1
        return count

    def to_list(self) -> list:
        """递归转换为普通 Python 列表"""
        result = []
        for item in self:
            if isinstance(item, NestedRemoteDBList):
                result.append(item.to_list())
            elif isinstance(item, NestedRemoteDBDict):
                result.append(item.to_dict())
            else:
                result.append(item)
        return result

    def _get_display_info(self) -> dict:
        """返回展示信息"""
        return {
            "class_name": "NestedRemoteDBList",
            "name": self._prefix,
            "location": None,
            "closed": False,
            "extras": {"length": self._get_length()},
            "tags": ["nested", "remote", "list"],
        }

    @property
    def name(self) -> str:
        return self._prefix

    def __repr__(self) -> str:
        try:
            items = list(self)
            count = len(items)

            if count == 0:
                return f"NestedRemoteDBList('{self._prefix}', [])"

            max_show = 5
            item_strs = []
            for item in items[:max_show]:
                if isinstance(item, (NestedRemoteDBDict, NestedRemoteDBList)):
                    item_str = "{...}" if isinstance(item, NestedRemoteDBDict) else "[...]"
                else:
                    item_str = repr(item)
                    if len(item_str) > 30:
                        item_str = item_str[:27] + "..."
                item_strs.append(item_str)

            content = ", ".join(item_strs)
            if count > max_show:
                content += f", ... {count - max_show} more"

            return f"NestedRemoteDBList('{self._prefix}', [{content}])"
        except Exception as e:
            return f"NestedRemoteDBList('{self._prefix}', error={e!r})"

    def __str__(self) -> str:
        try:
            count = len(self)
            return f"<NestedRemoteDBList '{self._prefix}' [{count} items]>"
        except Exception:
            return f"<NestedRemoteDBList '{self._prefix}' [nested]>"
