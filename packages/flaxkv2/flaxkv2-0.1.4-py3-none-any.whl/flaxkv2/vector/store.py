"""
VectorStore - 基于 hnswlib + FlaxKV2 的向量存储

职责分离：
- hnswlib: 向量索引、相似度搜索
- FlaxKV2: 元数据存储、ID 映射、持久化
"""

import os
import time
import threading
import atexit
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np

try:
    import hnswlib
except ImportError:
    raise ImportError(
        "hnswlib 未安装。请运行: pip install hnswlib\n"
        "或者: pip install flaxkv2[vector]"
    )

from flaxkv2 import FlaxKV


class VectorStore:
    """
    向量存储，结合 hnswlib 和 FlaxKV2

    示例:
        >>> store = VectorStore("my_vectors", "./data", dim=128)
        >>> store.add("doc1", vector, {"title": "Hello"})
        >>> results = store.search(query_vector, k=10)
        >>> store.close()

    或使用上下文管理器:
        >>> with VectorStore("my_vectors", "./data", dim=128) as store:
        ...     store.add("doc1", vector, {"title": "Hello"})
        ...     results = store.search(query_vector, k=10)
    """

    # FlaxKV2 键前缀
    _PREFIX_META = "meta:"      # 元数据: meta:{id} -> {metadata}
    _PREFIX_IDX = "idx:"        # ID映射: idx:{id} -> int_index
    _PREFIX_RIDX = "ridx:"      # 反向索引: ridx:{int_index} -> id
    _KEY_CONFIG = "__config__"  # 配置信息
    _KEY_COUNTER = "__counter__"  # 自增计数器

    def __init__(
        self,
        name: str,
        path: str,
        dim: int,
        space: str = "cosine",
        max_elements: int = 10000,
        ef_construction: int = 200,
        M: int = 16,
        ef_search: int = 50,
        auto_save: bool = True,
        save_on_write: int = 100,
        save_interval: float = 60.0,
        write_buffer_size: int = 0,
    ):
        """
        初始化 VectorStore

        Args:
            name: 存储名称
            path: 数据目录路径
            dim: 向量维度
            space: 距离度量 ('cosine', 'l2', 'ip')
            max_elements: 最大元素数量（可动态扩展）
            ef_construction: 构建时的 ef 参数（越大越精确，越慢）
            M: 每个节点的连接数（越大越精确，占用更多内存）
            ef_search: 搜索时的 ef 参数（越大越精确，越慢）
            auto_save: 关闭时是否自动保存索引
            save_on_write: 每 N 次写入后自动保存（0 表示禁用）
            save_interval: 定时保存间隔（秒），0 表示禁用
            write_buffer_size: 写缓冲大小（0 表示禁用，启用后大幅提升写入性能）
        """
        self.name = name
        self.path = Path(path)
        self.dim = dim
        self.space = space
        self.max_elements = max_elements
        self.ef_construction = ef_construction
        self.M = M
        self.ef_search = ef_search
        self.auto_save = auto_save
        self.save_on_write = save_on_write
        self.save_interval = save_interval
        self.write_buffer_size = write_buffer_size

        # 写入计数和脏标记
        self._write_count = 0
        self._dirty = False
        self._closed = False
        self._lock = threading.Lock()

        # 确保目录存在
        self.path.mkdir(parents=True, exist_ok=True)

        # 索引文件路径
        self._index_file = self.path / f"{name}.hnsw"

        # 初始化 FlaxKV2（存储元数据和 ID 映射）
        # 启用写缓冲可大幅提升写入性能
        if write_buffer_size > 0:
            self._kv = FlaxKV(f"{name}_meta", str(self.path), write_buffer_size=write_buffer_size)
        else:
            self._kv = FlaxKV(f"{name}_meta", str(self.path))

        # 初始化或加载 HNSW 索引
        self._index = hnswlib.Index(space=space, dim=dim)
        self._load_or_init_index()

        # 启动定时保存线程
        self._save_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        if self.save_interval > 0:
            self._start_save_thread()

        # 注册退出时保存
        atexit.register(self._atexit_save)

    def _load_or_init_index(self):
        """加载已有索引或初始化新索引"""
        if self._index_file.exists() and self._KEY_CONFIG in self._kv:
            # 加载已有索引
            config = self._kv[self._KEY_CONFIG]
            if config["dim"] != self.dim:
                raise ValueError(
                    f"维度不匹配: 已有索引维度={config['dim']}, 请求维度={self.dim}"
                )
            self._index.load_index(str(self._index_file), max_elements=config["max_elements"])
            self._index.set_ef(self.ef_search)
            self.max_elements = config["max_elements"]
        else:
            # 初始化新索引
            self._index.init_index(
                max_elements=self.max_elements,
                ef_construction=self.ef_construction,
                M=self.M,
            )
            self._index.set_ef(self.ef_search)
            # 保存配置
            self._kv[self._KEY_CONFIG] = {
                "dim": self.dim,
                "space": self.space,
                "max_elements": self.max_elements,
                "ef_construction": self.ef_construction,
                "M": self.M,
            }
            # 初始化计数器
            if self._KEY_COUNTER not in self._kv:
                self._kv[self._KEY_COUNTER] = 0

    def _start_save_thread(self):
        """启动定时保存后台线程"""
        def save_loop():
            while not self._stop_event.wait(self.save_interval):
                if self._dirty and not self._closed:
                    try:
                        self._do_save()
                    except Exception:
                        pass  # 忽略保存错误，下次重试

        self._save_thread = threading.Thread(target=save_loop, daemon=True)
        self._save_thread.start()

    def _atexit_save(self):
        """程序退出时保存"""
        if not self._closed and self._dirty:
            try:
                self._do_save()
            except Exception:
                pass

    def _do_save(self):
        """执行保存（内部方法）"""
        with self._lock:
            if self._dirty:
                self._index.save_index(str(self._index_file))
                self._dirty = False
                self._write_count = 0

    def _mark_dirty(self):
        """标记有未保存的修改，并检查是否需要触发保存"""
        self._dirty = True
        self._write_count += 1

        # 检查是否达到写入计数阈值
        if self.save_on_write > 0 and self._write_count >= self.save_on_write:
            self._do_save()

    def _get_next_idx(self) -> int:
        """获取下一个整数索引"""
        idx = self._kv[self._KEY_COUNTER]
        self._kv[self._KEY_COUNTER] = idx + 1
        return idx

    def _ensure_capacity(self, needed: int = 1):
        """确保索引容量足够"""
        current_count = self._index.get_current_count()
        if current_count + needed > self.max_elements:
            # 扩展容量（翻倍）
            new_max = max(self.max_elements * 2, current_count + needed)
            self._index.resize_index(new_max)
            self.max_elements = new_max
            # 更新配置
            config = self._kv[self._KEY_CONFIG]
            config["max_elements"] = new_max
            self._kv[self._KEY_CONFIG] = config

    def add(
        self,
        id: str,
        vector: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        添加单个向量

        Args:
            id: 唯一标识符（字符串）
            vector: 向量（numpy 数组）
            metadata: 元数据字典（可选）

        Returns:
            内部整数索引
        """
        vector = np.asarray(vector, dtype=np.float32)
        if vector.shape != (self.dim,):
            raise ValueError(f"向量维度错误: 期望 {self.dim}, 实际 {vector.shape}")

        # 检查是否已存在
        idx_key = f"{self._PREFIX_IDX}{id}"
        if idx_key in self._kv:
            # 更新已有向量
            idx = self._kv[idx_key]
            # hnswlib 不支持直接更新，需要标记删除后重新添加
            self._index.mark_deleted(idx)
            self._index.add_items(vector.reshape(1, -1), [idx])
        else:
            # 添加新向量
            self._ensure_capacity(1)
            idx = self._get_next_idx()
            self._index.add_items(vector.reshape(1, -1), [idx])
            self._kv[idx_key] = idx

        # 存储元数据
        meta_key = f"{self._PREFIX_META}{id}"
        self._kv[meta_key] = {
            "id": id,
            "idx": idx,
            "metadata": metadata or {},
        }

        # 存储反向索引 (idx -> id)
        ridx_key = f"{self._PREFIX_RIDX}{idx}"
        self._kv[ridx_key] = id

        # 标记脏数据
        self._mark_dirty()

        return idx

    def add_batch(
        self,
        ids: List[str],
        vectors: np.ndarray,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[int]:
        """
        批量添加向量（优化：真正的批量 HNSW 写入）

        Args:
            ids: ID 列表
            vectors: 向量数组 (n, dim)
            metadatas: 元数据列表（可选）

        Returns:
            内部索引列表
        """
        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        if vectors.shape[1] != self.dim:
            raise ValueError(f"向量维度错误: 期望 {self.dim}, 实际 {vectors.shape[1]}")
        if len(ids) != vectors.shape[0]:
            raise ValueError(f"ID 数量与向量数量不匹配: {len(ids)} vs {vectors.shape[0]}")

        metadatas = metadatas or [{}] * len(ids)

        # 分离：已存在的 ID（需要更新）vs 新 ID（可批量添加）
        new_indices = []  # 新增的在原数组中的位置
        update_indices = []  # 需要更新的在原数组中的位置

        for i, id_ in enumerate(ids):
            idx_key = f"{self._PREFIX_IDX}{id_}"
            if idx_key in self._kv:
                update_indices.append(i)
            else:
                new_indices.append(i)

        result_indices = [0] * len(ids)

        # 1. 处理更新（逐条，因为需要 mark_deleted）
        for i in update_indices:
            idx = self.add(ids[i], vectors[i], metadatas[i])
            result_indices[i] = idx

        # 2. 批量处理新增
        if new_indices:
            self._ensure_capacity(len(new_indices))

            # 批量分配 idx
            start_idx = self._kv[self._KEY_COUNTER]
            new_idx_list = list(range(start_idx, start_idx + len(new_indices)))
            self._kv[self._KEY_COUNTER] = start_idx + len(new_indices)

            # 批量写入 HNSW（关键优化点）
            new_vectors = vectors[new_indices]
            self._index.add_items(new_vectors, new_idx_list)

            # 批量写入元数据和索引
            for j, i in enumerate(new_indices):
                id_ = ids[i]
                idx = new_idx_list[j]
                meta = metadatas[i]

                # 存储 ID -> idx 映射
                self._kv[f"{self._PREFIX_IDX}{id_}"] = idx
                # 存储反向索引
                self._kv[f"{self._PREFIX_RIDX}{idx}"] = id_
                # 存储元数据
                self._kv[f"{self._PREFIX_META}{id_}"] = {
                    "id": id_,
                    "idx": idx,
                    "metadata": meta,
                }
                result_indices[i] = idx

            self._mark_dirty()

        return result_indices

    def search(
        self,
        query: np.ndarray,
        k: int = 10,
        filter_func: Optional[callable] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索最相似的向量

        Args:
            query: 查询向量
            k: 返回结果数量
            filter_func: 过滤函数，接收 metadata，返回 bool

        Returns:
            结果列表，每项包含 {id, distance, metadata}
        """
        query = np.asarray(query, dtype=np.float32)
        if query.shape != (self.dim,):
            raise ValueError(f"查询向量维度错误: 期望 {self.dim}, 实际 {query.shape}")

        # 如果有过滤，需要多取一些结果；同时不能超过实际数量
        current_count = self._index.get_current_count()
        fetch_k = min(k * 3 if filter_func else k, current_count)

        if fetch_k == 0:
            return []

        indices, distances = self._index.knn_query(query.reshape(1, -1), k=fetch_k)

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            # 查找 ID 和元数据
            meta_data = self._find_by_idx(idx)
            if meta_data is None:
                continue

            # 应用过滤
            if filter_func and not filter_func(meta_data["metadata"]):
                continue

            results.append({
                "id": meta_data["id"],
                "distance": float(distance),
                "metadata": meta_data["metadata"],
            })

            if len(results) >= k:
                break

        return results

    def search_batch(
        self,
        queries: np.ndarray,
        k: int = 10,
    ) -> List[List[Dict[str, Any]]]:
        """
        批量搜索

        Args:
            queries: 查询向量数组 (n, dim)
            k: 每个查询返回的结果数量

        Returns:
            结果列表的列表
        """
        queries = np.asarray(queries, dtype=np.float32)
        if queries.ndim == 1:
            queries = queries.reshape(1, -1)

        all_indices, all_distances = self._index.knn_query(queries, k=k)

        all_results = []
        for indices, distances in zip(all_indices, all_distances):
            results = []
            for idx, distance in zip(indices, distances):
                meta_data = self._find_by_idx(idx)
                if meta_data:
                    results.append({
                        "id": meta_data["id"],
                        "distance": float(distance),
                        "metadata": meta_data["metadata"],
                    })
            all_results.append(results)

        return all_results

    def _find_by_idx(self, idx: int) -> Optional[Dict]:
        """通过整数索引查找元数据（使用反向索引 O(1) 查找）"""
        ridx_key = f"{self._PREFIX_RIDX}{idx}"
        if ridx_key not in self._kv:
            return None
        id = self._kv[ridx_key]
        meta_key = f"{self._PREFIX_META}{id}"
        if meta_key in self._kv:
            return self._kv[meta_key]
        return None

    def get(self, id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定 ID 的元数据

        Args:
            id: 向量 ID

        Returns:
            元数据字典，不存在返回 None
        """
        meta_key = f"{self._PREFIX_META}{id}"
        if meta_key in self._kv:
            return self._kv[meta_key]["metadata"]
        return None

    def delete(self, id: str) -> bool:
        """
        删除向量（标记删除）

        Args:
            id: 向量 ID

        Returns:
            是否成功删除
        """
        idx_key = f"{self._PREFIX_IDX}{id}"
        meta_key = f"{self._PREFIX_META}{id}"

        if idx_key not in self._kv:
            return False

        idx = self._kv[idx_key]
        ridx_key = f"{self._PREFIX_RIDX}{idx}"

        self._index.mark_deleted(idx)
        del self._kv[idx_key]
        del self._kv[meta_key]
        if ridx_key in self._kv:
            del self._kv[ridx_key]

        # 标记脏数据
        self._mark_dirty()

        return True

    def __contains__(self, id: str) -> bool:
        """检查 ID 是否存在"""
        return f"{self._PREFIX_IDX}{id}" in self._kv

    def __len__(self) -> int:
        """返回向量数量"""
        return self._index.get_current_count()

    def count(self) -> int:
        """返回向量数量"""
        return len(self)

    def save(self):
        """保存索引到磁盘"""
        self._do_save()

    def close(self):
        """关闭存储"""
        if self._closed:
            return
        self._closed = True

        # 停止后台保存线程
        self._stop_event.set()
        if self._save_thread and self._save_thread.is_alive():
            self._save_thread.join(timeout=1.0)

        # 取消 atexit 注册
        try:
            atexit.unregister(self._atexit_save)
        except Exception:
            pass

        # 最终保存
        if self.auto_save and self._dirty:
            try:
                self._index.save_index(str(self._index_file))
            except Exception:
                pass

        self._kv.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def info(self) -> Dict[str, Any]:
        """获取存储信息"""
        return {
            "name": self.name,
            "path": str(self.path),
            "dim": self.dim,
            "space": self.space,
            "count": len(self),
            "max_elements": self.max_elements,
            "ef_search": self.ef_search,
            "index_file": str(self._index_file),
            "index_file_exists": self._index_file.exists(),
            "dirty": self._dirty,
            "write_count": self._write_count,
            "save_on_write": self.save_on_write,
            "save_interval": self.save_interval,
        }
