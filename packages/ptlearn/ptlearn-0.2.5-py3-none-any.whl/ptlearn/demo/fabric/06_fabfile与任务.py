"""
Fabric fabfile 与任务
=====================
使用 fabfile.py 组织部署任务，通过命令行调用

fabfile.py 是 Fabric 的约定配置文件
可以通过 fab 命令调用其中定义的任务

安装命令行工具: pip install fabric
"""

from fabric import task, Connection, Config
from invoke import Collection

# region 示例1: 基本任务定义
if False:  # 改为 True 可运行此示例
    # 在 fabfile.py 中定义任务
    # 使用 @task 装饰器
    
    @task
    def hello(ctx):
        """打印问候语（本地任务）"""
        print("Hello from Fabric!")
    
    @task
    def uptime(ctx, host):
        """查看服务器运行时间"""
        with Connection(host) as conn:
            result = conn.run("uptime", hide=True)
            print(result.stdout.strip())
    
    @task
    def disk_usage(ctx, host):
        """查看磁盘使用情况"""
        with Connection(host) as conn:
            result = conn.run("df -h", hide=True)
            print(result.stdout)
    
    # 命令行调用：
    # fab hello
    # fab uptime --host user@server
    # fab disk-usage --host user@server
# endregion

# region 示例2: 带参数的任务
if False:  # 改为 True 可运行此示例
    @task
    def deploy(ctx, host, branch="main", migrate=True):
        """
        部署应用
        
        参数:
            host: 目标服务器
            branch: Git 分支（默认 main）
            migrate: 是否执行数据库迁移（默认 True）
        """
        with Connection(host) as conn:
            with conn.cd("/var/www/app"):
                conn.run(f"git checkout {branch}")
                conn.run("git pull")
                
                with conn.prefix("source venv/bin/activate"):
                    conn.run("pip install -r requirements.txt")
                    if migrate:
                        conn.run("python manage.py migrate")
                
                conn.sudo("systemctl restart gunicorn")
        
        print(f"部署完成: {branch} -> {host}")
    
    # 命令行调用：
    # fab deploy --host user@server
    # fab deploy --host user@server --branch develop
    # fab deploy --host user@server --no-migrate
# endregion

# region 示例3: 任务组合
if False:  # 改为 True 可运行此示例
    @task
    def backup(ctx, host):
        """备份数据库"""
        with Connection(host) as conn:
            conn.sudo("pg_dump mydb > /tmp/backup.sql", user="postgres")
            conn.get("/tmp/backup.sql", "./backups/")
        print("备份完成")
    
    @task
    def test(ctx, host):
        """运行测试"""
        with Connection(host) as conn:
            with conn.cd("/var/www/app"):
                with conn.prefix("source venv/bin/activate"):
                    conn.run("pytest")
        print("测试通过")
    
    @task(pre=[backup, test])
    def release(ctx, host):
        """
        发布新版本
        会先执行 backup 和 test 任务
        """
        with Connection(host) as conn:
            with conn.cd("/var/www/app"):
                conn.run("git pull origin main")
                conn.sudo("systemctl restart gunicorn")
        print("发布完成")
    
    # 命令行调用：
    # fab release --host user@server
    # 会依次执行: backup -> test -> release
# endregion

# region 示例4: 使用 Collection 组织任务
if False:  # 改为 True 可运行此示例
    # 可以将任务组织成命名空间
    
    @task
    def start(ctx, host):
        """启动服务"""
        with Connection(host) as conn:
            conn.sudo("systemctl start gunicorn nginx")
    
    @task
    def stop(ctx, host):
        """停止服务"""
        with Connection(host) as conn:
            conn.sudo("systemctl stop gunicorn nginx")
    
    @task
    def restart(ctx, host):
        """重启服务"""
        with Connection(host) as conn:
            conn.sudo("systemctl restart gunicorn nginx")
    
    @task
    def status(ctx, host):
        """查看服务状态"""
        with Connection(host) as conn:
            conn.run("systemctl status gunicorn nginx")
    
    # 创建命名空间
    service = Collection("service")
    service.add_task(start)
    service.add_task(stop)
    service.add_task(restart)
    service.add_task(status)
    
    # 在 fabfile.py 末尾添加:
    # namespace = Collection()
    # namespace.add_collection(service)
    
    # 命令行调用：
    # fab service.start --host user@server
    # fab service.status --host user@server
# endregion

# region 示例5: 配置文件
if False:  # 改为 True 可运行此示例
    # fabric.yaml 配置文件示例
    """
    # fabric.yaml
    user: deploy
    connect_kwargs:
      key_filename: ~/.ssh/deploy_key
    
    sudo:
      password: your_sudo_password
    
    # 自定义配置
    project:
      path: /var/www/myapp
      branch: main
    
    hosts:
      production:
        - web-01.example.com
        - web-02.example.com
      staging:
        - staging.example.com
    """
    
    # 在任务中使用配置
    @task
    def deploy_with_config(ctx):
        """使用配置文件部署"""
        # ctx.config 包含配置信息
        project_path = ctx.config.project.path
        branch = ctx.config.project.branch
        hosts = ctx.config.hosts.production
        
        for host in hosts:
            with Connection(host, config=ctx.config) as conn:
                with conn.cd(project_path):
                    conn.run(f"git checkout {branch}")
                    conn.run("git pull")
# endregion

# region 示例6: 模拟演示
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("Fabric fabfile 与任务演示（模拟）")
    print("=" * 50)
    
    print("\n1. 定义任务（fabfile.py）：")
    print("   from fabric import task")
    print("   ")
    print("   @task")
    print("   def deploy(ctx, host, branch='main'):")
    print("       with Connection(host) as conn:")
    print("           conn.run('git pull')")
    
    print("\n2. 命令行调用：")
    print("   fab deploy --host user@server")
    print("   fab deploy --host user@server --branch develop")
    print("   fab --list  # 列出所有任务")
    
    print("\n3. 任务依赖：")
    print("   @task(pre=[backup, test])")
    print("   def release(ctx, host):")
    print("       # 会先执行 backup 和 test")
    
    print("\n4. 任务命名空间：")
    print("   fab service.start --host server")
    print("   fab service.stop --host server")
    print("   fab db.backup --host server")
    
    print("\n5. 配置文件 fabric.yaml：")
    print("   user: deploy")
    print("   connect_kwargs:")
    print("     key_filename: ~/.ssh/key")
    print("   project:")
    print("     path: /var/www/app")
    
    # 模拟 fab --list 输出
    print("\n--- 模拟 fab --list ---")
    tasks = [
        ("deploy", "部署应用到服务器"),
        ("backup", "备份数据库"),
        ("service.start", "启动服务"),
        ("service.stop", "停止服务"),
        ("service.restart", "重启服务"),
    ]
    for name, desc in tasks:
        print(f"  {name:<20} {desc}")
# endregion
