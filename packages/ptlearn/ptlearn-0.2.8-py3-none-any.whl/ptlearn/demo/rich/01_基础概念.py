"""
Rich 基础概念
=============
Rich 是一个用于在终端中生成富文本和精美格式的 Python 库
支持 Python 3.7+

本文件涵盖：
- Console 对象基础
- 基本文本样式
- 颜色和背景色
- 文本对齐
"""

from rich.console import Console
from rich.text import Text

console = Console()

# region 示例1: Console 基本使用
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: Console 基本使用")
    print("=" * 50)
    
    # Console 是 Rich 的核心对象，用于输出富文本
    console.print("Hello, [bold magenta]Rich[/bold magenta]!")
    console.print("这是一段普通文本")
    
    # 使用 style 参数设置整体样式
    console.print("这是红色文本", style="red")
    console.print("这是粗体蓝色文本", style="bold blue")
    print()
# endregion

# region 示例2: 内联样式标记
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 内联样式标记")
    print("=" * 50)
    
    # Rich 使用类似 BBCode 的标记语法
    console.print("[bold]粗体[/bold] [italic]斜体[/italic] [underline]下划线[/underline]")
    console.print("[strike]删除线[/strike] [reverse]反色[/reverse]")
    
    # 组合多种样式
    console.print("[bold italic red]粗体斜体红色[/bold italic red]")
    console.print("[yellow on blue]黄色文字蓝色背景[/yellow on blue]")
    print()
# endregion

# region 示例3: 颜色系统
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: 颜色系统")
    print("=" * 50)
    
    # 标准颜色名称
    colors = ["red", "green", "blue", "yellow", "magenta", "cyan", "white"]
    for color in colors:
        console.print(f"[{color}]这是 {color} 颜色[/{color}]")
    
    print()
    
    # 使用 RGB 颜色 (需要终端支持)
    console.print("[rgb(255,128,0)]橙色 RGB(255,128,0)[/rgb(255,128,0)]")
    console.print("[#FF6B6B]十六进制颜色 #FF6B6B[/#FF6B6B]")
    
    # 256 色模式
    console.print("[color(208)]256色模式 color(208)[/color(208)]")
    print()
# endregion

# region 示例4: Text 对象
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: Text 对象")
    print("=" * 50)
    
    # Text 对象提供更精细的文本控制
    text = Text()
    text.append("Hello ", style="bold")
    text.append("World", style="bold red")
    text.append("!", style="bold blue")
    console.print(text)
    
    # 使用 Text.from_markup 解析标记
    text2 = Text.from_markup("[bold cyan]从标记创建[/bold cyan]的文本")
    console.print(text2)
    
    # 高亮特定文本
    text3 = Text("在这段文字中高亮显示关键词")
    text3.highlight_words(["高亮", "关键词"], style="bold yellow")
    console.print(text3)
    print()
# endregion

# region 示例5: 文本对齐和填充
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: 文本对齐和填充")
    print("=" * 50)
    
    # justify 参数控制对齐方式
    console.print("左对齐文本", justify="left")
    console.print("居中对齐文本", justify="center")
    console.print("右对齐文本", justify="right")
    
    print()
    
    # 使用 rule 创建分隔线
    console.rule("[bold red]分隔线标题")
    console.rule()  # 无标题的分隔线
    console.rule("左对齐标题", align="left")
    print()
# endregion
