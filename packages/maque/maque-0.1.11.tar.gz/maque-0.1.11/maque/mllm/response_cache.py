#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM 响应缓存模块

使用 FlaxKV2 作为存储后端，提供高性能缓存。
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from flaxkv2 import FlaxKV
from loguru import logger

from .token_counter import messages_hash


DEFAULT_CACHE_DIR = os.path.expanduser("~/.cache/maque/llm_response")


@dataclass
class ResponseCacheConfig:
    """
    响应缓存配置

    Attributes:
        enabled: 是否启用缓存
        cache_dir: 缓存目录
        ttl: 缓存过期时间(秒)，0 表示永不过期
    """
    enabled: bool = False
    cache_dir: str = DEFAULT_CACHE_DIR
    ttl: int = 86400  # 24小时

    @classmethod
    def disabled(cls) -> "ResponseCacheConfig":
        """禁用缓存"""
        return cls(enabled=False)

    @classmethod
    def default(cls) -> "ResponseCacheConfig":
        """默认配置：禁用缓存"""
        return cls(enabled=False)

    @classmethod
    def with_ttl(cls, ttl: int = 3600, cache_dir: str = None) -> "ResponseCacheConfig":
        """启用缓存，自定义 TTL（秒）"""
        return cls(
            enabled=True,
            ttl=ttl,
            cache_dir=cache_dir or DEFAULT_CACHE_DIR,
        )

    @classmethod
    def persistent(cls, cache_dir: str = DEFAULT_CACHE_DIR) -> "ResponseCacheConfig":
        """持久缓存：永不过期"""
        return cls(enabled=True, cache_dir=cache_dir, ttl=0)


class ResponseCache:
    """
    LLM 响应缓存

    使用 FlaxKV2 存储，支持 TTL 过期、高性能读写。
    """

    def __init__(self, config: Optional[ResponseCacheConfig] = None):
        self.config = config or ResponseCacheConfig.disabled()
        self._stats = {"hits": 0, "misses": 0}
        self._db: Optional[FlaxKV] = None

        if self.config.enabled:
            self._db = FlaxKV(
                "llm_cache",
                self.config.cache_dir,
                default_ttl=self.config.ttl if self.config.ttl > 0 else None,
                read_cache_size=10000,
                write_buffer_size=100,
                async_flush=True,
            )

    def _make_key(self, messages: List[Dict], model: str, **kwargs) -> str:
        """生成缓存键"""
        return messages_hash(messages, model, **kwargs)

    def get(
        self,
        messages: List[Dict],
        model: str = "",
        **kwargs
    ) -> Optional[Any]:
        """
        获取缓存的响应

        Args:
            messages: 消息列表
            model: 模型名称
            **kwargs: 其他参数 (temperature, max_tokens 等)

        Returns:
            缓存的响应，未命中返回 None
        """
        if self._db is None:
            return None

        cache_key = self._make_key(messages, model, **kwargs)
        result = self._db.get(cache_key)

        if result is not None:
            self._stats["hits"] += 1
        else:
            self._stats["misses"] += 1

        return result

    def set(
        self,
        messages: List[Dict],
        response: Any,
        model: str = "",
        **kwargs
    ) -> None:
        """
        存储响应到缓存

        Args:
            messages: 消息列表
            response: API 响应
            model: 模型名称
            **kwargs: 其他参数
        """
        if self._db is None:
            return

        cache_key = self._make_key(messages, model, **kwargs)
        self._db[cache_key] = response

    def get_batch(
        self,
        messages_list: List[List[Dict]],
        model: str = "",
        **kwargs
    ) -> tuple[List[Optional[Any]], List[int]]:
        """
        批量获取缓存

        Returns:
            (cached_responses, uncached_indices)
        """
        cached = []
        uncached_indices = []

        for i, messages in enumerate(messages_list):
            result = self.get(messages, model, **kwargs)
            cached.append(result)
            if result is None:
                uncached_indices.append(i)

        return cached, uncached_indices

    def set_batch(
        self,
        messages_list: List[List[Dict]],
        responses: List[Any],
        model: str = "",
        **kwargs
    ) -> None:
        """批量存储缓存"""
        for messages, response in zip(messages_list, responses):
            if response is not None:
                self.set(messages, response, model, **kwargs)

    def clear(self) -> int:
        """清空缓存"""
        if self._db is None:
            return 0
        keys = list(self._db.keys())
        count = len(keys)
        for key in keys:
            del self._db[key]
        return count

    def close(self):
        """关闭缓存"""
        if self._db is not None:
            self._db.close()
            self._db = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def stats(self) -> Dict[str, Any]:
        """返回缓存统计"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        return {
            **self._stats,
            "total": total,
            "hit_rate": round(hit_rate, 4),
        }
