"""
Invoke 基础概念
===============
invoke 是一个 Python 任务执行库，用于管理面向 shell 的子进程，
并将可执行的 Python 代码组织成 CLI 可调用的任务。

适用版本: Python 3.6+
安装: pip install invoke
"""

from invoke import task, Context

# region 示例1: 最简单的任务定义
if True:  # 改为 False 可跳过此示例
    """
    @task 装饰器将普通函数转换为 invoke 任务
    第一个参数 c (或 ctx) 是 Context 对象，用于执行命令
    """
    
    @task
    def hello(c):
        """打印问候语"""
        print("Hello, Invoke!")
    
    # 直接调用任务函数进行测试
    # 创建一个 Context 对象
    ctx = Context()
    hello(ctx)
# endregion

# region 示例2: 带参数的任务
if True:  # 改为 False 可跳过此示例
    """
    任务可以接受参数，这些参数会自动转换为命令行选项
    """
    
    @task
    def greet(c, name, times=1):
        """
        问候指定的人
        
        Args:
            name: 要问候的人名（必需参数）
            times: 问候次数（可选，默认1次）
        """
        for i in range(times):
            print(f"Hello, {name}!")
    
    ctx = Context()
    greet(ctx, "Python", times=3)
# endregion

# region 示例3: 使用 Context 执行 shell 命令
if True:  # 改为 False 可跳过此示例
    """
    Context.run() 是 invoke 的核心功能，用于执行 shell 命令
    """
    
    @task
    def show_python_version(c):
        """显示 Python 版本"""
        # run() 执行命令并返回 Result 对象
        result = c.run("python --version", hide=False)
        print(f"返回码: {result.return_code}")
        print(f"命令执行成功: {result.ok}")
    
    ctx = Context()
    show_python_version(ctx)
# endregion

# region 示例4: 捕获命令输出
if True:  # 改为 False 可跳过此示例
    """
    使用 hide 参数控制输出显示，并通过 Result 对象获取输出内容
    """
    
    @task
    def capture_output(c):
        """捕获命令输出"""
        # hide=True 隐藏输出，hide='out' 只隐藏标准输出
        # hide='err' 只隐藏错误输出，hide='both' 隐藏全部
        result = c.run("python --version", hide=True)
        
        print(f"标准输出: {result.stdout.strip()}")
        print(f"标准错误: {result.stderr.strip()}")
    
    ctx = Context()
    capture_output(ctx)
# endregion

# region 示例5: 任务文档字符串
if True:  # 改为 False 可跳过此示例
    """
    任务的 docstring 会自动成为帮助信息
    在命令行使用 invoke --help taskname 可查看
    """
    
    @task
    def documented_task(c):
        """
        这是一个有详细文档的任务。
        
        这段文字会显示在 invoke --help documented-task 的输出中。
        注意：任务名中的下划线会自动转换为连字符。
        """
        print("任务执行完成")
    
    ctx = Context()
    documented_task(ctx)
    print("\n提示: 在命令行运行 'invoke --help documented-task' 查看帮助")
# endregion
