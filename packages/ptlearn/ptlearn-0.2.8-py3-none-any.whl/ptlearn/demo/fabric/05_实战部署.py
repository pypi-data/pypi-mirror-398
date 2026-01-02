"""
Fabric 实战部署
===============
完整的部署脚本示例，展示如何用 Fabric 自动化部署应用

包含：
- 项目部署流程
- 服务管理
- 数据库备份
- 日志管理
"""

from fabric import Connection, Config, ThreadingGroup
from datetime import datetime
from pathlib import Path

# region 示例1: 简单的 Web 应用部署
if False:  # 改为 True 可运行此示例
    def deploy_web_app(host: str, user: str, project_path: str):
        """部署 Web 应用的基本流程"""
        with Connection(f"{user}@{host}") as conn:
            with conn.cd(project_path):
                # 1. 拉取最新代码
                print("拉取代码...")
                conn.run("git fetch origin")
                conn.run("git reset --hard origin/main")
                
                # 2. 安装依赖
                print("安装依赖...")
                with conn.prefix("source venv/bin/activate"):
                    conn.run("pip install -r requirements.txt")
                
                # 3. 数据库迁移
                print("数据库迁移...")
                with conn.prefix("source venv/bin/activate"):
                    conn.run("python manage.py migrate")
                
                # 4. 收集静态文件
                print("收集静态文件...")
                with conn.prefix("source venv/bin/activate"):
                    conn.run("python manage.py collectstatic --noinput")
                
                # 5. 重启服务
                print("重启服务...")
                conn.sudo("systemctl restart gunicorn")
                conn.sudo("systemctl restart nginx")
                
                print("部署完成！")
    
    # 执行部署
    deploy_web_app("192.168.1.100", "deploy", "/var/www/myapp")
# endregion

# region 示例2: 带回滚的部署
if False:  # 改为 True 可运行此示例
    def deploy_with_rollback(conn: Connection, project_path: str):
        """支持回滚的部署流程"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with conn.cd(project_path):
            # 备份当前版本
            print("备份当前版本...")
            conn.run(f"cp -r current releases/{timestamp}")
            
            try:
                # 部署新版本
                print("部署新版本...")
                conn.run("git pull origin main")
                
                with conn.prefix("source venv/bin/activate"):
                    conn.run("pip install -r requirements.txt")
                    conn.run("python manage.py migrate")
                
                # 健康检查
                result = conn.run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health")
                if result.stdout.strip() != "200":
                    raise Exception("健康检查失败")
                
                print("部署成功！")
                
            except Exception as e:
                # 回滚
                print(f"部署失败: {e}")
                print("正在回滚...")
                conn.run(f"rm -rf current && cp -r releases/{timestamp} current")
                conn.sudo("systemctl restart gunicorn")
                print("回滚完成")
                raise
    
    with Connection("deploy@server") as conn:
        deploy_with_rollback(conn, "/var/www/myapp")
# endregion

# region 示例3: 数据库备份
if False:  # 改为 True 可运行此示例
    def backup_database(conn: Connection, db_name: str, backup_dir: str):
        """备份 PostgreSQL 数据库"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/{db_name}_{timestamp}.sql.gz"
        
        # 创建备份目录
        conn.run(f"mkdir -p {backup_dir}")
        
        # 执行备份
        print(f"备份数据库 {db_name}...")
        conn.sudo(
            f"pg_dump {db_name} | gzip > {backup_file}",
            user="postgres"
        )
        
        # 清理旧备份（保留最近7天）
        conn.run(f"find {backup_dir} -name '*.sql.gz' -mtime +7 -delete")
        
        print(f"备份完成: {backup_file}")
        return backup_file
    
    def restore_database(conn: Connection, db_name: str, backup_file: str):
        """恢复数据库"""
        print(f"恢复数据库 {db_name} from {backup_file}...")
        conn.sudo(
            f"gunzip -c {backup_file} | psql {db_name}",
            user="postgres"
        )
        print("恢复完成")
    
    with Connection("admin@db-server") as conn:
        backup_database(conn, "myapp_production", "/var/backups/db")
