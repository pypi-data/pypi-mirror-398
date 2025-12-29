"""Todo CLI Application

一个简单的命令行待办事项工具
"""

from .models import TodoItem
from .manager import TodoManager
from .cli import main

__version__ = "1.0.0"
__all__ = ["TodoItem", "TodoManager", "main"]
