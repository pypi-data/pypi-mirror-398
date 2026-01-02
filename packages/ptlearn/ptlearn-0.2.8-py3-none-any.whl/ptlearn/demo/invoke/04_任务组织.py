"""
Invoke 任务组织
===============
学习如何组织任务：前置任务、任务集合、命名空间等。

适用版本: Python 3.6+
"""

from invoke import task, Context, Collection

# region 示例1: 前置任务（pre-tasks）
if True:  # 改为 False 可跳过此示例
    """
    使用 pre 参数指定任务执行前需要先执行的任务
    """
    
    @task
    def clean(c):
        """清理构建产物"""
        print("[clean] 清理旧文件...")
    
    @task
    def compile_code(c):
        """编译代码"""
        print("[compile] 编译源代码...")
    
    @task(pre=[clean, compile_code])
    def build(c):
        """构建项目（先清理，再编译）"""
        print("[build] 打包构建产物...")
    
    ctx = Context()
    print("=== 执行 build 任务 ===")
    # build 会自动先执行 clean 和 compile_code
    build(ctx)
# endregion

# region 示例2: 后置任务（post-tasks）
if True:  # 改为 False 可跳过此示例
    """
    使用 post 参数指定任务执行后需要执行的任务
    """
    
    @task
    def notify(c):
        """发送通知"""
        print("[notify] 发送完成通知...")
    
    @task
    def cleanup(c):
        """清理临时文件"""
        print("[cleanup] 清理临时文件...")
    
    @task(post=[notify, cleanup])
    def deploy(c):
        """部署应用"""
        print("[deploy] 部署应用到服务器...")
    
    ctx = Context()
    print("=== 执行 deploy 任务 ===")
    deploy(ctx)
# endregion

# region 示例3: 任务调用其他任务
if True:  # 改为 False 可跳过此示例
    """
    在任务内部可以直接调用其他任务函数
    """
    from invoke import call
    
    @task
    def step1(c):
        """步骤1"""
        print("执行步骤1")
    
    @task
    def step2(c, message="default"):
        """步骤2"""
        print(f"执行步骤2: {message}")
    
    @task
    def workflow(c):
        """工作流：组合多个步骤"""
        print("=== 开始工作流 ===")
        step1(c)
        step2(c, message="来自 workflow")
        print("=== 工作流完成 ===")
    
    ctx = Context()
    workflow(ctx)
# endregion

# region 示例4: 使用 call() 传递参数给前置任务
if True:  # 改为 False 可跳过此示例
    """
    使用 call() 可以为前置任务指定参数
    """
    from invoke import call
    
    @task
    def setup_env(c, env="dev"):
        """设置环境"""
        print(f"[setup] 配置 {env} 环境")
    
    @task
    def run_tests(c, coverage=False):
        """运行测试"""
        cov_msg = "（含覆盖率）" if coverage else ""
        print(f"[test] 运行测试{cov_msg}")
    
    # 使用 call() 为前置任务传递参数
    @task(pre=[
        call(setup_env, env="test"),
        call(run_tests, coverage=True)
    ])
    def ci(c):
        """CI 流水线"""
        print("[ci] CI 检查完成")
    
    ctx = Context()
    print("=== 执行 CI 任务 ===")
    ci(ctx)
# endregion

# region 示例5: Collection（任务集合）
if True:  # 改为 False 可跳过此示例
    """
    Collection 用于组织和分组任务
    可以创建命名空间，避免任务名冲突
    """
    
    # 定义一些任务
    @task
    def db_migrate(c):
        """数据库迁移"""
        print("执行数据库迁移")
    
    @task
    def db_seed(c):
        """填充测试数据"""
        print("填充测试数据")
    
    @task
    def db_reset(c):
        """重置数据库"""
        print("重置数据库")
    
    # 创建 db 命名空间
    db = Collection('db')
    db.add_task(db_migrate, name='migrate')
    db.add_task(db_seed, name='seed')
    db.add_task(db_reset, name='reset')
    
    # 演示集合中的任务
    print("=== db 命名空间中的任务 ===")
    for task_name in db.tasks:
        print(f"  - db.{task_name}")
    
    # 执行任务
    ctx = Context()
    print("\n=== 执行 db.migrate ===")
    db.tasks['migrate'](ctx)
# endregion

# region 示例6: 嵌套 Collection
if True:  # 改为 False 可跳过此示例
    """
    Collection 可以嵌套，创建多级命名空间
    """
    
    @task
    def frontend_build(c):
        print("构建前端")
    
    @task
    def frontend_test(c):
        print("测试前端")
    
    @task
    def backend_build(c):
        print("构建后端")
    
    @task
    def backend_test(c):
        print("测试后端")
    
    # 创建子集合
    frontend = Collection('frontend')
    frontend.add_task(frontend_build, name='build')
    frontend.add_task(frontend_test, name='test')
    
    backend = Collection('backend')
    backend.add_task(backend_build, name='build')
    backend.add_task(backend_test, name='test')
    
    # 创建根集合并添加子集合
    ns = Collection()
    ns.add_collection(frontend)
    ns.add_collection(backend)
    
    print("=== 命名空间结构 ===")
    print("frontend:")
    for name in frontend.tasks:
        print(f"  - frontend.{name}")
    print("backend:")
    for name in backend.tasks:
        print(f"  - backend.{name}")
# endregion
