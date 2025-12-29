"""applab/core.py：包的功能实现模块.

提供核心业务逻辑相关的工具函数，当前包含向指定用户打招呼的功能。
"""


# core.py：包的功能实现模块
def say_hello(name: str) -> str:
    """向指定名字的人打招呼."""
    return f"Hello, {name}! 这是根目录包结构的示例"


def say_goodbye(name: str) -> str:
    """向指定名字的人说再见."""
    return f"Goodbye, {name}! 欢迎下次使用"
