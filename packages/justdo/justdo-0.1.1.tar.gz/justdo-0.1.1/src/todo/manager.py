"""TodoManager - 核心业务逻辑

管理待办事项的增删改查和持久化
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from .models import TodoItem


class TodoManager:
    """待办事项管理器"""

    def __init__(self, filepath: str | None = None):
        """初始化管理器

        Args:
            filepath: 数据文件路径，默认 ~/.jd/todo.json
        """
        if filepath is None:
            # 使用用户主目录下的 .jd 目录
            config_dir = Path.home() / ".jd"
            config_dir.mkdir(exist_ok=True)
            filepath = str(config_dir / "todo.json")

        self.filepath = Path(filepath)
        self.todos: List[TodoItem] = []
        self._next_id: int = 1
        self._load()

    def _load(self) -> None:
        """从文件加载数据"""
        if self.filepath.exists():
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.todos = [TodoItem.from_dict(item) for item in data.get("todos", [])]

            # 更新 next_id 为最大 ID + 1
            if self.todos:
                self._next_id = max(todo.id for todo in self.todos) + 1

    def add(self, text: str, priority: str = "medium") -> TodoItem:
        """添加新任务

        Args:
            text: 任务文本
            priority: 优先级 (low/medium/high)，默认 medium

        Returns:
            新创建的 TodoItem

        Raises:
            ValueError: 文本为空或优先级无效时
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")

        todo = TodoItem(
            id=self._next_id,
            text=text.strip(),
            done=False,
            priority=priority,
        )
        self.todos.append(todo)
        self._next_id += 1
        self.save()
        return todo

    def list(self) -> List[TodoItem]:
        """列出所有任务

        Returns:
            TodoItem 列表
        """
        return self.todos.copy()

    def mark_done(self, todo_id: int) -> None:
        """标记任务为完成

        Args:
            todo_id: 任务 ID

        Raises:
            ValueError: 任务不存在时
        """
        todo = self._find_todo(todo_id)
        if todo is None:
            raise ValueError(f"任务不存在: ID {todo_id}")

        todo.done = True
        self.save()

    def delete(self, todo_id: int) -> None:
        """删除任务

        Args:
            todo_id: 任务 ID

        Raises:
            ValueError: 任务不存在时
        """
        todo = self._find_todo(todo_id)
        if todo is None:
            raise ValueError(f"任务不存在: ID {todo_id}")

        self.todos.remove(todo)
        self.save()

    def clear(self) -> None:
        """清除所有已完成的任务"""
        self.todos = [todo for todo in self.todos if not todo.done]
        self.save()

    def save(self) -> None:
        """保存数据到文件"""
        data = {
            "todos": [todo.to_dict() for todo in self.todos]
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _find_todo(self, todo_id: int) -> Optional[TodoItem]:
        """查找任务

        Args:
            todo_id: 任务 ID

        Returns:
            找到的 TodoItem 或 None
        """
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None
