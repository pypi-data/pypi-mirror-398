"""
GitPython 提交与暂存操作
========================
本文件介绍 GitPython 的提交和暂存区操作，包括：
- 暂存文件
- 取消暂存
- 创建提交
- 修改提交
- 查看提交详情
"""

from git import Repo, Actor
import tempfile
from pathlib import Path
from datetime import datetime

# region 示例1: 暂存文件操作
if False:  # 改为 True 可运行此示例
    print("=" * 50)
    print("示例1: 暂存文件操作")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "test_repo"
        repo = Repo.init(repo_path)
        
        # 创建初始提交
        (repo_path / "README.md").write_text("# Project")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")
        
        # 创建多个文件
        (repo_path / "file1.txt").write_text("content 1")
        (repo_path / "file2.txt").write_text("content 2")
        (repo_path / "file3.txt").write_text("content 3")
        
        print("创建了 3 个新文件")
        print(f"未跟踪文件: {repo.untracked_files}")
        
        # 暂存单个文件
        repo.index.add(["file1.txt"])
        print("\n暂存 file1.txt 后:")
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        print(f"已暂存: {staged}")
        
        # 暂存多个文件
        repo.index.add(["file2.txt", "file3.txt"])
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        print(f"\n暂存所有文件后: {staged}")
        
        # 使用通配符暂存（通过 git 命令）
        (repo_path / "src").mkdir()
        (repo_path / "src" / "a.py").write_text("# a")
        (repo_path / "src" / "b.py").write_text("# b")
        
        # 暂存目录下所有文件
        repo.index.add(["src/a.py", "src/b.py"])
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        print(f"\n暂存 src 目录后: {staged}")
# endregion

# region 示例2: 取消暂存
if False:  # 改为 True 可运行此示例
    print("\n" + "=" * 50)
    print("示例2: 取消暂存")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "test_repo"
        repo = Repo.init(repo_path)
        
        # 创建初始提交
        (repo_path / "README.md").write_text("# Project")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")
        
        # 创建并暂存文件
        (repo_path / "file1.txt").write_text("content 1")
        (repo_path / "file2.txt").write_text("content 2")
        repo.index.add(["file1.txt", "file2.txt"])
        
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        print(f"暂存的文件: {staged}")
        
        # 取消暂存单个文件（使用 git reset）
        repo.index.reset(paths=["file1.txt"])
        
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        print(f"取消暂存 file1.txt 后: {staged}")
        print(f"未跟踪文件: {repo.untracked_files}")
# endregion

# region 示例3: 创建提交
if False:  # 改为 True 可运行此示例
    print("\n" + "=" * 50)
    print("示例3: 创建提交")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "test_repo"
        repo = Repo.init(repo_path)
        
        # 配置用户信息（如果没有全局配置）
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")
        
        # 创建文件并提交
        (repo_path / "README.md").write_text("# My Project")
        repo.index.add(["README.md"])
        
        # 基本提交
        commit1 = repo.index.commit("Initial commit")
        print(f"提交1: {commit1.hexsha[:8]}")
        print(f"  作者: {commit1.author}")
        print(f"  消息: {commit1.message}")
        
        # 使用自定义作者提交
        (repo_path / "file.txt").write_text("content")
        repo.index.add(["file.txt"])
        
        author = Actor("Custom Author", "custom@example.com")
        committer = Actor("Custom Committer", "committer@example.com")
        
        commit2 = repo.index.commit(
            "Add file with custom author",
            author=author,
            committer=committer
        )
        print(f"\n提交2: {commit2.hexsha[:8]}")
        print(f"  作者: {commit2.author}")
        print(f"  提交者: {commit2.committer}")
# endregion

# region 示例4: 查看提交详情
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例4: 查看提交详情")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 获取最新提交
        commit = repo.head.commit
        
        print("最新提交详情:")
        print(f"  SHA: {commit.hexsha}")
        print(f"  短SHA: {commit.hexsha[:8]}")
        print(f"  作者: {commit.author.name} <{commit.author.email}>")
        print(f"  提交者: {commit.committer.name}")
        print(f"  提交时间: {commit.committed_datetime}")
        print(f"  消息: {commit.message.strip()}")
        
        # 获取提交的父提交
        if commit.parents:
            print(f"\n父提交:")
            for parent in commit.parents:
                print(f"  - {parent.hexsha[:8]}: {parent.message.strip()[:40]}")
        
        # 获取提交修改的文件
        if commit.parents:
            print(f"\n修改的文件:")
            diffs = commit.diff(commit.parents[0])
            for diff in diffs[:5]:  # 只显示前5个
                change_type = diff.change_type  # A=添加, D=删除, M=修改, R=重命名
                print(f"  [{change_type}] {diff.a_path or diff.b_path}")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例5: 通过SHA获取提交
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例5: 通过SHA获取提交")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 获取最新提交的SHA
        latest_sha = repo.head.commit.hexsha
        print(f"最新提交SHA: {latest_sha}")
        
        # 通过完整SHA获取提交
        commit = repo.commit(latest_sha)
        print(f"通过完整SHA获取: {commit.message.strip()[:40]}")
        
        # 通过短SHA获取提交
        short_sha = latest_sha[:8]
        commit = repo.commit(short_sha)
        print(f"通过短SHA获取: {commit.message.strip()[:40]}")
        
        # 通过引用获取提交
        head_commit = repo.commit("HEAD")
        print(f"通过HEAD获取: {head_commit.message.strip()[:40]}")
        
        # 获取HEAD的前一个提交
        if head_commit.parents:
            parent_commit = repo.commit("HEAD~1")
            print(f"通过HEAD~1获取: {parent_commit.message.strip()[:40]}")
    except Exception as e:
        print(f"错误: {e}")
# endregion