# endregion

# region 示例4: 日志管理
if False:  # 改为 True 可运行此示例
    def tail_logs(conn: Connection, log_file: str, lines: int = 100):
        """查看日志尾部"""
        result = conn.run(f"tail -n {lines} {log_file}", hide=True)
        return result.stdout
    
    def search_logs(conn: Connection, log_file: str, pattern: str):
        """搜索日志"""
        result = conn.run(f"grep -i '{pattern}' {log_file}", hide=True, warn=True)
        return result.stdout
    
    def download_logs(conn: Connection, log_file: str, local_dir: str = "./logs"):
        """下载日志文件"""
        Path(local_dir).mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_file = f"{local_dir}/app_{timestamp}.log"
        conn.get(log_file, local_file)
        print(f"日志已下载到: {local_file}")
        return local_file
    
    with Connection("admin@server") as conn:
        # 查看最近的错误
        errors = search_logs(conn, "/var/log/app/error.log", "ERROR")
        print(errors)
        
        # 下载日志
        download_logs(conn, "/var/log/app/app.log")
# endregion

# region 示例5: 多服务器部署
if False:  # 改为 True 可运行此示例
    def deploy_to_cluster(hosts: list, project_path: str):
        """部署到服务器集群"""
        # 使用 ThreadingGroup 并行部署
        group = ThreadingGroup(*hosts)
        
        print("开始集群部署...")
        
        # 1. 拉取代码
        with group.cd(project_path):
            group.run("git pull origin main", hide=True)
        
        # 2. 安装依赖
        with group.cd(project_path):
            with group.prefix("source venv/bin/activate"):
                group.run("pip install -r requirements.txt", hide=True)
        
        # 3. 逐台重启（避免服务中断）
        for host in hosts:
            with Connection(host) as conn:
                print(f"重启 {host}...")
                conn.sudo("systemctl restart gunicorn")
                # 等待服务启动
                conn.run("sleep 5")
                # 健康检查
                result = conn.run("curl -s localhost:8000/health", hide=True, warn=True)
                if "ok" in result.stdout.lower():
                    print(f"  {host}: 正常")
                else:
                    print(f"  {host}: 异常！")
        
        print("集群部署完成")
    
    hosts = [
        "deploy@web-01",
        "deploy@web-02",
        "deploy@web-03",
    ]
    deploy_to_cluster(hosts, "/var/www/myapp")
# endregion

# region 示例6: 模拟演示
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("Fabric 实战部署演示（模拟）")
    print("=" * 50)
    
    print("\n1. 基本部署流程：")
    steps = [
        "git pull origin main",
        "pip install -r requirements.txt",
        "python manage.py migrate",
        "python manage.py collectstatic",
        "systemctl restart gunicorn",
    ]
    for i, step in enumerate(steps, 1):
        print(f"   {i}. {step}")
    
    print("\n2. 带回滚的部署：")
    print("   - 部署前备份当前版本")
    print("   - 部署失败时自动回滚")
    print("   - 健康检查确认服务正常")
    
    print("\n3. 数据库备份：")
    print('   pg_dump mydb | gzip > backup.sql.gz')
    print('   find /backups -mtime +7 -delete  # 清理旧备份')
    
    print("\n4. 集群部署策略：")
    print("   - 并行拉取代码和安装依赖")
    print("   - 逐台重启避免服务中断")
    print("   - 每台重启后健康检查")
    
    # 模拟部署过程
    print("\n--- 模拟部署过程 ---")
    import time
    servers = ["web-01", "web-02", "web-03"]
    for server in servers:
        print(f"  部署 {server}...", end=" ", flush=True)
        time.sleep(0.3)
        print("✓")
    print("  部署完成！")
# endregion
