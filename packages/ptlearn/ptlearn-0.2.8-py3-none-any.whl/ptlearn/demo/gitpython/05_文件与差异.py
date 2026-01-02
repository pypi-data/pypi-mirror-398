"""
GitPython 文件与差异操作
========================
本文件介绍 GitPython 的文件和差异比较功能，包括：
- 查看文件内容
- 比较差异
- 查看文件历史
- Blame 功能
"""

from git import Repo
import tempfile
from pathlib import Path

# region 示例1: 获取特定版本的文件内容
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 获取特定版本的文件内容")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 获取 HEAD 提交中的文件
        commit = repo.head.commit
        
        # 列出提交中的文件（树对象）
        print("HEAD 提交中的文件（前10个）:")
        for i, blob in enumerate(commit.tree.traverse()):
            if i >= 10:
                print("  ...")
                break
            if blob.type == "blob":  # 只显示文件，不显示目录
                print(f"  {blob.path}")
        
        # 获取特定文件的内容
        if "README.md" in [b.path for b in commit.tree.traverse()]:
            readme_blob = commit.tree / "README.md"
            content = readme_blob.data_stream.read().decode("utf-8")
            print(f"\nREADME.md 内容预览:")
            print(content[:200] + "..." if len(content) > 200 else content)
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例2: 比较两个提交的差异
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例2: 比较两个提交的差异")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        commits = list(repo.iter_commits(max_count=2))
        if len(commits) >= 2:
            newer = commits[0]
            older = commits[1]
            
            print(f"比较提交:")
            print(f"  旧: {older.hexsha[:8]} - {older.message.strip()[:30]}")
            print(f"  新: {newer.hexsha[:8]} - {newer.message.strip()[:30]}")
            
            # 获取差异
            diffs = older.diff(newer)
            
            print(f"\n变更文件 ({len(diffs)} 个):")
            for diff in diffs[:10]:
                change_type = diff.change_type
                type_map = {"A": "添加", "D": "删除", "M": "修改", "R": "重命名"}
                type_str = type_map.get(change_type, change_type)
                path = diff.b_path or diff.a_path
                print(f"  [{type_str}] {path}")
        else:
            print("提交历史不足2个，无法比较")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例3: 查看工作区与暂存区的差异
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例3: 查看工作区与暂存区的差异")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 工作区 vs 暂存区（未暂存的更改）
        unstaged_diffs = repo.index.diff(None)
        print(f"未暂存的更改 ({len(unstaged_diffs)} 个):")
        for diff in unstaged_diffs[:5]:
            print(f"  [M] {diff.a_path}")
        
        # 暂存区 vs HEAD（已暂存的更改）
        staged_diffs = repo.index.diff("HEAD")
        print(f"\n已暂存的更改 ({len(staged_diffs)} 个):")
        for diff in staged_diffs[:5]:
            print(f"  [M] {diff.a_path}")
        
        if not unstaged_diffs and not staged_diffs:
            print("工作区干净，没有更改")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例4: 获取差异的详细内容
if False:  # 改为 True 可运行此示例
    print("\n" + "=" * 50)
    print("示例4: 获取差异的详细内容")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "test_repo"
        repo = Repo.init(repo_path)
        
        # 创建初始文件
        file_path = repo_path / "test.txt"
        file_path.write_text("line 1\nline 2\nline 3\n")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        
        # 修改文件
        file_path.write_text("line 1\nmodified line 2\nline 3\nnew line 4\n")
        repo.index.add(["test.txt"])
        commit2 = repo.index.commit("Modify test.txt")
        
        # 获取详细差异
        parent = commit2.parents[0]
        diffs = parent.diff(commit2, create_patch=True)
        
        for diff in diffs:
            print(f"文件: {diff.a_path}")
            print("差异内容:")
            # diff.diff 是字节类型
            diff_text = diff.diff.decode("utf-8") if diff.diff else ""
            print(diff_text)
# endregion

# region 示例5: 查看文件的提交历史
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例5: 查看文件的提交历史")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 查看特定文件的历史
        file_path = "README.md"
        
        print(f"'{file_path}' 的提交历史（最近5次）:")
        commits = list(repo.iter_commits(paths=file_path, max_count=5))
        
        for commit in commits:
            print(f"\n  {commit.hexsha[:8]}")
            print(f"    作者: {commit.author.name}")
            print(f"    日期: {commit.committed_datetime.strftime('%Y-%m-%d %H:%M')}")
            print(f"    消息: {commit.message.strip()[:40]}")
        
        if not commits:
            print(f"  未找到 '{file_path}' 的提交历史")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例6: Git Blame 功能
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例6: Git Blame 功能")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        file_path = "README.md"
        
        # 使用 git blame
        blame_data = repo.blame("HEAD", file_path)
        
        print(f"'{file_path}' 的 blame 信息（前10行）:")
        line_num = 1
        for commit, lines in blame_data:
            for line in lines:
                if line_num > 10:
                    break
                author = commit.author.name[:10].ljust(10)
                sha = commit.hexsha[:7]
                content = line[:40] if len(line) <= 40 else line[:37] + "..."
                print(f"  {line_num:3} | {sha} | {author} | {content}")
                line_num += 1
            if line_num > 10:
                print("  ...")
                break
    except Exception as e:
        print(f"错误: {e}")
# endregion
