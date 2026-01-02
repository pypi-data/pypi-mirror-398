"""
Rich 进度条与状态
=================
本文件涵盖：
- Progress 进度条
- Spinner 加载动画
- Status 状态显示
- track 快捷函数
"""

import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.progress import track

console = Console()

# region 示例1: track 快捷进度条
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: track 快捷进度条")
    print("=" * 50)
    
    # track 是最简单的进度条用法
    items = range(10)
    for item in track(items, description="处理中..."):
        time.sleep(0.1)  # 模拟耗时操作
    
    console.print("[green]处理完成！[/green]")
    print()
# endregion

# region 示例2: Progress 上下文管理器
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: Progress 上下文管理器")
    print("=" * 50)
    
    # 使用 Progress 可以更精细地控制进度条
    with Progress() as progress:
        task = progress.add_task("[cyan]下载中...", total=100)
        
        while not progress.finished:
            progress.update(task, advance=5)
            time.sleep(0.05)
    
    console.print("[green]下载完成！[/green]")
    print()
# endregion

# region 示例3: 多任务进度条
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: 多任务进度条")
    print("=" * 50)
    
    # 同时显示多个进度条
    with Progress() as progress:
        task1 = progress.add_task("[red]任务1", total=100)
        task2 = progress.add_task("[green]任务2", total=100)
        task3 = progress.add_task("[blue]任务3", total=100)
        
        while not progress.finished:
            progress.update(task1, advance=3)
            progress.update(task2, advance=2)
            progress.update(task3, advance=1)
            time.sleep(0.02)
    
    console.print("[bold green]所有任务完成！[/bold green]")
    print()
# endregion

# region 示例4: 自定义进度条样式
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: 自定义进度条样式")
    print("=" * 50)
    
    # 自定义进度条的列组件
    custom_progress = Progress(
        SpinnerColumn(),                    # 旋转动画
        TextColumn("[bold blue]{task.description}"),  # 任务描述
        BarColumn(bar_width=40),            # 进度条
        TaskProgressColumn(),               # 百分比
        TextColumn("[cyan]{task.completed}/{task.total}"),  # 完成数/总数
    )
    
    with custom_progress:
        task = custom_progress.add_task("安装依赖", total=50)
        for _ in range(50):
            custom_progress.update(task, advance=1)
            time.sleep(0.03)
    
    console.print("[green]安装完成！[/green]")
    print()
# endregion

# region 示例5: Status 状态指示器
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: Status 状态指示器")
    print("=" * 50)
    
    # Status 用于显示不确定时长的操作状态
    with console.status("[bold green]正在连接服务器...") as status:
        time.sleep(1)
        status.update("[bold yellow]正在验证身份...")
        time.sleep(1)
        status.update("[bold cyan]正在加载数据...")
        time.sleep(1)
    
    console.print("[bold green]✓ 操作完成！[/bold green]")
    print()
# endregion

# region 示例6: 不同的 Spinner 样式
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例6: 不同的 Spinner 样式")
    print("=" * 50)
    
    spinners = ["dots", "line", "dots12", "arrow3", "bouncingBar"]
    
    for spinner in spinners:
        with console.status(f"[cyan]Spinner: {spinner}", spinner=spinner):
            time.sleep(1)
        console.print(f"[green]✓[/green] {spinner} 演示完成")
    
    print()
# endregion
