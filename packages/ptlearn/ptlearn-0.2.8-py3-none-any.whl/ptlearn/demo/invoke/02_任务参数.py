"""
Invoke 任务参数
===============
深入了解 invoke 任务的参数定义、类型转换和参数装饰器的使用。

适用版本: Python 3.6+
"""

from invoke import task, Context

# region 示例1: 参数类型自动推断
if True:  # 改为 False 可跳过此示例
    """
    invoke 会根据默认值自动推断参数类型
    - 默认值为 int -> 命令行参数转换为 int
    - 默认值为 bool -> 命令行参数成为开关标志
    - 无默认值 -> 字符串类型
    """
    
    @task
    def typed_args(c, name, count=1, verbose=False):
        """
        演示参数类型推断
        
        Args:
            name: 字符串参数（无默认值）
            count: 整数参数（默认值为 int）
            verbose: 布尔开关（默认值为 bool）
        """
        if verbose:
            print(f"详细模式已开启")
        
        for i in range(count):
            print(f"[{i+1}] Hello, {name}!")
    
    ctx = Context()
    # 模拟命令行: invoke typed-args --name Alice --count 2 --verbose
    typed_args(ctx, name="Alice", count=2, verbose=True)
# endregion

# region 示例2: 使用 @task 装饰器的参数选项
if True:  # 改为 False 可跳过此示例
    """
    @task 装饰器支持多种参数配置选项
    """
    
    @task(
        help={
            'name': '要问候的人名',
            'shout': '是否大声喊出来'
        },
        optional=['name']  # 将 name 设为可选参数
    )
    def greet_with_help(c, name="World", shout=False):
        """带帮助信息的问候任务"""
        message = f"Hello, {name}!"
        if shout:
            message = message.upper()
        print(message)
    
    ctx = Context()
    greet_with_help(ctx)
    greet_with_help(ctx, name="Invoke", shout=True)
# endregion

# region 示例3: 位置参数与关键字参数
if True:  # 改为 False 可跳过此示例
    """
    使用 positional 指定哪些参数可以作为位置参数传递
    """
    
    @task(positional=['src', 'dst'])
    def copy_file(c, src, dst, force=False):
        """
        复制文件（演示位置参数）
        
        命令行用法: invoke copy-file source.txt dest.txt --force
        """
        action = "强制复制" if force else "复制"
        print(f"{action}: {src} -> {dst}")
    
    ctx = Context()
    # 位置参数方式调用
    copy_file(ctx, "source.txt", "dest.txt", force=True)
# endregion

# region 示例4: 可迭代参数（接收多个值）
if True:  # 改为 False 可跳过此示例
    """
    使用 iterable 让参数可以接收多个值
    命令行: invoke task --item a --item b --item c
    """
    
    @task(iterable=['items'])
    def process_items(c, items):
        """处理多个项目"""
        print(f"收到 {len(items)} 个项目:")
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item}")
    
    ctx = Context()
    # 模拟 --items a --items b --items c
    process_items(ctx, items=["apple", "banana", "cherry"])
# endregion

# region 示例5: 增量参数（计数器）
if True:  # 改为 False 可跳过此示例
    """
    使用 incrementable 创建计数器参数
    命令行: invoke task -v -v -v  (verbose=3)
    """
    
    @task(incrementable=['verbose'])
    def with_verbosity(c, verbose=0):
        """
        支持多级详细程度
        
        -v: 基本信息
        -vv: 详细信息  
        -vvv: 调试信息
        """
        print(f"详细级别: {verbose}")
        
        if verbose >= 1:
            print("  -> 显示基本信息")
        if verbose >= 2:
            print("  -> 显示详细信息")
        if verbose >= 3:
            print("  -> 显示调试信息")
    
    ctx = Context()
    with_verbosity(ctx, verbose=3)
# endregion

# region 示例6: 参数别名
if True:  # 改为 False 可跳过此示例
    """
    为参数设置短名称别名
    """
    from invoke import Argument
    
    # 方法1: 在函数签名中使用单字母参数名
    @task
    def with_short_args(c, n="World", v=False):
        """
        使用短参数名
        命令行: invoke with-short-args -n Alice -v
        """
        msg = f"Hello, {n}!"
        if v:
            print(f"[VERBOSE] {msg}")
        else:
            print(msg)
    
    ctx = Context()
    with_short_args(ctx, n="Invoke", v=True)
# endregion
