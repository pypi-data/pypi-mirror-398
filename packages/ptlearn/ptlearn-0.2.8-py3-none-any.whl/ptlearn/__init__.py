import os
import subprocess
import sys
from pathlib import Path

import fire
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter




def run():
    # region 扫描 demo 目录下的所有 py 文件
    demo_dir = Path(__file__).parent / "demo"
    
    if not demo_dir.exists():
        print(f"错误: demo 目录不存在 ({demo_dir})")
        return
    
    # 递归扫描所有 .py 文件
    py_files = []
    for py_file in demo_dir.rglob("*.py"):
        # 排除 __pycache__ 和 __init__.py
        if "__pycache__" not in str(py_file) and py_file.name != "__init__.py":
            # 存储相对于 demo 目录的路径
            relative_path = py_file.relative_to(demo_dir)
            py_files.append((str(relative_path), str(py_file)))
    
    if not py_files:
        print("未找到任何示例文件")
        return
    # endregion
    
    # region 使用 prompt-toolkit 让用户选择文件
    # 创建文件选项列表(显示相对路径)
    file_choices = [path for path, _ in py_files]
    
    # 创建模糊补全器
    completer = FuzzyCompleter(WordCompleter(file_choices, ignore_case=True))
    
    try:
        selected = prompt(
            "请选择要执行的示例文件: ",
            completer=completer,
            complete_while_typing=True
        )
        
        # 查找选中的完整路径
        selected_file = None
        for rel_path, full_path in py_files:
            if rel_path == selected:
                selected_file = full_path
                break
        
        if not selected_file:
            print(f"错误: 未找到文件 '{selected}'")
            return
    except (KeyboardInterrupt, EOFError):
        print("\n操作已取消")
        return
    # endregion
    
    # region 执行用户选择的文件
    print(f"\n正在执行: {selected}")
    print("-" * 50)
    
    try:
        # 使用当前 Python 解释器执行文件
        result = subprocess.run(
            [sys.executable, selected_file],
            cwd=demo_dir.parent.parent.parent,  # 项目根目录
            check=False
        )
        
        print("-" * 50)
        if result.returncode == 0:
            print("执行完成")
        else:
            print(f"执行失败，退出码: {result.returncode}")
    except Exception as e:
        print(f"执行出错: {str(e)}")
    # endregion



def main() -> None:
    try:
        fire.Fire(run)
    except KeyboardInterrupt:
        print("\n操作已取消")
        exit(0)
    # except Exception as e:
    #     print(f"\n程序执行出错: {str(e)}")
    #     print("请检查您的输入参数或网络连接")
    #     exit(1)