"""Shared instances - Global singletons for executor and storage."""

from .executor.k6 import K6Executor
from .storage.file import FileStorage

# 全局共享实例（单例模式）
executor = K6Executor()
storage = FileStorage()

