"""
FlaxKV2 Inspector - 数据库可视化和检查工具核心模块
"""

import sys
from typing import Any, Dict, List, Optional, Iterator, Tuple, Set
from datetime import datetime, timezone
import re

from flaxkv2 import FlaxKV


def get_deep_size(obj: Any, seen: Optional[Set[int]] = None) -> int:
    """
    递归计算对象的深度大小（包括嵌套对象）

    Args:
        obj: 要计算大小的对象
        seen: 已访问对象的 id 集合（避免循环引用）

    Returns:
        对象的总字节大小
    """
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        size += sum(get_deep_size(k, seen) + get_deep_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(get_deep_size(item, seen) for item in obj)
    elif hasattr(obj, '__dict__'):
        size += get_deep_size(obj.__dict__, seen)
    elif hasattr(obj, '__slots__'):
        size += sum(get_deep_size(getattr(obj, slot), seen)
                    for slot in obj.__slots__ if hasattr(obj, slot))

    return size


class Inspector:
    """
    FlaxKV 数据库检查器核心类

    提供数据浏览、统计分析、搜索等功能，供 CLI 和 Web UI 共同使用
    """

    def __init__(self, db_name: str, path: str, backend: str = 'local', **kwargs):
        """
        初始化 Inspector

        Args:
            db_name: 数据库名称
            path: 数据库路径（本地路径或远程地址）
            backend: 后端类型 ('local', 'remote', 'auto')
            **kwargs: 传递给 FlaxKV 的其他参数
        """
        self.db_name = db_name
        self.path = path
        self.backend = backend

        # 将 'auto' 转换为 None，让 FlaxKV 自动检测
        backend_param = None if backend == 'auto' else backend
        self.db = FlaxKV(db_name, path, backend=backend_param, **kwargs)

    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def count_keys(self, pattern: Optional[str] = None) -> int:
        """
        获取键总数

        Args:
            pattern: 正则表达式模式（可选），如果指定则只计算匹配的键

        Returns:
            键的数量
        """
        if pattern is None:
            try:
                return len(self.db)
            except Exception:
                # 如果 len() 不支持，则遍历计数
                return sum(1 for _ in self.db.keys())
        else:
            # 带 pattern 时需要遍历计数
            regex = re.compile(pattern)
            return sum(1 for key in self.db.keys() if regex.search(key))

    def list_keys(self, pattern: Optional[str] = None, limit: int = 100,
                  offset: int = 0) -> List[str]:
        """
        列出所有键（支持分页和模式匹配）

        Args:
            pattern: 正则表达式模式（可选）
            limit: 返回的最大数量
            offset: 跳过的键数量

        Returns:
            键列表
        """
        keys, _ = self.list_keys_with_count(pattern=pattern, limit=limit, offset=offset)
        return keys

    def list_keys_with_count(self, pattern: Optional[str] = None, limit: int = 100,
                             offset: int = 0) -> Tuple[List[str], int]:
        """
        列出键并返回匹配总数（单次遍历，避免双重遍历性能问题）

        Args:
            pattern: 正则表达式模式（可选）
            limit: 返回的最大数量
            offset: 跳过的键数量

        Returns:
            (键列表, 匹配的总数量)
        """
        keys = []
        regex = re.compile(pattern) if pattern else None

        total_matched = 0
        for key in self.db.keys():
            # 模式匹配
            if regex and not regex.search(key):
                continue

            total_matched += 1

            # 分页：跳过 offset 之前的
            if total_matched <= offset:
                continue

            # 收集 limit 个 key（但继续遍历以统计 total）
            if len(keys) < limit:
                keys.append(key)

        return keys, total_matched

    def get_value_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取键的详细信息

        Args:
            key: 键名

        Returns:
            包含类型、大小、TTL、值等信息的字典，键不存在返回 None
        """
        if key not in self.db:
            return None

        try:
            # 获取原始值
            raw_value = self.db[key]

            # 获取值的基本信息
            info = {
                'key': key,
                'exists': True,
                'type': type(raw_value).__name__,
                'size': get_deep_size(raw_value),
                'value': None,
                'ttl': None,
                'expires_at': None,
            }

            # 尝试获取更详细的类型信息
            type_name = self._get_type_name(raw_value)
            info['type'] = type_name

            # 获取值的预览
            info['value'] = self._get_value_preview(raw_value)

            # 检查是否有 TTL 信息
            ttl_info = self._get_ttl_info(key)
            if ttl_info:
                info.update(ttl_info)

            return info

        except Exception as e:
            return {
                'key': key,
                'exists': True,
                'error': str(e),
                'type': 'unknown',
                'size': 0,
            }

    def _get_type_name(self, value: Any) -> str:
        """获取值的类型名称"""
        type_map = {
            'int': 'integer',
            'float': 'float',
            'str': 'string',
            'bool': 'boolean',
            'list': 'list',
            'dict': 'dict',
            'bytes': 'bytes',
            'NoneType': 'null',
        }

        type_name = type(value).__name__

        # 特殊类型检测
        if type_name == 'ndarray':
            return 'numpy.ndarray'
        elif type_name == 'DataFrame':
            return 'pandas.DataFrame'
        elif type_name == 'Series':
            return 'pandas.Series'
        elif type_name == 'NestedDBList':
            return 'list'
        elif type_name == 'NestedDBDict':
            return 'dict'

        return type_map.get(type_name, type_name)

    def _get_value_preview(self, value: Any, max_length: int = 100) -> Any:
        """获取值的预览（截断长内容）"""
        # 处理 NestedDBList 和 NestedDBDict - 转换为普通类型
        type_name = type(value).__name__
        if type_name == 'NestedDBList':
            # 转换为普通列表
            try:
                value = value.to_list()
            except Exception:
                value = list(value)
        elif type_name == 'NestedDBDict':
            # 转换为普通字典
            try:
                value = value.to_dict()
            except Exception:
                value = dict(value)

        if isinstance(value, (str, bytes)):
            if len(value) > max_length:
                preview = value[:max_length]
                if isinstance(value, str):
                    return preview + '...'
                else:
                    return preview + b'...'
            return value
        elif isinstance(value, (list, tuple)):
            if len(value) > 10:
                return list(value[:10]) + ['...']
            return value
        elif isinstance(value, dict):
            if len(value) > 10:
                items = list(value.items())[:10]
                preview = dict(items)
                preview['...'] = f'... ({len(value) - 10} more items)'
                return preview
            return value
        else:
            # 其他类型，尝试转为字符串
            str_repr = str(value)
            if len(str_repr) > max_length:
                return str_repr[:max_length] + '...'
            return value

    def _get_ttl_info(self, key: str) -> Optional[Dict[str, Any]]:
        """获取键的 TTL 信息"""
        try:
            # 优先使用统一的 get_ttl 方法（本地后端支持）
            if hasattr(self.db, 'get_ttl'):
                ttl = self.db.get_ttl(key)
                if ttl is not None and ttl > 0:
                    from datetime import timedelta
                    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
                    return {
                        'ttl': ttl,
                        'expires_at': expires_at.isoformat(),
                        'expired': False,
                    }
                elif ttl is not None and ttl <= 0:
                    return {
                        'ttl': 0,
                        'expires_at': None,
                        'expired': True,
                    }
            # 远程后端暂不支持 TTL 查询，返回 None
            return None
        except Exception:
            return None

    def delete_key(self, key: str) -> bool:
        """
        删除指定键

        Args:
            key: 键名

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            if key in self.db:
                del self.db[key]
                return True
            return False
        except Exception:
            return False

    def set_value(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置键值

        Args:
            key: 键名
            value: 值
            ttl: 过期时间（秒）

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            if ttl:
                self.db.set(key, value, ttl=ttl)
            else:
                self.db[key] = value
            return True
        except Exception:
            return False

    def get_stats(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Args:
            sample_size: 采样大小（可选）。如果指定，将随机采样指定数量的键进行统计，
                        适用于大数据库的近似统计。None 表示统计所有键。

        Returns:
            统计信息字典
        """
        import random

        stats = {
            'total_keys': 0,
            'sampled_keys': 0,
            'error_keys': 0,
            'is_sampled': sample_size is not None,
            'type_distribution': {},
            'size_distribution': {
                'tiny': 0,      # < 1KB
                'small': 0,     # 1KB - 10KB
                'medium': 0,    # 10KB - 100KB
                'large': 0,     # 100KB - 1MB
                'huge': 0,      # > 1MB
            },
            'ttl_status': {
                'with_ttl': 0,
                'without_ttl': 0,
                'expired': 0,
            },
            'total_size': 0,
        }

        try:
            # 获取所有键
            all_keys = list(self.db.keys())
            stats['total_keys'] = len(all_keys)

            # 决定要统计的键
            if sample_size is not None and sample_size < len(all_keys):
                keys_to_process = random.sample(all_keys, sample_size)
                stats['sampled_keys'] = sample_size
            else:
                keys_to_process = all_keys
                stats['sampled_keys'] = len(all_keys)

            for key in keys_to_process:
                try:
                    value = self.db[key]

                    # 类型分布
                    type_name = self._get_type_name(value)
                    stats['type_distribution'][type_name] = \
                        stats['type_distribution'].get(type_name, 0) + 1

                    # 大小分布（使用深度计算）
                    size = get_deep_size(value)
                    stats['total_size'] += size

                    if size < 1024:
                        stats['size_distribution']['tiny'] += 1
                    elif size < 10 * 1024:
                        stats['size_distribution']['small'] += 1
                    elif size < 100 * 1024:
                        stats['size_distribution']['medium'] += 1
                    elif size < 1024 * 1024:
                        stats['size_distribution']['large'] += 1
                    else:
                        stats['size_distribution']['huge'] += 1

                    # TTL 状态
                    ttl_info = self._get_ttl_info(key)
                    if ttl_info:
                        stats['ttl_status']['with_ttl'] += 1
                        if ttl_info.get('expired'):
                            stats['ttl_status']['expired'] += 1
                    else:
                        stats['ttl_status']['without_ttl'] += 1

                except Exception:
                    stats['error_keys'] += 1
                    continue

            # 如果是采样统计，推算总大小
            if stats['is_sampled'] and stats['sampled_keys'] > 0:
                scale_factor = stats['total_keys'] / stats['sampled_keys']
                stats['estimated_total_size'] = int(stats['total_size'] * scale_factor)

            return stats

        except Exception as e:
            return {
                'error': str(e),
                'total_keys': 0,
            }

    def search_keys(self, pattern: str, limit: int = 100) -> List[Tuple[str, Any]]:
        """
        搜索键（返回键和部分信息）

        Args:
            pattern: 正则表达式模式
            limit: 最大返回数量

        Returns:
            (键名, 简要信息) 的列表
        """
        results = []
        regex = re.compile(pattern)

        for key in self.db.keys():
            if not regex.search(key):
                continue

            if len(results) >= limit:
                break

            try:
                value = self.db[key]
                info = {
                    'type': self._get_type_name(value),
                    'size': get_deep_size(value),
                }
                results.append((key, info))
            except Exception:
                results.append((key, {'type': 'error', 'size': 0}))

        return results

    def export_data(self, keys: Optional[List[str]] = None, limit: int = 10000) -> Dict[str, Any]:
        """
        导出数据（带内存保护）

        Args:
            keys: 要导出的键列表，None 表示导出所有
            limit: 最大导出数量（默认 10000，防止内存溢出）

        Returns:
            包含键值对的字典
        """
        data = {}
        if keys:
            key_list = keys[:limit]
        else:
            key_list = []
            for i, key in enumerate(self.db.keys()):
                if i >= limit:
                    break
                key_list.append(key)

        for key in key_list:
            try:
                data[key] = self.db[key]
            except Exception:
                data[key] = None

        return data

    def iter_items(self, pattern: Optional[str] = None) -> Iterator[Tuple[str, Any]]:
        """
        迭代所有键值对（流式处理，内存友好）

        Args:
            pattern: 正则表达式模式（可选）

        Yields:
            (键, 值) 元组
        """
        regex = re.compile(pattern) if pattern else None

        for key in self.db.keys():
            if regex and not regex.search(key):
                continue
            try:
                yield key, self.db[key]
            except Exception:
                yield key, None
