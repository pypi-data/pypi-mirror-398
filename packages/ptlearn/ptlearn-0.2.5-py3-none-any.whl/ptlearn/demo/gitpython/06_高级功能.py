"""
GitPython 高级功能
==================
本文件介绍 GitPython 的高级功能，包括：
- 标签管理
- Stash 操作
- 子模块
- Git 配置
- 执行原生 Git 命令
"""

from git import Repo
import tempfile
from pathlib import Path

# region 示例1: 标签管理
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 标签管理")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 列出所有标签
        print("现有标签:")
        if repo.tags:
            for tag in repo.tags[:10]:
                print(f"  - {tag.name}")
                if tag.tag:  # 附注标签
                    print(f"    消息: {tag.tag.message.strip()[:40] if tag.tag.message else 'N/A'}")
        else:
            print("  (无标签)")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例2: 创建和删除标签
if False:  # 改为 True 可运行此示例
    print("\n" + "=" * 50)
    print("示例2: 创建和删除标签")
    print("=" * 50)

    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "test_repo"
        repo = Repo.init(repo_path)
        
        # 创建初始提交
        (repo_path / "README.md").write_text("# Project")
        repo.index.add(["README.md"])
        commit1 = repo.index.commit("Initial commit")
        
        # 创建轻量标签
        light_tag = repo.create_tag("v0.1.0")
        print(f"创建轻量标签: {light_tag.name}")
        
        # 创建另一个提交
        (repo_path / "file.txt").write_text("content")
        repo.index.add(["file.txt"])
        commit2 = repo.index.commit("Add file")
        
        # 创建附注标签
        annotated_tag = repo.create_tag(
            "v1.0.0",
            message="Release version 1.0.0"
        )
        print(f"创建附注标签: {annotated_tag.name}")
        
        # 在特定提交上创建标签
        old_tag = repo.create_tag("v0.0.1", ref=commit1)
        print(f"在旧提交上创建标签: {old_tag.name}")
        
        # 列出所有标签
        print("\n所有标签:")
        for tag in repo.tags:
            print(f"  - {tag.name} -> {tag.commit.hexsha[:8]}")
        
        # 删除标签
        repo.delete_tag("v0.0.1")
        print("\n删除 v0.0.1 后:")
        for tag in repo.tags:
            print(f"  - {tag.name}")
# endregion

# region 示例3: Stash 操作
if False:  # 改为 True 可运行此示例
    print("\n" + "=" * 50)
    print("示例3: Stash 操作")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir) / "test_repo"
        repo = Repo.init(repo_path)
        
        # 配置用户
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test")
            config.set_value("user", "email", "test@test.com")
        
        # 创建初始提交
        (repo_path / "file.txt").write_text("original")
        repo.index.add(["file.txt"])
        repo.index.commit("Initial commit")
        
        # 修改文件
        (repo_path / "file.txt").write_text("modified")
        print(f"文件已修改，仓库是否dirty: {repo.is_dirty()}")
        
        # 创建 stash
        repo.git.stash("save", "My stash message")
        print(f"Stash 后，仓库是否dirty: {repo.is_dirty()}")
        
        # 查看 stash 列表
        stash_list = repo.git.stash("list")
        print(f"Stash 列表:\n{stash_list}")
        
        # 恢复 stash
        repo.git.stash("pop")
        print(f"Pop 后，仓库是否dirty: {repo.is_dirty()}")
        
        # 读取文件内容验证
        content = (repo_path / "file.txt").read_text()
        print(f"文件内容: {content}")
# endregion

# region 示例4: 读取和修改 Git 配置
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例4: 读取 Git 配置")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 读取配置
        config = repo.config_reader()
        
        # 读取用户信息
        try:
            user_name = config.get_value("user", "name")
            user_email = config.get_value("user", "email")
            print(f"用户名: {user_name}")
            print(f"邮箱: {user_email}")
        except Exception:
            print("未配置用户信息")
        
        # 读取远程仓库配置
        print("\n远程仓库配置:")
        for remote in repo.remotes:
            try:
                url = config.get_value(f'remote "{remote.name}"', "url")
                print(f"  {remote.name}: {url}")
            except Exception:
                pass
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例5: 执行原生 Git 命令
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例5: 执行原生 Git 命令")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 使用 repo.git 可以执行任何 git 命令
        # 方法名对应 git 子命令，下划线会转换为连字符
        
        # git status
        status = repo.git.status(short=True)
        print("git status --short:")
        print(status if status else "  (工作区干净)")
        
        # git log --oneline -5
        log = repo.git.log("--oneline", "-5")
        print("\ngit log --oneline -5:")
        print(log)
        
        # git branch -a
        branches = repo.git.branch("-a")
        print("\ngit branch -a:")
        print(branches)
        
        # git rev-parse HEAD
        head_sha = repo.git.rev_parse("HEAD")
        print(f"\ngit rev-parse HEAD: {head_sha[:8]}")
    except Exception as e:
        print(f"错误: {e}")
# endregion

# region 示例6: 子模块操作
if False:  # 改为 True 可运行此示例
    print("\n" + "=" * 50)
    print("示例6: 子模块操作")
    print("=" * 50)
    
    try:
        repo = Repo(search_parent_directories=True)
        
        # 列出子模块
        if repo.submodules:
            print("子模块列表:")
            for sm in repo.submodules:
                print(f"  - {sm.name}")
                print(f"    路径: {sm.path}")
                print(f"    URL: {sm.url}")
        else:
            print("该仓库没有子模块")
        
        # 添加子模块示例（注释掉，避免实际执行）
        # repo.create_submodule(
        #     "lib",
        #     "lib",
        #     url="https://github.com/user/lib.git"
        # )
    except Exception as e:
        print(f"错误: {e}")
# endregion
