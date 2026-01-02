"""
Fabric Task 装饰器使用
======================
展示 Fabric 库中 @task 装饰器的各种使用方式

Fabric 的 @task 装饰器用于将函数标记为可被 fab 命令调用的任务。
它继承自 invoke 的 @task，但针对远程操作场景做了扩展。
"""

from fabric import task, Connection
from invoke import Context

# region 示例1: 最基础的 task 定义
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例1: 最基础的 task 定义")
    print("=" * 60)
    
    # 最简单的任务定义，只需要 @task 装饰器
    @task
    def hello(ctx):
        """最简单的任务"""
        print("Hello from Fabric!")
    
    # 本地执行（不需要远程连接）
    ctx = Context()
    hello(ctx)
    
    print(f"\n任务名称: {hello.name}")
    print(f"任务文档: {hello.__doc__}")
    print()
# endregion

# region 示例2: 带参数的 task
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例2: 带参数的 task")
    print("=" * 60)
    
    @task
    def greet(ctx, name, times=1):
        """
        问候任务
        
        命令行调用: fab greet --name=张三 --times=3
        """
        for i in range(int(times)):
            print(f"  第{i+1}次: 你好, {name}!")
    
    ctx = Context()
    greet(ctx, name="Fabric用户", times=2)
    
    print("\n命令行调用方式:")
    print("  fab greet --name=张三")
    print("  fab greet --name=张三 --times=3")
    print()
# endregion

# region 示例3: 自定义任务名称
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例3: 自定义任务名称")
    print("=" * 60)
    
    # 默认任务名 = 函数名（下划线转连字符）
    @task
    def deploy_app(ctx):
        """默认名称: deploy-app"""
        print("  使用默认名称")
    
    # 自定义任务名
    @task(name="release")
    def deploy_to_production(ctx):
        """自定义名称: release"""
        print("  使用自定义名称 'release'")
    
    print(f"deploy_app 的任务名: {deploy_app.name}")
    print(f"deploy_to_production 的任务名: {deploy_to_production.name}")
    
    ctx = Context()
    deploy_app(ctx)
    deploy_to_production(ctx)
    
    print("\n命令行调用:")
    print("  fab deploy-app        # 默认名称（下划线变连字符）")
    print("  fab release           # 自定义名称")
    print()
# endregion

# region 示例4: 参数帮助信息
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例4: 参数帮助信息")
    print("=" * 60)
    
    @task(
        help={
            "env": "部署环境: dev/staging/prod",
            "branch": "Git 分支名称",
            "force": "是否强制部署（跳过检查）"
        }
    )
    def deploy(ctx, env, branch="main", force=False):
        """部署应用到指定环境"""
        print(f"  部署 {branch} 分支到 {env} 环境")
        if force:
            print("  [强制模式] 跳过所有检查")
    
    print("任务帮助信息配置:")
    for param, desc in deploy.help.items():
        print(f"  --{param}: {desc}")
    
    ctx = Context()
    deploy(ctx, env="staging", branch="feature-x")
    
    print("\n运行 'fab deploy --help' 可查看完整帮助")
    print()
# endregion

# region 示例5: 位置参数与可选参数
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例5: 位置参数与可选参数")
    print("=" * 60)
    
    @task(
        positional=["filename"],  # 可作为位置参数传递
        optional=["backup"]       # 标记为可选（即使无默认值）
    )
    def process_file(ctx, filename, backup=True):
        """处理文件"""
        print(f"  处理文件: {filename}")
        print(f"  备份: {'是' if backup else '否'}")
    
    print("参数配置:")
    print(f"  位置参数: {process_file.positional}")
    print(f"  可选参数: {process_file.optional}")
    
    ctx = Context()
    process_file(ctx, "data.txt")
    
    print("\n命令行调用:")
    print("  fab process-file data.txt           # 位置参数")
    print("  fab process-file --filename=data.txt  # 命名参数")
    print("  fab process-file data.txt --no-backup # 禁用备份")
    print()
# endregion

# region 示例6: 可重复参数（iterable）
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例6: 可重复参数（iterable）")
    print("=" * 60)
    
    @task(iterable=["hosts"])
    def ping_hosts(ctx, hosts=None):
        """
        Ping 多个主机
        
        命令行: fab ping-hosts -H host1 -H host2 -H host3
        """
        hosts = hosts or []
        print(f"  要 ping 的主机列表: {hosts}")
        for host in hosts:
            print(f"    ping {host} ...")
    
    print(f"可重复参数: {ping_hosts.iterable}")
    
    ctx = Context()
    ping_hosts(ctx, hosts=["192.168.1.1", "192.168.1.2", "192.168.1.3"])
    
    print("\n命令行调用（-H 可重复使用）:")
    print("  fab ping-hosts -H server1 -H server2 -H server3")
    print()
