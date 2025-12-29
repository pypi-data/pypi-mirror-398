"""
FlaxKV2 统一展示模块

设计原则：
1. __repr__: 轻量级标识，零 I/O，构造函数风格
2. __str__: 友好摘要，零 I/O，单行简洁
3. preview(): 按需数据预览，显式 I/O

所有展示方法都不会触发不必要的 I/O 操作。
"""

from typing import Any, Optional, List, Tuple


def format_value(value: Any, max_len: int = 60) -> str:
    """
    智能格式化值，处理特殊类型

    Args:
        value: 要格式化的值
        max_len: 最大显示长度

    Returns:
        格式化后的字符串
    """
    # NumPy 数组
    try:
        import numpy as np
        if isinstance(value, np.ndarray):
            return f"<ndarray {value.shape} {value.dtype}>"
    except ImportError:
        pass

    # Pandas DataFrame
    try:
        import pandas as pd
        if isinstance(value, pd.DataFrame):
            return f"<DataFrame {value.shape}>"
        if isinstance(value, pd.Series):
            return f"<Series len={len(value)}>"
    except ImportError:
        pass

    # bytes
    if isinstance(value, bytes):
        size = len(value)
        if size < 1024:
            return f"<bytes {size}B>"
        elif size < 1024 * 1024:
            return f"<bytes {size/1024:.1f}KB>"
        else:
            return f"<bytes {size/(1024*1024):.1f}MB>"

    # 嵌套字典
    if isinstance(value, dict):
        s = repr(value)
        if len(s) > max_len:
            return f"{{...{len(value)} keys}}"
        return s

    # 嵌套列表
    if isinstance(value, list):
        s = repr(value)
        if len(s) > max_len:
            return f"[...{len(value)} items]"
        return s

    # 通用处理
    s = repr(value)
    if len(s) > max_len:
        return s[:max_len - 3] + "..."
    return s


def format_size(size_bytes: int) -> str:
    """格式化字节大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def build_preview(
    items_func,
    keys_count_func,
    name: str,
    class_name: str,
    n: int = 10,
    stat_func=None
) -> str:
    """
    构建数据预览字符串

    Args:
        items_func: 获取 items 的函数/方法，签名: () -> List[Tuple[key, value]]
        keys_count_func: 获取键数量的函数/方法，签名: () -> int
        name: 数据库名称
        class_name: 类名
        n: 预览的键值对数量
        stat_func: 可选的统计信息函数，签名: () -> dict

    Returns:
        格式化的预览字符串
    """
    lines = []

    # 获取统计信息
    total_keys = keys_count_func()
    size_str = ""
    if stat_func:
        try:
            stats = stat_func()
            if 'approximate_size' in stats:
                size_str = f", ~{stats['approximate_size']}"
        except Exception:
            pass

    # 标题行
    lines.append(f"{class_name} '{name}' ({total_keys:,} keys{size_str})")
    lines.append("─" * 50)

    if total_keys == 0:
        lines.append("  (empty)")
        return "\n".join(lines)

    # 获取前 n 个键值对
    count = 0
    try:
        for key, value in items_func():
            if count >= n:
                break
            key_str = repr(key)
            if len(key_str) > 20:
                key_str = key_str[:17] + "..."
            value_str = format_value(value, max_len=40)
            lines.append(f"  {key_str:20} → {value_str}")
            count += 1
    except Exception as e:
        lines.append(f"  (error reading data: {e})")
        return "\n".join(lines)

    # 剩余数量提示
    remaining = total_keys - count
    if remaining > 0:
        lines.append(f"  ... and {remaining:,} more keys")

    return "\n".join(lines)


class DisplayMixin:
    """
    统一的展示行为 Mixin

    子类需要实现以下属性/方法：
    - name: str - 数据库名称
    - _closed: bool - 是否已关闭
    - _get_display_info() -> dict - 返回展示信息

    可选实现：
    - items() - 用于 preview()
    - keys_count() 或 __len__() - 用于 preview()
    - stat() - 用于 preview()
    """

    def _get_display_info(self) -> dict:
        """
        返回展示信息（子类必须实现）

        Returns:
            dict 包含以下字段:
            - class_name: str - 类名
            - name: str - 数据库名称
            - location: str - 位置（路径或URL）
            - closed: bool - 是否已关闭
            - extras: dict - 额外参数（如 cache, encrypted 等）
            - tags: list - 标签（如 'encrypted', 'cached'）
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        """
        轻量级标识，零 I/O

        格式: ClassName('name', location='...', extra1=val1, ...)
        """
        info = self._get_display_info()

        if info.get('closed'):
            return f"{info['class_name']}({info['name']!r}, closed=True)"

        parts = [repr(info['name'])]

        if info.get('location'):
            parts.append(f"path={info['location']!r}")

        for k, v in info.get('extras', {}).items():
            if isinstance(v, str):
                parts.append(f"{k}={v!r}")
            else:
                parts.append(f"{k}={v}")

        return f"{info['class_name']}({', '.join(parts)})"

    def __str__(self) -> str:
        """
        友好摘要，零 I/O

        格式: <ClassName 'name' at location [tags]>
        """
        info = self._get_display_info()

        if info.get('closed'):
            return f"<{info['class_name']} {info['name']!r} (closed)>"

        parts = [f"<{info['class_name']} {info['name']!r}"]

        if info.get('location'):
            parts.append(f"at {info['location']}")

        tags = info.get('tags', [])
        if tags:
            parts.append(f"[{', '.join(tags)}]")

        return " ".join(parts) + ">"

    def preview(self, n: int = 10) -> str:
        """
        按需数据预览，显式 I/O

        Args:
            n: 预览的键值对数量

        Returns:
            格式化的预览字符串
        """
        info = self._get_display_info()

        if info.get('closed'):
            return f"<{info['class_name']} {info['name']!r} (closed)>"

        # 获取 items 函数
        items_func = getattr(self, 'items', None)
        if items_func is None:
            return f"<{info['class_name']} {info['name']!r} (preview not supported)>"

        # 获取 keys_count 函数
        keys_count_func = getattr(self, 'keys_count', None)
        if keys_count_func is None:
            keys_count_func = lambda: len(self)

        # 获取 stat 函数
        stat_func = getattr(self, 'stat', None)

        return build_preview(
            items_func=items_func,
            keys_count_func=keys_count_func,
            name=info['name'],
            class_name=info['class_name'],
            n=n,
            stat_func=stat_func
        )

    def _repr_html_(self) -> str:
        """
        Jupyter Notebook HTML 展示

        在 Jupyter 中提供更友好的展示格式
        """
        info = self._get_display_info()

        if info.get('closed'):
            return f"<code style='color: gray;'>&lt;{info['class_name']} {info['name']!r} (closed)&gt;</code>"

        tags_html = ""
        tags = info.get('tags', [])
        if tags:
            tags_html = " ".join(
                f"<span style='background: #e0e0e0; padding: 1px 4px; border-radius: 3px; font-size: 0.8em;'>{t}</span>"
                for t in tags
            )

        return f"""
        <code>
            <b>{info['class_name']}</b>
            '{info['name']}'
            <span style='color: gray;'>at {info.get('location', 'unknown')}</span>
            {tags_html}
        </code>
        """
