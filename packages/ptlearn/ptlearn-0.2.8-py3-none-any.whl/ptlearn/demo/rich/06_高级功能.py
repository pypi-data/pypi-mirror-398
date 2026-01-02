"""
Rich 高级功能
=============
本文件涵盖：
- Live 实时更新显示
- Prompt 交互式输入
- Inspect 对象检查
- Pretty 美化打印
- Console 导出功能
"""

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import inspect
from rich.pretty import pprint, Pretty
from rich.panel import Panel
import time

console = Console()

# region 示例1: Live 实时更新
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: Live 实时更新")
    print("=" * 50)
    
    def generate_table(count):
        """生成动态表格"""
        table = Table(title=f"实时数据 (更新 {count} 次)")
        table.add_column("ID", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("进度", style="yellow")
        
        for i in range(3):
            progress = min(100, (count * 10 + i * 20) % 110)
            status = "完成" if progress >= 100 else "进行中"
            table.add_row(str(i + 1), status, f"{progress}%")
        
        return table
    
    # Live 可以实时更新终端显示
    with Live(generate_table(0), refresh_per_second=4) as live:
        for i in range(10):
            time.sleep(0.3)
            live.update(generate_table(i + 1))
    
    console.print("[green]实时更新演示完成！[/green]")
    print()
# endregion

# region 示例2: Prompt 交互式输入
if False:  # 改为 True 可启用此示例（需要用户输入）
    print("=" * 50)
    print("示例2: Prompt 交互式输入")
    print("=" * 50)
    
    # 基本文本输入
    name = Prompt.ask("请输入你的名字")
    console.print(f"你好, [bold cyan]{name}[/bold cyan]!")
    
    # 带默认值的输入
    color = Prompt.ask("你喜欢的颜色", default="蓝色")
    console.print(f"你选择了: [bold {color}]{color}[/bold {color}]")
    
    # 限制选项的输入
    choice = Prompt.ask("选择一个选项", choices=["A", "B", "C"])
    console.print(f"你选择了: {choice}")
    
    # 整数输入
    age = IntPrompt.ask("请输入你的年龄")
    console.print(f"你的年龄是: {age}")
    
    # 确认输入
    if Confirm.ask("确定要继续吗?"):
        console.print("[green]继续执行...[/green]")
    else:
        console.print("[yellow]已取消[/yellow]")
    
    print()
# endregion

# region 示例3: Inspect 对象检查
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: Inspect 对象检查")
    print("=" * 50)
    
    # 检查一个列表对象
    my_list = [1, 2, 3, "hello", {"key": "value"}]
    console.print("[bold]检查列表对象:[/bold]")
    inspect(my_list, methods=False)
    
    print()
    
    # 检查一个类
    class Person:
        """一个简单的人员类"""
        def __init__(self, name, age):
            self.name = name
            self.age = age
        
        def greet(self):
            """打招呼"""
            return f"Hello, I'm {self.name}"
    
    person = Person("Alice", 30)
    console.print("[bold]检查自定义对象:[/bold]")
    inspect(person, methods=True)
    print()
# endregion

# region 示例4: Pretty 美化打印
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: Pretty 美化打印")
    print("=" * 50)
    
    # 复杂数据结构
    data = {
        "users": [
            {"id": 1, "name": "Alice", "roles": ["admin", "user"]},
            {"id": 2, "name": "Bob", "roles": ["user"]},
        ],
        "settings": {
            "theme": "dark",
            "notifications": True,
            "language": "zh-CN",
        },
        "metadata": {
            "version": "1.0.0",
            "updated": "2024-01-01",
        },
    }
    
    # 使用 pprint 美化输出
    console.print("[bold]使用 pprint:[/bold]")
    pprint(data, expand_all=True)
    
    print()
    
    # 在面板中使用 Pretty
    console.print(Panel(Pretty(data), title="数据预览"))
    print()
# endregion

# region 示例5: Console 导出功能
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: Console 导出功能")
    print("=" * 50)
    
    # 创建一个用于记录的 Console
    from io import StringIO
    
    # 导出为文本
    record_console = Console(record=True, width=60)
    record_console.print("[bold red]错误:[/bold red] 文件未找到")
    record_console.print("[bold yellow]警告:[/bold yellow] 配置已过期")
    record_console.print("[bold green]成功:[/bold green] 操作完成")
    
    # 导出为纯文本
    text_output = record_console.export_text()
    console.print("[bold]导出的纯文本:[/bold]")
    console.print(Panel(text_output))
    
    # 也可以导出为 HTML（这里只展示方法）
    # html_output = record_console.export_html()
    
    console.print("[dim]提示: 还可以使用 export_html() 导出为 HTML 格式[/dim]")
    print()
# endregion

# region 示例6: 控制台尺寸和样式
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例6: 控制台尺寸和样式")
    print("=" * 50)
    
    # 获取终端尺寸
    console.print(f"[cyan]终端宽度:[/cyan] {console.width}")
    console.print(f"[cyan]终端高度:[/cyan] {console.height}")
    console.print(f"[cyan]是否为终端:[/cyan] {console.is_terminal}")
    console.print(f"[cyan]颜色系统:[/cyan] {console.color_system}")
    
    print()
    
    # 创建固定宽度的 Console
    narrow_console = Console(width=40)
    narrow_console.print(Panel(
        "这是一个固定宽度为40的控制台输出，文本会自动换行以适应宽度限制。",
        title="窄控制台"
    ))
    print()
# endregion
