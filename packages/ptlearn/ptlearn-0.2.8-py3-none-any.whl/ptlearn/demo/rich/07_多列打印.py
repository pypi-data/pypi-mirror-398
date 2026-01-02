"""
多列打印
========
展示如何在 Panel 中使用 Columns 实现大列表的多列布局显示
"""

from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

console = Console()

# region 示例1: 基础多列打印
if True:  # 改为 False 可跳过此示例
    # 创建一个较大的列表
    items = [f"项目 {i:03d}" for i in range(1, 51)]
    
    # 使用 Columns 进行多列布局
    columns = Columns(items, equal=True, expand=True)
    
    # 将多列内容放入 Panel 中
    panel = Panel(columns, title="基础多列打印", border_style="green")
    console.print(panel)
# endregion

# region 示例2: 带样式的多列打印
if True:  # 改为 False 可跳过此示例
    # 创建带颜色的列表项
    colors = ["red", "green", "blue", "yellow", "magenta", "cyan"]
    styled_items = [
        Text(f"元素 {i:03d}", style=colors[i % len(colors)])
        for i in range(1, 61)
    ]
    
    # 多列布局，指定列数
    columns = Columns(styled_items, equal=True, expand=True)
    panel = Panel(columns, title="带样式的多列打印", border_style="blue")
    console.print(panel)
# endregion

# region 示例3: 自定义列宽的多列打印
if True:  # 改为 False 可跳过此示例
    # 创建不同长度的列表项
    data = [f"数据项_{i}" for i in range(1, 81)]
    
    # column_first=True 表示先填充列再填充行
    columns = Columns(data, equal=True, expand=True, column_first=True)
    panel = Panel(
        columns,
        title="列优先填充模式",
        subtitle="共 80 个项目",
        border_style="magenta"
    )
    console.print(panel)
# endregion

# region 示例4: Panel 嵌套实现分组多列
if True:  # 改为 False 可跳过此示例
    # 将大列表分组，每组用小 Panel 包裹
    all_items = [f"Item-{i:04d}" for i in range(1, 101)]
    group_size = 20
    
    # 分组并创建小 Panel
    panels = []
    for i in range(0, len(all_items), group_size):
        group = all_items[i:i + group_size]
        group_columns = Columns(group, equal=True)
        mini_panel = Panel(
            group_columns,
            title=f"分组 {i // group_size + 1}",
            border_style="cyan"
        )
        panels.append(mini_panel)
    
    # 将所有小 Panel 放入大 Panel
    outer_columns = Columns(panels, equal=True, expand=True)
    outer_panel = Panel(
        outer_columns,
        title="分组多列打印 (100 个项目)",
        border_style="yellow"
    )
    console.print(outer_panel)
# endregion

# region 示例5: 使用 renderables 列表实现复杂布局
if True:  # 改为 False 可跳过此示例
    from rich.table import Table
    
    # 创建大量数据
    large_list = [f"#{i:05d}" for i in range(1, 201)]
    
    # 手动分成多列（每列 25 个）
    col_count = 8
    items_per_col = len(large_list) // col_count
    
    # 创建表格实现精确的列控制
    table = Table(show_header=False, box=None, padding=(0, 2))
    for _ in range(col_count):
        table.add_column()
    
    # 按行填充数据
    for row_idx in range(items_per_col):
        row_data = [
            large_list[col * items_per_col + row_idx]
            for col in range(col_count)
            if col * items_per_col + row_idx < len(large_list)
        ]
        table.add_row(*row_data)
    
    panel = Panel(
        table,
        title="精确列控制 (200 个项目，8 列)",
        border_style="red"
    )
    console.print(panel)
# endregion
