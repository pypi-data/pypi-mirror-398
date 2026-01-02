"""
GitPython 远程仓库操作
======================
本文件介绍 GitPython 的远程仓库操作，包括：
- 管理远程仓库
- 拉取和推送
- 获取远程信息
"""

from git import Repo
from git.exc import GitCommandError
import tempfile
from pathlib import Path

# region 示例1: 查看远程仓库
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 查看远程仓库")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        print("远程仓库列表:")
        for remote in repo.remotes:
            print(f"\n  名称: {remote.name}")
            # 获取远程URL
            for url in remote.urls:
                print(f"  URL: {url}")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例2: 添加和删除远程仓库
if False:  # 改为 True 可运行此示例
    print("\n" + "=" * 50)
    print("示例2: 添加和删除远程仓库")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "test_repo"
        repo = Repo.init(repo_path)

        # 创建初始提交
        (repo_path / "README.md").write_text("# Test")
        repo.index.add(["README.md"])
        repo.index.commit("Initial commit")
        
        # 添加远程仓库
        origin = repo.create_remote("origin", "https://github.com/user/repo.git")
        print(f"添加远程仓库: {origin.name} -> {list(origin.urls)[0]}")
        
        # 添加另一个远程
        upstream = repo.create_remote("upstream", "https://github.com/other/repo.git")
        print(f"添加远程仓库: {upstream.name} -> {list(upstream.urls)[0]}")
        
        print("\n当前远程仓库:")
        for remote in repo.remotes:
            print(f"  - {remote.name}")
        
        # 删除远程仓库
        repo.delete_remote("upstream")
        print("\n删除 upstream 后:")
        for remote in repo.remotes:
            print(f"  - {remote.name}")
# endregion

# region 示例3: Fetch 操作
if False:  # 改为 True 可运行此示例（需要网络连接）
    print("\n" + "=" * 50)
    print("示例3: Fetch 操作")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        if repo.remotes:
            origin = repo.remotes.origin
            print(f"正在从 {origin.name} 获取更新...")
            
            # fetch 获取远程更新但不合并
            fetch_info = origin.fetch()
            
            for info in fetch_info:
                print(f"  {info.name}: {info.commit.hexsha[:8]}")
        else:
            print("没有配置远程仓库")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例4: Pull 和 Push 操作
if False:  # 改为 True 可运行此示例（需要网络连接和权限）
    print("\n" + "=" * 50)
    print("示例4: Pull 和 Push 操作")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        if repo.remotes:
            origin = repo.remotes.origin
            
            # Pull: 获取并合并远程更改
            print("执行 pull...")
            pull_info = origin.pull()
            for info in pull_info:
                print(f"  {info.ref}: {info.commit.hexsha[:8]}")
            
            # Push: 推送本地更改到远程（需要权限）
            # print("执行 push...")
            # push_info = origin.push()
            # for info in push_info:
            #     print(f"  {info.summary}")
        else:
            print("没有配置远程仓库")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例5: 查看远程分支信息
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例5: 查看远程分支信息")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        for remote in repo.remotes:
            print(f"\n远程 '{remote.name}' 的分支:")
            for ref in remote.refs:
                print(f"  - {ref.name}")
                print(f"    最新提交: {ref.commit.hexsha[:8]}")
                print(f"    提交消息: {ref.commit.message.strip()[:40]}")
    except Exception as e:
        print(f"错误: {e}")
# endregion
