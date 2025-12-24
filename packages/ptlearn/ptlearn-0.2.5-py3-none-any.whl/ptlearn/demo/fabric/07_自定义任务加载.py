"""
自定义任务加载器
================
展示如何自己编写程序加载被 @task 装饰器装饰的函数
而不依赖 fab 命令行工具

核心原理：
1. @task 装饰器会将函数包装成 invoke.Task 对象
2. 可以通过模块的 __dict__ 或 inspect 模块找到这些 Task 对象
3. 直接调用 Task 对象或其内部函数即可执行任务
"""

from fabric import task, Connection
from invoke import Task, Context, Collection, Program
import inspect
import sys

# region 示例1: 定义一些任务供后续加载
@task
def hello(ctx):
    """打印问候语"""
    print("Hello from custom loader!")

@task
def greet(ctx, name="World"):
    """带参数的问候"""
    print(f"Hello, {name}!")

@task
def add(ctx, a, b):
    """计算两数之和"""
    result = int(a) + int(b)
    print(f"{a} + {b} = {result}")
    return result

@task
def server_info(ctx, host="localhost"):
    """获取服务器信息（模拟）"""
    print(f"正在获取 {host} 的信息...")
    print(f"  主机: {host}")
    print(f"  状态: 在线")
# endregion

# region 示例2: 从当前模块收集所有任务
def collect_tasks_from_module(module):
    """
    从模块中收集所有被 @task 装饰的函数
    
    返回: dict[任务名, Task对象]
    """
    tasks = {}
    for name, obj in vars(module).items():
        # Task 是 @task 装饰后的对象类型
        if isinstance(obj, Task):
            tasks[name] = obj
    return tasks

if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 从模块收集任务")
    print("=" * 50)
    
    # 获取当前模块
    current_module = sys.modules[__name__]
    tasks = collect_tasks_from_module(current_module)
    
    print(f"\n发现 {len(tasks)} 个任务:")
    for name, task_obj in tasks.items():
        # task_obj.body 是原始函数
        # task_obj.__doc__ 或 task_obj.body.__doc__ 是文档字符串
        doc = task_obj.body.__doc__ or "无描述"
        doc = doc.strip().split('\n')[0]  # 只取第一行
        print(f"  - {name}: {doc}")
# endregion

# region 示例3: 直接调用任务
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例3: 直接调用任务")
    print("=" * 50)
    
    # 创建一个 Context 对象（任务的第一个参数）
    ctx = Context()
    
    print("\n调用 hello 任务:")
    hello(ctx)
    
    print("\n调用 greet 任务（带参数）:")
    greet(ctx, name="Fabric")
    
    print("\n调用 add 任务:")
    add(ctx, a=10, b=20)
# endregion

# region 示例4: 构建简单的任务运行器
class SimpleTaskRunner:
    """简单的任务运行器"""
    
    def __init__(self):
        self.tasks = {}
        self.ctx = Context()
    
    def register(self, task_obj, name=None):
        """注册一个任务"""
        task_name = name or task_obj.name
        self.tasks[task_name] = task_obj
    
    def register_from_module(self, module):
        """从模块注册所有任务"""
        for name, obj in vars(module).items():
            if isinstance(obj, Task):
                self.register(obj, name)
    
    def list_tasks(self):
        """列出所有任务"""
        print("可用任务:")
        for name, task_obj in self.tasks.items():
            # 获取参数信息
            sig = inspect.signature(task_obj.body)
            params = [p for p in sig.parameters.keys() if p != 'ctx']
            params_str = f"({', '.join(params)})" if params else "()"
            
            doc = (task_obj.body.__doc__ or "").strip().split('\n')[0]
            print(f"  {name}{params_str}: {doc}")
    
    def run(self, task_name, **kwargs):
        """运行指定任务"""
        if task_name not in self.tasks:
            print(f"错误: 任务 '{task_name}' 不存在")
            return None
        
        task_obj = self.tasks[task_name]
        print(f">>> 执行任务: {task_name}")
        return task_obj(self.ctx, **kwargs)

if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例4: 使用 SimpleTaskRunner")
    print("=" * 50)
    
    runner = SimpleTaskRunner()
    runner.register_from_module(sys.modules[__name__])
    
    print()
    runner.list_tasks()
    
    print()
    runner.run("hello")
    
    print()
    runner.run("greet", name="Python")
    
    print()
    runner.run("add", a=100, b=200)
