"""
Invoke 实战应用
===============
综合运用 invoke 构建实际项目的自动化任务。

适用版本: Python 3.6+
"""

from invoke import task, Context, Collection
import sys
import os

# region 示例1: 项目构建任务
if True:  # 改为 False 可跳过此示例
    """
    典型的 Python 项目构建任务
    """
    
    @task
    def clean_build(c):
        """清理构建产物"""
        print("[clean] 清理构建目录...")
        
        dirs_to_clean = ['build', 'dist', '*.egg-info']
        for pattern in dirs_to_clean:
            if sys.platform == 'win32':
                c.run(f'if exist {pattern} rmdir /s /q {pattern}', warn=True, hide=True)
            else:
                c.run(f'rm -rf {pattern}', warn=True, hide=True)
        
        print("[clean] 清理完成")
    
    @task
    def build_package(c):
        """构建 Python 包"""
        print("[build] 构建 Python 包...")
        c.run("python -m build", warn=True)
        print("[build] 构建完成")
    
    ctx = Context()
    print("=== 清理任务演示 ===")
    clean_build(ctx)
# endregion

# region 示例2: 代码质量检查任务
if True:  # 改为 False 可跳过此示例
    """
    代码格式化和检查任务
    """
    
    @task
    def format_code(c, check=False):
        """
        格式化代码
        
        Args:
            check: 仅检查，不修改文件
        """
        check_flag = "--check" if check else ""
        
        print("[format] 使用 black 格式化...")
        # 这里只是演示命令，实际需要安装 black
        cmd = f"black {check_flag} src/"
        print(f"  将执行: {cmd}")
        
        print("[format] 使用 isort 排序导入...")
        isort_check = "--check-only" if check else ""
        cmd = f"isort {isort_check} src/"
        print(f"  将执行: {cmd}")
    
    @task
    def lint(c):
        """运行代码检查"""
        print("[lint] 运行 flake8...")
        print("  将执行: flake8 src/")
        
        print("[lint] 运行 mypy 类型检查...")
        print("  将执行: mypy src/")
    
    @task(pre=[format_code, lint])
    def check_all(c):
        """运行所有代码检查"""
        print("[check] 所有检查完成!")
    
    ctx = Context()
    print("=== 代码检查任务演示 ===")
    format_code(ctx, check=True)
# endregion

# region 示例3: 测试任务
if True:  # 改为 False 可跳过此示例
    """
    测试相关任务
    """
    
    @task
    def test(c, coverage=False, verbose=False, marker=None):
        """
        运行测试
        
        Args:
            coverage: 是否生成覆盖率报告
            verbose: 详细输出
            marker: pytest marker 过滤
        """
        cmd_parts = ["pytest"]
        
        if coverage:
            cmd_parts.append("--cov=src --cov-report=html")
        
        if verbose:
            cmd_parts.append("-v")
        
        if marker:
            cmd_parts.append(f"-m {marker}")
        
        cmd = " ".join(cmd_parts)
        print(f"[test] 执行: {cmd}")
    
    @task
    def test_unit(c):
        """只运行单元测试"""
        test(c, marker="unit")
    
    @task
    def test_integration(c):
        """只运行集成测试"""
        test(c, marker="integration")
    
    ctx = Context()
    print("=== 测试任务演示 ===")
    test(ctx, coverage=True, verbose=True)
# endregion

# region 示例4: Docker 相关任务
if True:  # 改为 False 可跳过此示例
    """
    Docker 构建和管理任务
    """
    
    @task
    def docker_build(c, tag="latest", no_cache=False):
        """
        构建 Docker 镜像
        
        Args:
            tag: 镜像标签
            no_cache: 是否禁用缓存
        """
        cache_flag = "--no-cache" if no_cache else ""
        cmd = f"docker build {cache_flag} -t myapp:{tag} ."
        print(f"[docker] 构建镜像: {cmd}")
    
    @task
    def docker_run(c, tag="latest", port=8000):
        """
        运行 Docker 容器
        
        Args:
            tag: 镜像标签
            port: 映射端口
        """
        cmd = f"docker run -p {port}:8000 myapp:{tag}"
        print(f"[docker] 运行容器: {cmd}")
    
    @task
    def docker_push(c, tag="latest", registry="docker.io"):
        """推送镜像到仓库"""
        full_tag = f"{registry}/myapp:{tag}"
        print(f"[docker] 标记镜像: docker tag myapp:{tag} {full_tag}")
        print(f"[docker] 推送镜像: docker push {full_tag}")
    
    ctx = Context()
    print("=== Docker 任务演示 ===")
    docker_build(ctx, tag="v1.0.0")
# endregion

# region 示例5: 完整的 tasks.py 示例
if True:  # 改为 False 可跳过此示例
    """
    展示一个完整的 tasks.py 文件结构
    """
    
    tasks_py_content = '''
"""
tasks.py - 项目自动化任务
========================
使用方法: invoke <task-name> [options]
查看帮助: invoke --list
"""

from invoke import task, Collection

# ============ 构建任务 ============

@task
def clean(c):
    """清理构建产物"""
    c.run("rm -rf build dist *.egg-info", warn=True)

@task
def build(c):
    """构建项目"""
    c.run("python -m build")

@task(pre=[clean, build])
def rebuild(c):
    """清理后重新构建"""
    print("重新构建完成")

# ============ 测试任务 ============

@task
def test(c, cov=False):
    """运行测试"""
    cmd = "pytest"
    if cov:
        cmd += " --cov=src"
    c.run(cmd)

@task
def lint(c):
    """代码检查"""
    c.run("flake8 src/")
    c.run("mypy src/")

# ============ 开发任务 ============

@task
def dev(c):
    """启动开发服务器"""
    c.run("python -m flask run --reload")

@task
def shell(c):
    """启动交互式 shell"""
    c.run("python -i -c \\"from myapp import *\\"")

# ============ 部署任务 ============

@task
def deploy(c, env="staging"):
    """部署到指定环境"""
    print(f"部署到 {env} 环境...")

# ============ 命名空间组织 ============

# 创建命名空间
ns = Collection()
ns.add_task(clean)
ns.add_task(build)
ns.add_task(rebuild)
ns.add_task(test)
ns.add_task(lint)
ns.add_task(dev)
ns.add_task(deploy)

# 或者使用子命名空间
# db = Collection('db')
# db.add_task(migrate)
# db.add_task(seed)
# ns.add_collection(db)
'''
    
    print("=== 完整 tasks.py 示例 ===")
    print(tasks_py_content)
# endregion

# region 示例6: 命令行使用示例
if True:  # 改为 False 可跳过此示例
    """
    invoke 命令行使用方法汇总
    """
    
    print("=== invoke 命令行使用 ===")
    
    commands = [
        ("invoke --list", "列出所有可用任务"),
        ("invoke --help", "显示帮助信息"),
        ("invoke --help <task>", "显示特定任务的帮助"),
        ("invoke <task>", "执行任务"),
        ("invoke <task> --arg value", "带参数执行任务"),
        ("invoke <task> -a value", "使用短参数"),
        ("invoke task1 task2", "依次执行多个任务"),
        ("invoke -e", "显示执行的命令（echo）"),
        ("invoke -w", "命令失败时只警告"),
        ("invoke -f other_tasks.py", "使用其他任务文件"),
    ]
    
    for cmd, desc in commands:
        print(f"  {cmd}")
        print(f"    -> {desc}")
        print()
# endregion
