"""applab/__init__.py：包入口模块.

提供包的入口函数，并导入包中的核心功能模块。
"""

from .core import say_goodbye, say_hello  # noqa: F401 忽略导入未使用警告

__all__ = [
    "say_goodbye",
    "say_hello",
]
