"""
FlaxKV2 Vector - 向量存储扩展

基于 hnswlib 提供向量相似度搜索，FlaxKV2 负责元数据存储。

使用前需要安装 hnswlib:
    pip install flaxkv2[vector]
"""

from flaxkv2.vector.store import VectorStore

__all__ = ["VectorStore"]
