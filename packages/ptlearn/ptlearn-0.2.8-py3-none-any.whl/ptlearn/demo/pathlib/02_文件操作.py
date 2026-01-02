"""
pathlib 文件操作
================
pathlib 提供了便捷的文件读写和操作方法
无需再使用 open() 函数或 os 模块的繁琐操作
"""

from pathlib import Path
import tempfile

# region 示例1: 文件读写
if True:  # 改为 False 可跳过此示例
    # 创建临时目录进行演示
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "test.txt"

        # 写入文本
        p.write_text("Hello, pathlib!\n第二行内容", encoding="utf-8")
        print("文件已写入:", p)

        # 读取文本
        content = p.read_text(encoding="utf-8")
        print("读取内容:", content)

        # 写入字节
        binary_file = Path(tmpdir) / "data.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03")
        print("字节内容:", binary_file.read_bytes())
# endregion

# region 示例2: 文件存在性检查
if True:  # 改为 False 可跳过此示例
    p = Path(".")

    print("路径存在:", p.exists())
    print("是文件:", p.is_file())
    print("是目录:", p.is_dir())
    print("是符号链接:", p.is_symlink())

    # 检查不存在的路径
    fake = Path("/this/path/does/not/exist")
    print("不存在的路径:", fake.exists())
# endregion

# region 示例3: 创建和删除
if True:  # 改为 False 可跳过此示例
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # 创建目录 (mkdir)
        new_dir = base / "level1" / "level2" / "level3"
        new_dir.mkdir(parents=True, exist_ok=True)  # parents=True 递归创建
        print("目录已创建:", new_dir.exists())

        # 创建文件
        new_file = new_dir / "test.txt"
        new_file.touch()  # 创建空文件，类似 Unix 的 touch 命令
        print("文件已创建:", new_file.exists())

        # 删除文件
        new_file.unlink()
        print("文件已删除:", not new_file.exists())

        # 删除空目录
        new_dir.rmdir()
        print("目录已删除:", not new_dir.exists())
# endregion

# region 示例4: 重命名和移动
if True:  # 改为 False 可跳过此示例
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # 创建原始文件
        original = base / "original.txt"
        original.write_text("原始内容")

        # 重命名
        renamed = original.rename(base / "renamed.txt")
        print("重命名后:", renamed.name)

        # 替换 (如果目标存在则覆盖)
        target = base / "target.txt"
        target.write_text("将被覆盖")
        renamed.replace(target)
        print("替换后内容:", target.read_text())
# endregion

# region 示例5: 文件信息
if True:  # 改为 False 可跳过此示例
    p = Path(__file__)  # 当前脚本文件

    # 获取文件状态
    stat = p.stat()
    print("文件大小:", stat.st_size, "字节")
    print("修改时间戳:", stat.st_mtime)

    # 更友好的时间显示
    from datetime import datetime

    mtime = datetime.fromtimestamp(stat.st_mtime)
    print("修改时间:", mtime.strftime("%Y-%m-%d %H:%M:%S"))

    # 检查权限 (Unix 系统)
    # print("可读:", p.is_readable())  # Python 3.12+
# endregion
