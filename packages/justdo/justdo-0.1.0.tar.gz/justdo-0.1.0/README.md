# justdo - Just do it! 🚀

一个用 TDD 方式开发的简单命令行待办事项工具，支持任务优先级管理。

> **Just do it!** - 简单、高效的待办事项管理工具

## 安装

```bash
pip install justdo
```

## 使用方法

### 基础命令

```bash
# 添加任务（默认中等优先级）
jd add "购买牛奶"

# 列出所有任务（按 ID 排序）
jd list

# 标记任务为完成
jd done 1

# 删除任务
jd delete 1

# 清空所有已完成的任务
jd clear
```

### 优先级功能

```bash
# 添加高优先级任务
jd add "紧急任务" -p high
jd add "紧急任务" --priority high

# 添加低优先级任务
jd add "不重要的事" -p low

# 按优先级排序显示（高优先级在前）
jd list --sort-by priority
```

### 优先级说明

| 优先级 | Emoji | 说明 |
|--------|-------|------|
| high | 🔴 | 高优先级（紧急重要） |
| medium | 🟡 | 中优先级（默认） |
| low | 🟢 | 低优先级（可延后） |

### 显示示例

```bash
$ jd add "完成文档" -p high
✓ 已添加任务 [1] 🔴: 完成文档

$ jd add "整理桌面" -p low
✓ 已添加任务 [2] 🟢: 整理桌面

$ jd list --sort-by priority
[1] [ ] 🔴 高优先级任务
[2] [ ] 🟡 中优先级任务
[3] [ ] 🟢 低优先级任务
```

## 技术栈

- Python 3.8+
- pytest（测试框架）
- argparse（命令行解析）
- JSON（数据存储）
- TDD 开发模式

## 开发

```bash
# 克隆仓库
git clone https://github.com/gqy20/todo-cli.git
cd todo-cli

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 查看测试覆盖率
pytest --cov=todo
```

## 项目结构

```
do-it/
├── src/
│   └── todo/
│       ├── __init__.py
│       ├── models.py      # 数据模型（TodoItem）
│       ├── manager.py     # 核心业务逻辑（TodoManager）
│       └── cli.py         # 命令行接口
├── tests/
│   └── unit/
│       ├── test_models.py
│       ├── test_manager.py
│       └── test_cli.py
├── pyproject.toml         # 包配置
├── todo.json              # 数据存储（自动生成）
└── README.md
```

## 功能命令

| 命令 | 说明 |
|------|------|
| `jd add <text> [-p PRIORITY]` | 添加新任务，可指定优先级 |
| `jd list [--sort-by]` | 列出任务，支持按 ID 或优先级排序 |
| `jd done <id>` | 标记指定 ID 的任务为完成 |
| `jd delete <id>` | 删除指定 ID 的任务 |
| `jd clear` | 清除所有已完成的任务 |

## 测试

项目采用 TDD 开发模式，**44 个单元测试全部通过**：

- 数据模型测试（15 个）- 包括优先级功能
- 业务逻辑测试（17 个）- 包括优先级参数
- CLI 命令测试（12 个）- 包括优先级显示和排序

## 为什么叫 justdo？

- ✅ **简洁有力** - 两个音节，朗朗上口
- ✅ **寓意完美** - "Just do it!" 正是待办事项的核心精神
- ✅ **命令简短** - `jd` 两个字母，快速输入
- ✅ **易记易搜** - 用户搜索 "just do" 很容易找到
- ✅ **国际化** - 英语通用，全球用户都能理解

## 链接

- **GitHub**: https://github.com/gqy20/todo-cli
- **PyPI**: https://pypi.org/project/justdo/
- **文档**: http://home.gqy20.top/todo-cli/

## License

MIT
