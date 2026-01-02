"""
Invoke 命令执行
===============
深入了解 Context.run() 的各种选项和用法。

适用版本: Python 3.6+
"""

from invoke import task, Context
import sys

# region 示例1: run() 基本选项
if True:  # 改为 False 可跳过此示例
    """
    Context.run() 的常用参数：
    - hide: 控制输出显示 (True/'out'/'err'/'both'/False)
    - warn: 命令失败时是否只警告而不抛异常
    - pty: 是否使用伪终端（Unix only）
    - echo: 是否打印正在执行的命令
    """
    
    @task
    def run_options(c):
        """演示 run() 的各种选项"""
        
        # echo=True 会打印正在执行的命令
        print("=== echo=True ===")
        c.run("python -c \"print('Hello')\"", echo=True)
        
        # hide=True 隐藏命令输出
        print("\n=== hide=True ===")
        result = c.run("python -c \"print('Hidden output')\"", hide=True)
        print(f"捕获的输出: {result.stdout.strip()}")
    
    ctx = Context()
    run_options(ctx)
# endregion

# region 示例2: 处理命令失败
if True:  # 改为 False 可跳过此示例
    """
    默认情况下，命令失败会抛出 UnexpectedExit 异常
    使用 warn=True 可以改为只警告
    """
    from invoke.exceptions import UnexpectedExit
    
    @task
    def handle_failure(c):
        """处理命令执行失败"""
        
        # warn=True: 命令失败不抛异常
        print("=== 使用 warn=True ===")
        result = c.run("python -c \"exit(1)\"", warn=True, hide=True)
        print(f"命令成功: {result.ok}")
        print(f"返回码: {result.return_code}")
        
        # 不使用 warn 时需要 try-except
        print("\n=== 使用 try-except ===")
        try:
            c.run("python -c \"exit(1)\"", hide=True)
        except UnexpectedExit as e:
            print(f"命令失败，返回码: {e.result.return_code}")
    
    ctx = Context()
    handle_failure(ctx)
# endregion

# region 示例3: 环境变量
if True:  # 改为 False 可跳过此示例
    """
    通过 env 参数传递环境变量
    """
    
    @task
    def with_env(c):
        """使用环境变量"""
        
        # 设置环境变量
        code = "import os; print(f'MY_VAR={os.environ.get(\"MY_VAR\", \"not set\")}')"
        
        print("=== 默认环境 ===")
        c.run(f'python -c "{code}"')
        
        print("\n=== 自定义环境变量 ===")
        c.run(f'python -c "{code}"', env={'MY_VAR': 'hello_invoke'})
    
    ctx = Context()
    with_env(ctx)
# endregion

# region 示例4: 工作目录
if True:  # 改为 False 可跳过此示例
    """
    使用 Context.cd() 上下文管理器改变工作目录
    """
    
    @task
    def change_directory(c):
        """在不同目录执行命令"""
        
        print("=== 当前目录 ===")
        if sys.platform == 'win32':
            c.run("cd")
        else:
            c.run("pwd")
        
        print("\n=== 切换到上级目录 ===")
        with c.cd(".."):
            if sys.platform == 'win32':
                c.run("cd")
            else:
                c.run("pwd")
        
        print("\n=== 回到原目录 ===")
        if sys.platform == 'win32':
            c.run("cd")
        else:
            c.run("pwd")
    
    ctx = Context()
    change_directory(ctx)
# endregion

# region 示例5: 命令前缀
if True:  # 改为 False 可跳过此示例
    """
    使用 Context.prefix() 为命令添加前缀
    常用于激活虚拟环境等场景
    """
    
    @task
    def with_prefix(c):
        """使用命令前缀"""
        
        # 模拟设置环境变量前缀
        if sys.platform == 'win32':
            prefix_cmd = "set MY_PREFIX=active &&"
        else:
            prefix_cmd = "export MY_PREFIX=active &&"
        
        print("=== 使用前缀 ===")
        with c.prefix(prefix_cmd):
            code = "import os; print(f'MY_PREFIX={os.environ.get(\"MY_PREFIX\", \"not set\")}')"
            c.run(f'python -c "{code}"')
    
    ctx = Context()
    with_prefix(ctx)
# endregion

# region 示例6: Result 对象详解
if True:  # 改为 False 可跳过此示例
    """
    run() 返回的 Result 对象包含丰富的执行信息
    """
    
    @task
    def result_details(c):
        """查看 Result 对象的属性"""
        
        result = c.run(
            "python -c \"import sys; print('stdout'); print('stderr', file=sys.stderr)\"",
            hide=True
        )
        
        print("=== Result 对象属性 ===")
        print(f"stdout: {repr(result.stdout)}")
        print(f"stderr: {repr(result.stderr)}")
        print(f"return_code: {result.return_code}")
        print(f"ok: {result.ok}")
        print(f"failed: {result.failed}")
        print(f"command: {result.command}")
        print(f"shell: {result.shell}")
    
    ctx = Context()
    result_details(ctx)
# endregion