# endregion

# region 示例7: 任务依赖（pre/post）
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例7: 任务依赖（pre/post）")
    print("=" * 60)
    
    @task
    def check_env(ctx):
        """检查环境"""
        print("  [pre] 检查环境配置...")
    
    @task
    def run_tests(ctx):
        """运行测试"""
        print("  [pre] 运行测试...")
    
    @task
    def notify_team(ctx):
        """通知团队"""
        print("  [post] 发送部署通知...")
    
    @task
    def cleanup(ctx):
        """清理临时文件"""
        print("  [post] 清理临时文件...")
    
    # 主任务：指定前置和后置任务
    @task(pre=[check_env, run_tests], post=[notify_team, cleanup])
    def full_deploy(ctx):
        """完整部署流程"""
        print("  [main] 执行部署...")
    
    print("full_deploy 任务的依赖:")
    print(f"  前置任务: {[t.name for t in full_deploy.pre]}")
    print(f"  后置任务: {[t.name for t in full_deploy.post]}")
    print()
    
    print("执行顺序演示（手动模拟）:")
    ctx = Context()
    for pre_task in full_deploy.pre:
        pre_task(ctx)
    full_deploy.body(ctx)  # 调用原始函数
    for post_task in full_deploy.post:
        post_task(ctx)
    print()
# endregion

# region 示例8: 默认任务（default=True）
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例8: 默认任务（default=True）")
    print("=" * 60)
    
    @task
    def build(ctx):
        """构建项目"""
        print("  构建中...")
    
    @task(default=True)
    def status(ctx):
        """
        查看状态（默认任务）
        
        当只运行 'fab' 不带任务名时执行此任务
        """
        print("  显示项目状态...")
    
    print(f"build 是默认任务: {getattr(build, 'default', False)}")
    print(f"status 是默认任务: {getattr(status, 'default', False)}")
    
    ctx = Context()
    status(ctx)
    
    print("\n命令行调用:")
    print("  fab          # 执行默认任务 status")
    print("  fab build    # 执行指定任务")
    print()
# endregion

# region 示例9: 结合 Connection 执行远程命令
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例9: 结合 Connection 执行远程命令")
    print("=" * 60)
    
    @task
    def remote_info(ctx, host="localhost"):
        """
        获取远程主机信息
        
        实际使用时需要有效的 SSH 连接
        """
        print(f"  目标主机: {host}")
        print("  （以下为模拟输出，实际需要有效的 SSH 连接）")
        print()
        print("  实际代码示例:")
        print("  ```")
        print("  @task")
        print("  def remote_info(ctx, host):")
        print("      conn = Connection(host)")
        print("      result = conn.run('uname -a', hide=True)")
        print("      print(result.stdout)")
        print("  ```")
    
    ctx = Context()
    remote_info(ctx, host="user@server.example.com")
    print()
# endregion

# region 示例10: 完整的 fabfile 示例
if True:  # 改为 False 可跳过此示例
    print("=" * 60)
    print("示例10: 完整的 fabfile 示例")
    print("=" * 60)
    
    print("一个典型的 fabfile.py 结构:")
    print()
    print('''```python
from fabric import task, Connection

@task
def test(ctx):
    """运行测试"""
    ctx.run("pytest")

@task
def build(ctx):
    """构建项目"""
    ctx.run("python -m build")

@task(pre=[test, build])
def deploy(ctx, host, env="staging"):
    """
    部署到远程服务器
    
    用法: fab deploy --host=user@server --env=prod
    """
    conn = Connection(host)
    conn.put("dist/*.whl", "/app/")
    conn.run(f"pip install /app/*.whl")
    print(f"已部署到 {env} 环境")

@task(default=True)
def status(ctx):
    """显示项目状态"""
    ctx.run("git status")
```''')
    print()
    
    print("常用命令:")
    print("  fab --list              # 列出所有任务")
    print("  fab test                # 运行测试")
    print("  fab deploy --host=xxx   # 部署")
    print("  fab                     # 执行默认任务")
    print()
# endregion
