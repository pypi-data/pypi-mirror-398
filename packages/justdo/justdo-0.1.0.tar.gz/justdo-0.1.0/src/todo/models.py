"""数据模型定义

TodoItem - 单个待办事项数据模型
"""

from dataclasses import dataclass, field
from typing import Dict

# 有效的优先级值
VALID_PRIORITIES = {"low", "medium", "high"}

# 优先级到 emoji 的映射
PRIORITY_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
}

# 优先级排序权重
PRIORITY_WEIGHT = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


@dataclass
class TodoItem:
    """待办事项数据模型"""

    id: int
    text: str
    done: bool = False
    priority: str = "medium"

    def __post_init__(self):
        """创建后验证数据"""
        if self.id < 1:
            raise ValueError("ID 必须为正整数")
        if not self.text or not self.text.strip():
            raise ValueError("文本不能为空")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"优先级必须是 {VALID_PRIORITIES} 之一")

    def to_dict(self) -> Dict:
        """转换为字典格式

        Returns:
            包含 id, text, done, priority 的字典
        """
        return {
            "id": self.id,
            "text": self.text,
            "done": self.done,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TodoItem":
        """从字典创建 TodoItem

        Args:
            data: 包含 id, text, done, priority (可选) 的字典

        Returns:
            TodoItem 实例
        """
        return cls(
            id=data["id"],
            text=data["text"],
            done=data.get("done", False),
            priority=data.get("priority", "medium"),
        )

    @property
    def priority_emoji(self) -> str:
        """获取优先级对应的 emoji

        Returns:
            优先级 emoji 字符
        """
        return PRIORITY_EMOJI.get(self.priority, "")

    @property
    def priority_weight(self) -> int:
        """获取优先级排序权重

        Returns:
            优先级权重，用于排序
        """
        return PRIORITY_WEIGHT.get(self.priority, 0)
