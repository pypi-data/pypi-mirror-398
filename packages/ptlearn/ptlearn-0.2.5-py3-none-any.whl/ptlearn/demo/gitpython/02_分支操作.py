"""
GitPython 分支操作
==================
本文件介绍 GitPython 的分支管理功能，包括：
- 列出分支
- 创建/删除分支
- 切换分支
- 分支比较
"""

from git import Repo
from git.exc import GitCommandError
import tempfile
from pathlib import Path

# region 示例1: 列出所有分支
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 列出所有分支")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 列出本地分支
        print("本地分支:")
        for branch in repo.branches:
            # 标记当前分支
            marker = " *" if branch == repo.active_branch else ""
            print(f"  - {branch.name}{marker}")
        
        # 列出远程分支
        print("\n远程分支:")
        for remote in repo.remotes:
            print(f"  远程仓库: {remote.name}")
            for ref in remote.refs:
                print(f"    - {ref.name}")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例2: 获取分支详细信息
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例2: 获取分支详细信息")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 当前分支信息
        current = repo.active_branch
        print(f"当前分支: {current.name}")
        print(f"分支指向的提交: {current.commit.hexsha[:8]}")
        print(f"提交消息: {current.commit.message.strip()[:50]}")
        
        # 检查分支是否有上游跟踪
        if current.tracking_branch():
            tracking = current.tracking_branch()
            print(f"跟踪分支: {tracking.name}")
        else:
            print("跟踪分支: 无")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例3: 创建和删除分支（演示用临时仓库）
if False:  # 改为 True 可运行此示例
    print("\n" + "=" * 50)
    print("示例3: 创建和删除分支")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 创建测试仓库
        repo_path = Path(tmp_dir) / "test_repo"
        repo = Repo.init(repo_path)
        
        # 创建初始提交
        (repo_path / "file.txt").write_text("hello")
        repo.index.add(["file.txt"])
        repo.index.commit("Initial commit")
        
        print(f"初始分支: {repo.active_branch.name}")
        
        # 创建新分支
        new_branch = repo.create_head("feature/new-feature")
        print(f"创建分支: {new_branch.name}")
        
        # 从特定提交创建分支
        another_branch = repo.create_head("bugfix/fix-123", repo.head.commit)
        print(f"创建分支: {another_branch.name}")
        
        # 列出所有分支
        print("\n当前所有分支:")
        for b in repo.branches:
            print(f"  - {b.name}")
        
        # 删除分支
        repo.delete_head("bugfix/fix-123")
        print("\n删除分支后:")
        for b in repo.branches:
            print(f"  - {b.name}")
# endregion

# region 示例4: 切换分支
if False:  # 改为 True 可运行此示例
    print("\n" + "=" * 50)
    print("示例4: 切换分支")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 创建测试仓库
        repo_path = Path(tmp_dir) / "test_repo"
        repo = Repo.init(repo_path)
        
        # 创建初始提交
        (repo_path / "file.txt").write_text("hello")
        repo.index.add(["file.txt"])
        repo.index.commit("Initial commit")
        
        # 创建新分支
        dev_branch = repo.create_head("develop")
        
        print(f"当前分支: {repo.active_branch.name}")
        
        # 切换到新分支
        dev_branch.checkout()
        print(f"切换后: {repo.active_branch.name}")
        
        # 在新分支上提交
        (repo_path / "dev_file.txt").write_text("dev content")
        repo.index.add(["dev_file.txt"])
        repo.index.commit("Add dev file")
        
        # 切换回主分支
        repo.heads.master.checkout()
        print(f"切换回: {repo.active_branch.name}")
        
        # 验证文件状态
        dev_file_exists = (repo_path / "dev_file.txt").exists()
        print(f"dev_file.txt 存在: {dev_file_exists}")  # 应该是 False
# endregion

# region 示例5: 比较分支差异
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例5: 比较分支差异")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        if len(repo.branches) >= 2:
            branch1 = repo.branches[0]
            branch2 = repo.branches[1] if len(repo.branches) > 1 else branch1
            
            print(f"比较 {branch1.name} 和 {branch2.name}:")
            
            # 获取两个分支之间的差异提交
            commits_diff = list(repo.iter_commits(f"{branch1.name}..{branch2.name}", max_count=5))
            print(f"\n{branch2.name} 比 {branch1.name} 多的提交 (最多5个):")
            for commit in commits_diff:
                print(f"  - {commit.hexsha[:8]}: {commit.message.strip()[:40]}")
            
            if not commits_diff:
                print("  (无差异或分支相同)")
        else:
            print("仓库只有一个分支，无法比较")
    except Exception as e:
        print(f"错误: {e}")
# endregion
