"""
pathlib 实战应用
================
常见的文件系统操作场景和最佳实践
"""

from pathlib import Path
import tempfile
import shutil

# region 示例1: 安全地创建目录结构
if True:  # 改为 False 可跳过此示例
    def ensure_dir(path: Path) -> Path:
        """确保目录存在，返回 Path 对象"""
        path.mkdir(parents=True, exist_ok=True)
        return path

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # 创建项目结构
        project = base / "myproject"
        dirs = ["src", "tests", "docs", "config"]

        for d in dirs:
            ensure_dir(project / d)
            print(f"创建目录: {d}")

        # 验证结构
        print("\n项目结构:")
        for item in sorted(project.iterdir()):
            print(f"  📁 {item.name}")
# endregion

# region 示例2: 批量重命名文件
if True:  # 改为 False 可跳过此示例
    def batch_rename(directory: Path, pattern: str, prefix: str) -> list:
        """批量添加前缀"""
        renamed = []
        for f in directory.glob(pattern):
            if not f.name.startswith(prefix):
                new_name = f.with_name(f"{prefix}{f.name}")
                # f.rename(new_name)  # 实际重命名
                renamed.append((f.name, new_name.name))
        return renamed

    # 演示 (不实际执行)
    demo_dir = Path("src/ptlearn/demo/pathlib")
    print("批量重命名预览 (添加 'demo_' 前缀):")
    for old, new in batch_rename(demo_dir, "*.py", "demo_")[:3]:
        print(f"  {old} -> {new}")
# endregion

# region 示例3: 查找并处理特定文件
if True:  # 改为 False 可跳过此示例
    def find_large_files(directory: Path, min_size_kb: int = 10) -> list:
        """查找大于指定大小的文件"""
        large_files = []
        for f in directory.rglob("*"):
            if f.is_file():
                size_kb = f.stat().st_size / 1024
                if size_kb >= min_size_kb:
                    large_files.append((f, size_kb))
        return sorted(large_files, key=lambda x: x[1], reverse=True)

    # 查找项目中的大文件
    project_root = Path(".")
    print(f"大于 1KB 的文件 (前 5 个):")
    for f, size in find_large_files(project_root, min_size_kb=1)[:5]:
        print(f"  {f}: {size:.1f} KB")
# endregion

# region 示例4: 文件备份工具
if True:  # 改为 False 可跳过此示例
    from datetime import datetime

    def backup_file(file_path: Path, backup_dir: Path = None) -> Path:
        """创建文件备份，添加时间戳"""
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 默认备份到同目录
        if backup_dir is None:
            backup_dir = file_path.parent

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}.bak"
        backup_path = backup_dir / backup_name

        # 复制文件 (使用 shutil)
        # shutil.copy2(file_path, backup_path)

        return backup_path

    # 演示
    demo_file = Path("pyproject.toml")
    if demo_file.exists():
        backup = backup_file(demo_file)
        print(f"备份路径预览: {backup}")
# endregion

# region 示例5: 项目文件统计
if True:  # 改为 False 可跳过此示例
    def analyze_project(root: Path) -> dict:
        """分析项目文件统计"""
        stats = {
            "total_files": 0,
            "total_dirs": 0,
            "by_extension": {},
            "total_size": 0,
        }

        for item in root.rglob("*"):
            # 跳过隐藏文件和常见忽略目录
            if any(part.startswith(".") for part in item.parts):
                continue
            if any(part in ["__pycache__", "node_modules", ".venv"] for part in item.parts):
                continue

            if item.is_file():
                stats["total_files"] += 1
                stats["total_size"] += item.stat().st_size

                ext = item.suffix.lower() or "(无后缀)"
                stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1
            elif item.is_dir():
                stats["total_dirs"] += 1

        return stats

    # 分析当前项目
    project = Path("src")
    if project.exists():
        result = analyze_project(project)
        print("项目统计:")
        print(f"  文件数: {result['total_files']}")
        print(f"  目录数: {result['total_dirs']}")
        print(f"  总大小: {result['total_size'] / 1024:.1f} KB")
        print("  按扩展名:")
        for ext, count in sorted(result["by_extension"].items(), key=lambda x: -x[1])[:5]:
            print(f"    {ext}: {count} 个")
# endregion

# region 示例6: 与 os.path 对比
if True:  # 改为 False 可跳过此示例
    import os

    # 传统 os.path 方式
    old_way = os.path.join(
        os.path.expanduser("~"),
        "documents",
        "projects",
        "myapp",
        "config.json"
    )

    # pathlib 方式
    new_way = Path.home() / "documents" / "projects" / "myapp" / "config.json"

    print("os.path 方式:")
    print(f"  {old_way}")
    print("\npathlib 方式:")
    print(f"  {new_way}")
    print("\n结果相同:", str(new_way) == old_way)

    # 更多对比
    print("\n常用操作对比:")
    print("  获取文件名: os.path.basename() vs path.name")
    print("  获取目录:   os.path.dirname()  vs path.parent")
    print("  拼接路径:   os.path.join()     vs path / 'sub'")
    print("  是否存在:   os.path.exists()   vs path.exists()")
    print("  读取文件:   open() + read()    vs path.read_text()")
# endregion
