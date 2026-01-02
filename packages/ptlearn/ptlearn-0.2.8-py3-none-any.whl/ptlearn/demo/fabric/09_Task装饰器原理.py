"""
Task 装饰器原理
===============
讲解函数被 @task 装饰后变成 Task 类实例的好处

@task 装饰器将普通函数转换为 Task 实例，这种设计带来了：
1. 元数据存储 - 保存任务名称、文档、参数配置等
2. 任务依赖 - 支持 pre/post 前置后置任务
3. 参数处理 - 自动类型转换和验证
4. 统一接口 - 任务发现、注册、执行的标准化
5. 可调用性 - Task 实例仍可像函数一样调用
"""

from invoke import task, Task, Context
import inspect

# region 示例1: 普通函数 vs Task 实例
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例1: 普通函数 vs Task 实例")
    print("=" * 60)
    
    # 普通函数
    def normal_func(ctx):
        """普通函数的文档"""
        print("普通函数执行")
    
    # 被 @task 装饰的函数
    @task
    def task_func(ctx):
        """Task 函数的文档"""
        print("Task 执行")
    
    print(f"普通函数类型: {type(normal_func)}")
    print(f"Task 类型:     {type(task_func)}")
    print(f"是否为 Task 实例: {isinstance(task_func, Task)}")
    print()
# endregion

# region 示例2: 好处一 - 元数据存储
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例2: 好处一 - 元数据存储")
    print("=" * 60)
    
    @task(name="custom-name", help={"name": "用户名称"})
    def greet(ctx, name="World"):
        """问候任务 - 这段文档会被保存"""
        print(f"Hello, {name}!")
    
    # Task 实例存储了丰富的元数据
    print("Task 实例的元数据属性:")
    print(f"  .name  = {greet.name!r}")      # 任务名称（可自定义）
    print(f"  .body  = {greet.body}")        # 原始函数引用
    print(f"  .help  = {greet.help}")        # 参数帮助信息
    print(f"  .__doc__ = {greet.__doc__!r}") # 文档字符串
    print()
    
    # 普通函数只有 __doc__ 和 __name__，没有这些扩展属性
    print("对比：普通函数无法存储这些额外信息")
    print()
# endregion

# region 示例3: 好处二 - 任务依赖（pre/post）
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例3: 好处二 - 任务依赖（pre/post）")
    print("=" * 60)
    
    @task
    def clean(ctx):
        """清理任务"""
        print("  [clean] 清理旧文件")
    
    @task
    def lint(ctx):
        """代码检查"""
        print("  [lint] 检查代码风格")
    
    @task
    def notify(ctx):
        """通知任务"""
        print("  [notify] 发送完成通知")
    
    # pre: 前置任务，post: 后置任务
    @task(pre=[clean, lint], post=[notify])
    def build(ctx):
        """构建任务 - 自动执行前置和后置任务"""
        print("  [build] 构建项目")
    
    print("build 任务的依赖配置:")
    print(f"  前置任务 (pre):  {[t.name for t in build.pre]}")
    print(f"  后置任务 (post): {[t.name for t in build.post]}")
    print()
    
    # 普通函数无法声明式地定义依赖关系
    print("普通函数需要手动调用依赖，无法声明式配置")
    print()
# endregion

# region 示例4: 好处三 - 参数配置
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例4: 好处三 - 参数配置")
    print("=" * 60)
    
    @task(
        positional=["count"],           # 位置参数
        optional=["verbose"],           # 可选参数
        iterable=["files"],             # 可重复参数
        help={
            "count": "处理数量",
            "verbose": "详细输出",
            "files": "要处理的文件列表"
        }
    )
    def process(ctx, count, verbose=False, files=None):
        """处理任务 - 展示参数配置"""
        print(f"处理 {count} 项, verbose={verbose}, files={files}")
    
    print("Task 的参数配置:")
    print(f"  位置参数:   {process.positional}")
    print(f"  可选参数:   {process.optional}")
    print(f"  可重复参数: {process.iterable}")
    print(f"  帮助信息:   {process.help}")
    print()
    
    print("命令行调用示例:")
    print("  invoke process 10                    # count=10")
    print("  invoke process 10 --verbose          # 启用详细模式")
    print("  invoke process 10 -f a.txt -f b.txt  # 多个文件")
    print()
# endregion

# region 示例5: 好处四 - 任务发现与注册
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例5: 好处四 - 任务发现与注册")
    print("=" * 60)
    
    # 模拟一个模块中定义的内容
    class FakeModule:
        @task
        def deploy(ctx):
            """部署任务"""
            pass
        
        @task
        def rollback(ctx):
            """回滚任务"""
            pass
        
        def helper_func():
            """普通辅助函数"""
            pass
        
        CONFIG = {"env": "prod"}
    
    # 自动发现所有 Task 实例
    def discover_tasks(module):
        """从模块中发现所有任务"""
        tasks = {}
        for name, obj in vars(module).items():
            if isinstance(obj, Task):  # 关键：通过类型判断
                tasks[name] = obj
        return tasks
    
    found = discover_tasks(FakeModule)
    print("自动发现的任务:")
    for name, t in found.items():
        print(f"  {name}: {t.__doc__}")
    print()
    
    print("普通函数无法通过类型区分是否为「任务」")
    print("Task 实例提供了统一的类型标识")
    print()
# endregion

# region 示例6: 好处五 - 保持可调用性
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例6: 好处五 - 保持可调用性")
    print("=" * 60)
    
    @task
    def add(ctx, a, b):
        """加法任务"""
        result = int(a) + int(b)
        print(f"  {a} + {b} = {result}")
        return result
    
    ctx = Context()
    
    # Task 实例可以像函数一样调用
    print("Task 实例可直接调用:")
    result = add(ctx, 3, 5)
    print(f"  返回值: {result}")
    print()
    
    # 同时可以访问原始函数
    print("也可以访问原始函数 (.body):")
    print(f"  add.body = {add.body}")
    print(f"  函数签名: {inspect.signature(add.body)}")
    print()
# endregion

# region 示例7: 综合对比总结
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例7: 综合对比总结")
    print("=" * 60)
    
    def normal(ctx):
        """普通函数"""
        pass
    
    @task(pre=[], post=[], help={"x": "参数x"})
    def decorated(ctx, x=1):
        """装饰后的任务"""
        pass
    
    print("普通函数具有的属性:")
    print(f"  __name__, __doc__, __annotations__")
    print()
    
    print("Task 实例额外具有的属性:")
    attrs = ["name", "body", "help", "pre", "post", "positional", "optional", "iterable"]
    for attr in attrs:
        val = getattr(decorated, attr, "N/A")
        print(f"  .{attr:12} = {val}")
    print()
    
    print("总结：@task 装饰器将函数升级为功能丰富的 Task 对象")
    print("      既保留了函数的可调用性，又增加了任务管理所需的元数据")
    print()
# endregion
