"""
pathlib 目录遍历
================
pathlib 提供了强大的目录遍历和文件搜索功能
支持 glob 模式匹配，比 os.walk 更加简洁
"""

from pathlib import Path

# region 示例1: iterdir - 遍历目录内容
if True:  # 改为 False 可跳过此示例
    p = Path(".")

    print("当前目录内容:")
    for item in p.iterdir():
        item_type = "📁" if item.is_dir() else "📄"
        print(f"  {item_type} {item.name}")
# endregion

# region 示例2: glob - 模式匹配
if True:  # 改为 False 可跳过此示例
    p = Path("src/ptlearn/demo")

    # 匹配当前目录下的所有 .py 文件
    print("当前目录的 .py 文件:")
    for py_file in p.glob("*.py"):
        print(f"  {py_file.name}")

    # 匹配特定模式
    print("\n以数字开头的 .py 文件 (当前目录):")
    for py_file in p.glob("[0-9]*.py"):
        print(f"  {py_file.name}")
# endregion

# region 示例3: rglob - 递归匹配
if True:  # 改为 False 可跳过此示例
    p = Path("src/ptlearn/demo")

    # 递归查找所有 .py 文件
    print("递归查找所有 .py 文件:")
    py_files = list(p.rglob("*.py"))
    print(f"  共找到 {len(py_files)} 个文件")

    # 显示前 5 个
    for f in py_files[:5]:
        print(f"  {f.relative_to(p)}")
    if len(py_files) > 5:
        print(f"  ... 还有 {len(py_files) - 5} 个文件")
# endregion

# region 示例4: glob 高级模式
if True:  # 改为 False 可跳过此示例
    p = Path("src/ptlearn/demo")

    # ** 匹配任意层级目录
    print("使用 ** 匹配:")
    for f in p.glob("**/01_*.py"):
        print(f"  {f.relative_to(p)}")

    # 匹配多种后缀 (需要多次调用)
    print("\n查找配置文件 (.json, .yaml, .toml):")
    config_patterns = ["**/*.json", "**/*.yaml", "**/*.toml"]
    for pattern in config_patterns:
        for f in Path(".").glob(pattern):
            print(f"  {f}")
# endregion

# region 示例5: 过滤和排序
if True:  # 改为 False 可跳过此示例
    p = Path("src/ptlearn/demo")

    # 只获取目录
    print("子目录列表:")
    dirs = [d for d in p.iterdir() if d.is_dir()]
    for d in sorted(dirs):
        print(f"  📁 {d.name}")

    # 按修改时间排序文件
    print("\n最近修改的 5 个 .py 文件:")
    py_files = list(p.rglob("*.py"))
    py_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    for f in py_files[:5]:
        print(f"  {f.relative_to(p)}")

    # 按文件大小过滤
    print("\n大于 1KB 的文件:")
    large_files = [f for f in p.rglob("*.py") if f.stat().st_size > 1024]
    for f in large_files[:5]:
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name}: {size_kb:.1f} KB")
# endregion
