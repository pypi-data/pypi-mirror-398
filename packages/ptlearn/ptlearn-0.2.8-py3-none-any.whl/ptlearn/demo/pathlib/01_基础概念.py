"""
pathlib 基础概念
================
pathlib 是 Python 3.4+ 引入的面向对象的文件系统路径处理模块
相比 os.path，它提供了更直观、更 Pythonic 的 API
"""

from pathlib import Path

# region 示例1: 创建 Path 对象
if True:  # 改为 False 可跳过此示例
    # 多种方式创建 Path 对象
    p1 = Path(".")  # 当前目录
    p2 = Path("/usr/local/bin")  # 绝对路径
    p3 = Path.cwd()  # 当前工作目录
    p4 = Path.home()  # 用户主目录

    print("当前目录:", p1)
    print("绝对路径:", p2)
    print("工作目录:", p3)
    print("主目录:", p4)
# endregion

# region 示例2: 路径拼接 (/ 运算符)
if True:  # 改为 False 可跳过此示例
    # 使用 / 运算符拼接路径，非常直观
    base = Path.home()
    config_path = base / ".config" / "myapp" / "settings.json"

    print("拼接后的路径:", config_path)

    # 也可以使用 joinpath 方法
    another_path = base.joinpath("Documents", "projects")
    print("joinpath 方式:", another_path)
# endregion

# region 示例3: 路径属性
if True:  # 改为 False 可跳过此示例
    p = Path("/home/user/documents/report.txt")

    print("完整路径:", p)
    print("文件名:", p.name)  # report.txt
    print("文件名(无后缀):", p.stem)  # report
    print("后缀:", p.suffix)  # .txt
    print("父目录:", p.parent)  # /home/user/documents
    print("所有父目录:", list(p.parents))  # 逐级向上的所有父目录
    print("各部分:", p.parts)  # ('/', 'home', 'user', 'documents', 'report.txt')
# endregion

# region 示例4: 路径转换
if True:  # 改为 False 可跳过此示例
    p = Path(".")

    # 转换为绝对路径
    print("绝对路径:", p.absolute())
    print("解析路径:", p.resolve())  # 解析符号链接，返回规范化的绝对路径

    # 转换为字符串
    print("字符串形式:", str(p))

    # 转换为 URI
    print("URI 形式:", p.resolve().as_uri())

    # Windows 风格路径 (仅在 Windows 上有意义)
    # print("POSIX 风格:", p.as_posix())
# endregion

# region 示例5: 路径比较与判断
if True:  # 改为 False 可跳过此示例
    p1 = Path("/home/user")
    p2 = Path("/home/user/documents")
    p3 = Path("/home/user")

    # 相等比较
    print("p1 == p3:", p1 == p3)  # True

    # 检查是否为子路径
    print("p2 相对于 p1:", p2.relative_to(p1))  # documents

    # 检查路径是否匹配模式
    p = Path("report.txt")
    print("匹配 *.txt:", p.match("*.txt"))  # True
    print("匹配 *.py:", p.match("*.py"))  # False
# endregion