# endregion

# region 示例5: 从外部文件动态加载任务
def load_tasks_from_file(filepath):
    """
    从外部 Python 文件加载任务
    
    这是 fab 命令加载 fabfile.py 的简化版本
    """
    import importlib.util
    
    # 动态加载模块
    spec = importlib.util.spec_from_file_location("dynamic_tasks", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # 收集任务
    return collect_tasks_from_module(module)

if False:  # 改为 True 需要有实际的 fabfile.py 文件
    print("\n" + "=" * 50)
    print("示例5: 从外部文件加载任务")
    print("=" * 50)
    
    # 假设有一个 fabfile.py 文件
    tasks = load_tasks_from_file("fabfile.py")
    print(f"从 fabfile.py 加载了 {len(tasks)} 个任务")
# endregion

# region 示例6: 使用 invoke 的 Collection 和 Program
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例6: 使用 Collection 组织任务")
    print("=" * 50)
    
    # Collection 是 invoke 提供的任务容器
    ns = Collection()
    
    # 添加任务到 Collection
    ns.add_task(hello)
    ns.add_task(greet)
    ns.add_task(add)
    
    # 可以创建子命名空间
    server_ns = Collection("server")
    server_ns.add_task(server_info, name="info")
    ns.add_collection(server_ns)
    
    print("\nCollection 中的任务:")
    for task_name in ns.task_names:
        print(f"  - {task_name}")
    
    # 从 Collection 获取并执行任务
    print("\n从 Collection 执行任务:")
    ctx = Context()
    
    task_obj = ns.tasks["hello"]
    task_obj(ctx)
    
    task_obj = ns.tasks["greet"]
    task_obj(ctx, name="Collection")
# endregion

# region 示例7: 命令行风格的任务调用器
def parse_args(args):
    """解析命令行风格的参数"""
    task_name = None
    kwargs = {}
    
    i = 0
    while i < len(args):
        arg = args[i]
        if task_name is None and not arg.startswith("--"):
            task_name = arg
        elif arg.startswith("--"):
            key = arg[2:]  # 去掉 --
            if "=" in key:
                k, v = key.split("=", 1)
                kwargs[k] = v
            elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                kwargs[key] = args[i + 1]
                i += 1
            else:
                kwargs[key] = True
        i += 1
    
    return task_name, kwargs

class CLITaskRunner(SimpleTaskRunner):
    """命令行风格的任务运行器"""
    
    def run_from_args(self, args):
        """从命令行参数运行任务"""
        if not args:
            self.list_tasks()
            return
        
        task_name, kwargs = parse_args(args)
        
        if task_name is None:
            self.list_tasks()
        elif task_name == "--list":
            self.list_tasks()
        else:
            self.run(task_name, **kwargs)

if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例7: 命令行风格调用")
    print("=" * 50)
    
    cli = CLITaskRunner()
    cli.register_from_module(sys.modules[__name__])
    
    # 模拟命令行调用
    print("\n模拟: python runner.py greet --name=World")
    cli.run_from_args(["greet", "--name=World"])
    
    print("\n模拟: python runner.py add --a 5 --b 3")
    cli.run_from_args(["add", "--a", "5", "--b", "3"])
    
    print("\n模拟: python runner.py server_info --host=192.168.1.1")
    cli.run_from_args(["server_info", "--host=192.168.1.1"])
# endregion

# region 示例8: 完整的自定义 fab 替代品
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例8: 总结 - 自定义任务加载的核心原理")
    print("=" * 50)
    
    print("""
核心要点:

1. @task 装饰器的本质
   - 将函数包装成 invoke.Task 对象
   - Task 对象是可调用的，调用时执行原函数
   - task_obj.body 保存原始函数引用

2. 收集任务的方法
   - 遍历模块的 __dict__ 或 vars()
   - 检查对象是否是 Task 实例
   - 使用 importlib 动态加载外部模块

3. 执行任务的方法
   - 创建 Context 对象作为第一个参数
   - 直接调用 Task 对象: task_obj(ctx, **kwargs)
   - 或调用原函数: task_obj.body(ctx, **kwargs)

4. 组织任务的方法
   - 使用 Collection 创建命名空间
   - 支持嵌套的 Collection 实现层级结构

5. 实际应用场景
   - 自定义部署工具
   - CI/CD 流水线集成
   - 批量任务调度
   - 构建自己的任务管理框架
""")
# endregion

