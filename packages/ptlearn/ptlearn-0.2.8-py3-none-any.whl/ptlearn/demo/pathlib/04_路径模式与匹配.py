"""
pathlib 路径模式与匹配
======================
深入了解 glob 模式语法和路径匹配技巧
"""

from pathlib import Path, PurePath

# region 示例1: glob 模式语法
if True:  # 改为 False 可跳过此示例
    """
    glob 模式语法说明:
    - *      匹配任意字符 (不包括路径分隔符)
    - **     匹配任意层级目录
    - ?      匹配单个字符
    - [abc]  匹配方括号内的任意字符
    - [!abc] 匹配不在方括号内的字符
    - [0-9]  匹配数字范围
    """
    p = Path("src/ptlearn/demo")

    print("模式示例:")
    print("  *.py      - 当前目录的 .py 文件")
    print("  **/*.py   - 所有子目录的 .py 文件")
    print("  0?.py     - 01.py, 02.py 等")
    print("  [abc]*.py - a/b/c 开头的 .py 文件")

    # 实际演示
    print("\n匹配 0?_*.py 的文件:")
    for f in p.rglob("0?_*.py"):
        print(f"  {f.relative_to(p)}")
# endregion

# region 示例2: match 方法
if True:  # 改为 False 可跳过此示例
    # match 用于检查路径是否匹配给定模式
    paths = [
        Path("src/main.py"),
        Path("tests/test_main.py"),
        Path("docs/readme.md"),
        Path("src/utils/helper.py"),
    ]

    print("匹配 *.py 的路径:")
    for p in paths:
        if p.match("*.py"):
            print(f"  ✓ {p}")

    print("\n匹配 src/**/*.py 的路径:")
    for p in paths:
        if p.match("src/**/*.py"):
            print(f"  ✓ {p}")

    print("\n匹配 test_*.py 的路径:")
    for p in paths:
        if p.match("test_*.py"):
            print(f"  ✓ {p}")
# endregion

# region 示例3: PurePath - 纯路径操作
if True:  # 改为 False 可跳过此示例
    from pathlib import PurePosixPath, PureWindowsPath

    # PurePath 不访问文件系统，只做路径字符串操作
    # 适合处理远程路径或跨平台路径

    # POSIX 风格路径
    posix = PurePosixPath("/home/user/file.txt")
    print("POSIX 路径:", posix)
    print("  父目录:", posix.parent)
    print("  文件名:", posix.name)

    # Windows 风格路径
    win = PureWindowsPath(r"C:\Users\user\file.txt")
    print("\nWindows 路径:", win)
    print("  驱动器:", win.drive)
    print("  根目录:", win.root)
    print("  各部分:", win.parts)
# endregion

# region 示例4: 路径规范化
if True:  # 改为 False 可跳过此示例
    # 处理包含 . 和 .. 的路径
    messy_path = Path("src/../src/./ptlearn/../ptlearn/demo")

    print("原始路径:", messy_path)
    print("规范化后:", messy_path.resolve())

    # 相对路径计算
    base = Path("/home/user/projects")
    target = Path("/home/user/documents/file.txt")

    # 注意: relative_to 要求 target 必须在 base 下
    # 如果不在，会抛出 ValueError
    try:
        rel = target.relative_to(base)
    except ValueError as e:
        print(f"\n无法计算相对路径: {e}")

    # 正确的例子
    target2 = Path("/home/user/projects/myapp/main.py")
    rel2 = target2.relative_to(base)
    print(f"相对路径: {rel2}")
# endregion

# region 示例5: 路径修改
if True:  # 改为 False 可跳过此示例
    p = Path("/home/user/documents/report.txt")

    # 修改文件名
    new_name = p.with_name("summary.txt")
    print("修改文件名:", new_name)

    # 修改后缀
    new_suffix = p.with_suffix(".md")
    print("修改后缀:", new_suffix)

    # 修改文件名 (保留后缀)
    new_stem = p.with_stem("analysis")
    print("修改 stem:", new_stem)

    # 链式修改
    result = p.with_stem("final").with_suffix(".pdf")
    print("链式修改:", result)
# endregion
