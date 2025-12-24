"""
GitPython 分支追踪与比较
========================
本文件介绍如何：
- 查询本地分支对应的远程追踪分支
- 比较本地分支与远程分支的提交差异
"""

from git import Repo

# region 示例1: 查询本地分支对应的远程追踪分支
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 查询本地分支对应的远程追踪分支")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        print("\n本地分支及其追踪的远程分支:")
        for branch in repo.branches:
            tracking = branch.tracking_branch()
            if tracking:
                print(f"  {branch.name} -> {tracking.name}")
            else:
                print(f"  {branch.name} -> (无追踪分支)")
        
        # 单独查询当前分支的追踪分支
        print(f"\n当前分支: {repo.active_branch.name}")
        current_tracking = repo.active_branch.tracking_branch()
        if current_tracking:
            print(f"追踪分支: {current_tracking.name}")
        else:
            print("追踪分支: (未设置)")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例2: 比较本地分支与远程分支的提交差异
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例2: 比较本地分支与远程分支的提交差异")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 先 fetch 确保远程信息是最新的
        print("正在获取远程更新...")
        for remote in repo.remotes:
            remote.fetch()
        
        local_branch = repo.active_branch
        tracking = local_branch.tracking_branch()
        
        if not tracking:
            print(f"分支 '{local_branch.name}' 没有设置追踪分支")
        else:
            print(f"\n比较: {local_branch.name} vs {tracking.name}")
            
            # 本地领先的提交 (本地有但远程没有)
            ahead_commits = list(repo.iter_commits(f"{tracking.name}..{local_branch.name}"))
            print(f"\n本地领先 {len(ahead_commits)} 个提交:")
            for commit in ahead_commits[:5]:  # 最多显示5个
                print(f"  + {commit.hexsha[:8]} {commit.message.strip()[:50]}")
            if len(ahead_commits) > 5:
                print(f"  ... 还有 {len(ahead_commits) - 5} 个提交")
            
            # 本地落后的提交 (远程有但本地没有)
            behind_commits = list(repo.iter_commits(f"{local_branch.name}..{tracking.name}"))
            print(f"\n本地落后 {len(behind_commits)} 个提交:")
            for commit in behind_commits[:5]:  # 最多显示5个
                print(f"  - {commit.hexsha[:8]} {commit.message.strip()[:50]}")
            if len(behind_commits) > 5:
                print(f"  ... 还有 {len(behind_commits) - 5} 个提交")
            
            # 总结
            if not ahead_commits and not behind_commits:
                print("\n状态: 本地与远程完全同步")
            elif ahead_commits and not behind_commits:
                print(f"\n状态: 本地领先远程 {len(ahead_commits)} 个提交，可以 push")
            elif behind_commits and not ahead_commits:
                print(f"\n状态: 本地落后远程 {len(behind_commits)} 个提交，需要 pull")
            else:
                print(f"\n状态: 本地与远程有分歧，需要合并或变基")
    except Exception as e:
        print(f"错误: {e}")
# endregion
