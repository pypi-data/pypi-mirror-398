"""
GitPython 基础操作
==================
本文件介绍 GitPython 的基础用法，包括：
- 安装与导入
- 打开/克隆仓库
- 获取仓库基本信息
- 查看提交历史

安装: pip install gitpython
文档: https://gitpython.readthedocs.io/
"""

from git import Repo
from pathlib import Path
import tempfile

# region 示例1: 打开本地仓库
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 打开本地仓库")
    print("=" * 50)
    
    # 打开当前项目的 Git 仓库（假设在 Git 仓库中运行）
    # Repo() 可以接受仓库路径，或使用 search_parent_directories 向上查找
    try:
        repo = Repo(search_parent_directories=True)
        print(f"仓库路径: {repo.working_dir}")
        print(f"Git 目录: {repo.git_dir}")
        print(f"是否为裸仓库: {repo.bare}")
        print(f"当前分支: {repo.active_branch}")
    except Exception as e:
        print(f"未找到 Git 仓库: {e}")
# endregion

# region 示例2: 获取仓库状态
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例2: 获取仓库状态")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 检查是否有未提交的更改
        print(f"是否有未提交的更改: {repo.is_dirty()}")
        
        # 获取未跟踪的文件
        untracked = repo.untracked_files
        print(f"未跟踪文件数量: {len(untracked)}")
        if untracked[:3]:  # 只显示前3个
            print(f"未跟踪文件示例: {untracked[:3]}")
        
        # 获取已修改但未暂存的文件
        changed_files = [item.a_path for item in repo.index.diff(None)]
        print(f"已修改未暂存文件: {changed_files[:3] if changed_files else '无'}")
        
        # 获取已暂存的文件
        staged_files = [item.a_path for item in repo.index.diff('HEAD')]
        print(f"已暂存文件: {staged_files[:3] if staged_files else '无'}")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例3: 查看提交历史
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例3: 查看提交历史")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 获取最近5次提交
        print("最近5次提交:")
        for i, commit in enumerate(repo.iter_commits(max_count=5)):
            print(f"\n  [{i+1}] {commit.hexsha[:8]}")
            print(f"      作者: {commit.author.name} <{commit.author.email}>")
            print(f"      日期: {commit.committed_datetime}")
            print(f"      消息: {commit.message.strip()[:50]}")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例4: 克隆远程仓库
if False:  # 改为 True 可运行此示例（会实际克隆仓库）
    print("\n" + "=" * 50)
    print("示例4: 克隆远程仓库")
    print("=" * 50)
    
    # 使用临时目录克隆一个小型仓库
    with tempfile.TemporaryDirectory() as tmp_dir:
        clone_url = "https://github.com/gitpython-developers/GitPython.git"
        clone_path = Path(tmp_dir) / "gitpython"
        
        print(f"正在克隆 {clone_url}...")
        print(f"目标路径: {clone_path}")
        
        # 浅克隆（只获取最近1次提交，节省时间和空间）
        cloned_repo = Repo.clone_from(
            clone_url, 
            clone_path,
            depth=1  # 浅克隆
        )
        
        print(f"克隆完成!")
        print(f"默认分支: {cloned_repo.active_branch}")
        print(f"最新提交: {cloned_repo.head.commit.hexsha[:8]}")
# endregion

# region 示例5: 初始化新仓库
if False:  # 改为 True 可运行此示例（会创建新仓库）
    print("\n" + "=" * 50)
    print("示例5: 初始化新仓库")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        new_repo_path = Path(tmp_dir) / "my_new_repo"
        new_repo_path.mkdir()
        
        # 初始化新仓库
        new_repo = Repo.init(new_repo_path)
        print(f"新仓库已创建: {new_repo.working_dir}")
        print(f"是否为空仓库: {len(list(new_repo.iter_commits())) == 0}")
        
        # 创建一个文件并提交
        readme = new_repo_path / "README.md"
        readme.write_text("# My New Project\n")
        
        new_repo.index.add(["README.md"])
        new_repo.index.commit("Initial commit")
        
        print(f"首次提交完成: {new_repo.head.commit.hexsha[:8]}")
# endregion
