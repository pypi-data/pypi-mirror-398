"""
Rich 树形结构与布局
===================
本文件涵盖：
- Tree 树形结构
- Columns 列布局
- Group 分组
- Layout 高级布局
"""

from rich.console import Console, Group
from rich.tree import Tree
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text

console = Console()

# region 示例1: 基础树形结构
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 基础树形结构")
    print("=" * 50)
    
    # 创建树的根节点
    tree = Tree("[bold cyan]项目结构[/bold cyan]")
    
    # 添加子节点
    src = tree.add("[bold yellow]src/[/bold yellow]")
    src.add("[green]main.py[/green]")
    src.add("[green]utils.py[/green]")
    
    tests = tree.add("[bold yellow]tests/[/bold yellow]")
    tests.add("[green]test_main.py[/green]")
    
    tree.add("[dim]README.md[/dim]")
    tree.add("[dim]pyproject.toml[/dim]")
    
    console.print(tree)
    print()
# endregion

# region 示例2: 带图标的树形结构
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 带图标的树形结构")
    print("=" * 50)
    
    tree = Tree("📁 [bold]my_project[/bold]", guide_style="bold bright_blue")
    
    # 源代码目录
    src = tree.add("📁 [yellow]src[/yellow]")
    src.add("🐍 [green]app.py[/green]")
    src.add("🐍 [green]config.py[/green]")
    
    models = src.add("📁 [yellow]models[/yellow]")
    models.add("🐍 [green]user.py[/green]")
    models.add("🐍 [green]product.py[/green]")
    
    # 配置文件
    tree.add("📄 [dim].gitignore[/dim]")
    tree.add("📄 [dim]requirements.txt[/dim]")
    tree.add("📖 [blue]README.md[/blue]")
    
    console.print(tree)
    print()
# endregion

# region 示例3: Columns 列布局
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: Columns 列布局")
    print("=" * 50)
    
    # 创建多个面板
    panels = [
        Panel("[red]红色面板[/red]", title="1"),
        Panel("[green]绿色面板[/green]", title="2"),
        Panel("[blue]蓝色面板[/blue]", title="3"),
        Panel("[yellow]黄色面板[/yellow]", title="4"),
    ]
    
    # 使用 Columns 自动排列
    console.print(Columns(panels))
    print()
    
    # 指定列数
    console.print("[bold]指定等宽列:[/bold]")
    console.print(Columns(panels, equal=True, expand=True))
    print()
# endregion

# region 示例4: Group 分组渲染
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: Group 分组渲染")
    print("=" * 50)
    
    # Group 可以将多个可渲染对象组合在一起
    from rich.table import Table
    
    # 创建一个表格
    table = Table(title="数据表")
    table.add_column("名称")
    table.add_column("值")
    table.add_row("A", "100")
    table.add_row("B", "200")
    
    # 创建一个树
    tree = Tree("[bold]相关文件[/bold]")
    tree.add("data.csv")
    tree.add("config.json")
    
    # 将它们组合到一个面板中
    group = Group(table, "", tree)  # 空字符串作为间隔
    console.print(Panel(group, title="[bold cyan]报告[/bold cyan]"))
    print()
# endregion

# region 示例5: 动态生成树形结构
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: 动态生成树形结构")
    print("=" * 50)
    
    # 模拟一个嵌套的数据结构
    data = {
        "用户信息": {
            "基本信息": {
                "姓名": "张三",
                "年龄": 25,
            },
            "联系方式": {
                "邮箱": "zhangsan@example.com",
                "电话": "138****1234",
            },
        },
        "订单列表": ["订单001", "订单002", "订单003"],
    }
    
    def build_tree(data, tree):
        """递归构建树形结构"""
        if isinstance(data, dict):
            for key, value in data.items():
                branch = tree.add(f"[cyan]{key}[/cyan]")
                build_tree(value, branch)
        elif isinstance(data, list):
            for item in data:
                tree.add(f"[green]{item}[/green]")
        else:
            tree.add(f"[yellow]{data}[/yellow]")
    
    root = Tree("[bold]数据结构[/bold]")
    build_tree(data, root)
    console.print(root)
    print()
# endregion

# region 示例6: 文本列表布局
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例6: 文本列表布局")
    print("=" * 50)
    
    # 创建一组带样式的文本
    items = [
        Text("Python", style="bold red"),
        Text("JavaScript", style="bold yellow"),
        Text("Go", style="bold cyan"),
        Text("Rust", style="bold magenta"),
        Text("Java", style="bold green"),
        Text("C++", style="bold blue"),
        Text("Ruby", style="bold red"),
        Text("Swift", style="bold orange1"),
    ]
    
    console.print("[bold]编程语言列表:[/bold]")
    console.print(Columns(items, equal=True, expand=True))
    print()
# endregion
