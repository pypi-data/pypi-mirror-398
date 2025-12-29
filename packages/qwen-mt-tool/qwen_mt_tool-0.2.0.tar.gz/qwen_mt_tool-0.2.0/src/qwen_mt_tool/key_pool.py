# -*- coding: utf-8 -*-
"""
Key 池模块 - 管理 API Key 的并发获取和释放
"""

import threading
import time
from contextlib import contextmanager
from queue import Queue, Empty

from .logging_setup import logger


class KeyPool:
    """
    线程安全的 API Key 池，支持 QPS 限制和独占获取。
    
    特性：
    - 每个 Key 同一时刻只能被一个请求使用
    - 支持 QPS 限制（每个 Key 的请求频率限制）
    - 支持动态移除无效 Key
    """
    
    def __init__(self, api_keys: list, qps: float = 1.0):
        """
        初始化 Key 池。
        
        Args:
            api_keys: API Key 列表
            qps: 每个 Key 的每秒请求数限制（默认 1.0）
        """
        self.qps = qps
        self.min_interval = 1.0 / qps if qps > 0 else 0
        
        # 记录每个 Key 的最后使用时间
        self.last_used = {key: 0.0 for key in api_keys}
        
        # Key 队列（用于独占获取）
        self.keys_queue = Queue()
        for k in api_keys:
            self.keys_queue.put(k)
        
        self._lock = threading.Lock()
        self.active_keys = set(api_keys)

    @property
    def keys(self) -> list:
        """返回当前活跃的 Key 列表。"""
        with self._lock:
            return list(self.active_keys)

    def get_key(self) -> str:
        """已废弃：请使用 acquire() 上下文管理器。"""
        with self.acquire() as key:
            return key

    def remove_key(self, key: str) -> None:
        """
        从池中移除一个 Key（线程安全）。
        
        Args:
            key: 要移除的 API Key
        """
        with self._lock:
            if key in self.active_keys:
                self.active_keys.remove(key)
                if key in self.last_used:
                    del self.last_used[key]
                logger.warning(f"已从池中移除无效 Key: {key}. 剩余 Key 数量: {len(self.active_keys)}")

    @contextmanager
    def acquire(self):
        """
        独占获取一个 Key，并在必要时等待以遵守 QPS 限制。
        
        使用方式：
            with key_pool.acquire() as key:
                # 使用 key 发起请求
                pass
        
        Yields:
            str | None: API Key，如果池为空则返回 None
        """
        key = None
        
        # 循环获取，带超时以避免死锁
        while True:
            try:
                key = self.keys_queue.get(timeout=1.0)
                break
            except Empty:
                with self._lock:
                    if not self.active_keys:
                        # 池已空
                        yield None
                        return
                    # 继续等待

        try:
            # 检查 Key 是否已被移除
            with self._lock:
                if key not in self.active_keys:
                    yield None
                    return

            # 计算等待时间以遵守 QPS 限制
            now = time.time()
            elapsed = now - self.last_used.get(key, 0.0)
            wait_time = self.min_interval - elapsed

            if wait_time > 0:
                time.sleep(wait_time)
                now = time.time()

            self.last_used[key] = now
            yield key
            
        finally:
            # 使用完毕后将 Key 放回队列
            with self._lock:
                if key is not None and key in self.active_keys:
                    self.keys_queue.put(key)
            self.keys_queue.task_done()
