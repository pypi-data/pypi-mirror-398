"""
Rich 表格与面板
===============
本文件涵盖：
- Table 表格创建与样式
- Panel 面板组件
- 表格高级配置
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# region 示例1: 基础表格
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 基础表格")
    print("=" * 50)
    
    # 创建表格并添加列
    table = Table(title="用户列表")
    table.add_column("ID", style="cyan", justify="center")
    table.add_column("姓名", style="magenta")
    table.add_column("邮箱", style="green")
    
    # 添加行数据
    table.add_row("1", "张三", "zhangsan@example.com")
    table.add_row("2", "李四", "lisi@example.com")
    table.add_row("3", "王五", "wangwu@example.com")
    
    console.print(table)
    print()
# endregion

# region 示例2: 表格样式定制
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 表格样式定制")
    print("=" * 50)
    
    # 使用不同的边框样式
    table = Table(title="边框样式演示", box=box.ROUNDED)
    table.add_column("样式", style="cyan")
    table.add_column("说明", style="yellow")
    
    table.add_row("ROUNDED", "圆角边框")
    table.add_row("SQUARE", "方角边框")
    table.add_row("MINIMAL", "极简边框")
    
    console.print(table)
    print()
    
    # 带有表头和表尾样式的表格
    table2 = Table(
        title="[bold]销售报表[/bold]",
        caption="数据截止到2024年",
        box=box.DOUBLE_EDGE,
        header_style="bold white on blue",
        row_styles=["", "dim"],  # 交替行样式
    )
    table2.add_column("产品", justify="left")
    table2.add_column("销量", justify="right")
    table2.add_column("金额", justify="right", style="green")
    
    table2.add_row("产品A", "100", "¥10,000")
    table2.add_row("产品B", "200", "¥25,000")
    table2.add_row("产品C", "150", "¥18,000")
    table2.add_row("产品D", "80", "¥9,600")
    
    console.print(table2)
    print()
# endregion

# region 示例3: Panel 面板
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: Panel 面板")
    print("=" * 50)
    
    # 基础面板
    console.print(Panel("这是一个简单的面板"))
    
    # 带标题的面板
    console.print(Panel("面板内容", title="标题", subtitle="副标题"))
    
    # 自定义样式面板
    console.print(Panel(
        "[bold yellow]重要提示[/bold yellow]\n请注意保存您的工作！",
        title="[red]警告[/red]",
        border_style="red",
        box=box.DOUBLE,
    ))
    print()
# endregion

# region 示例4: 面板中嵌套表格
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: 面板中嵌套表格")
    print("=" * 50)
    
    # 创建内部表格
    inner_table = Table(show_header=True, box=box.SIMPLE)
    inner_table.add_column("配置项", style="cyan")
    inner_table.add_column("值", style="green")
    
    inner_table.add_row("主机", "localhost")
    inner_table.add_row("端口", "8080")
    inner_table.add_row("调试模式", "开启")
    
    # 将表格放入面板
    console.print(Panel(
        inner_table,
        title="[bold]服务器配置[/bold]",
        border_style="blue",
    ))
    print()
# endregion

# region 示例5: 表格边框样式一览
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: 常用边框样式一览")
    print("=" * 50)
    
    box_styles = [
        ("ASCII", box.ASCII),
        ("SQUARE", box.SQUARE),
        ("ROUNDED", box.ROUNDED),
        ("MINIMAL", box.MINIMAL),
        ("SIMPLE", box.SIMPLE),
        ("DOUBLE", box.DOUBLE),
    ]
    
    for name, style in box_styles:
        table = Table(title=f"{name} 样式", box=style, width=40)
        table.add_column("A")
        table.add_column("B")
        table.add_row("1", "2")
        console.print(table)
        print()
# endregion
