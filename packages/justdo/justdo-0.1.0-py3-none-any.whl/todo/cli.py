"""CLI 命令行接口

提供命令行参数解析和用户交互
"""

import sys
import argparse
from .manager import TodoManager


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="Todo CLI - 命令行待办事项工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # add 命令
    add_parser = subparsers.add_parser("add", help="添加新任务")
    add_parser.add_argument("text", help="任务文本")
    add_parser.add_argument(
        "-p", "--priority",
        choices=["low", "medium", "high"],
        default="medium",
        help="优先级 (low/medium/high，默认 medium)"
    )

    # list 命令
    list_parser = subparsers.add_parser("list", help="列出所有任务")
    list_parser.add_argument(
        "--sort-by",
        choices=["id", "priority"],
        default="id",
        help="排序方式 (id/priority，默认 id)"
    )

    # done 命令
    done_parser = subparsers.add_parser("done", help="标记任务为完成")
    done_parser.add_argument("id", type=int, help="任务 ID")

    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除任务")
    delete_parser.add_argument("id", type=int, help="任务 ID")

    # clear 命令
    subparsers.add_parser("clear", help="清除所有已完成任务")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = TodoManager()

    try:
        if args.command == "add":
            # CLI 层处理空格
            text = args.text.strip()
            todo = manager.add(text, priority=args.priority)
            emoji = todo.priority_emoji
            print(f"✓ 已添加任务 [{todo.id}] {emoji}: {todo.text}")

        elif args.command == "list":
            todos = manager.list()
            if not todos:
                print("暂无任务")
            else:
                # 按指定方式排序
                if args.sort_by == "priority":
                    todos = sorted(todos, key=lambda t: (-t.priority_weight, t.id))
                else:  # sort_by == "id"
                    todos = sorted(todos, key=lambda t: t.id)

                for todo in todos:
                    status = "✓" if todo.done else " "
                    emoji = todo.priority_emoji
                    print(f"[{todo.id}] [{status}] {emoji} {todo.text}")

        elif args.command == "done":
            manager.mark_done(args.id)
            print(f"✓ 任务 [{args.id}] 已标记为完成")

        elif args.command == "delete":
            manager.delete(args.id)
            print(f"✓ 任务 [{args.id}] 已删除")

        elif args.command == "clear":
            manager.clear()
            print("✓ 已清除所有已完成任务")

    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
