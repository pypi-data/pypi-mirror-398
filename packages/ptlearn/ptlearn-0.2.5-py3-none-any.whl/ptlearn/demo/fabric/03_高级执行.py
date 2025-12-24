"""
Fabric 高级执行
===============
更复杂的命令执行场景：sudo、环境变量、工作目录、超时等

核心功能：
- sudo(): 以 root 权限执行
- cd(): 切换工作目录
- prefix(): 命令前缀
- 环境变量设置
"""

from fabric import Connection, Config

# region 示例1: sudo 执行
if True:  # 改为 True 可运行此示例
    # 方式1: 使用 sudo() 方法
    with Connection("vagrant@u12") as conn:
        # 基本 sudo
        result = conn.sudo("apt update", hide=True, env={"LANG": "en_US.UTF-8"})
        print(result.stdout)
        
        # 指定 sudo 用户
        result = conn.sudo("whoami", user="www-data", hide=True)
        print(f"当前用户: {result.stdout.strip()}")
        
        # sudo 时提供密码（交互式）
        # result = conn.sudo("systemctl restart nginx")
    
    # 方式2: 通过 Config 预设 sudo 密码
    config = Config(overrides={"sudo": {"password": "vagrant"}})
    with Connection("vagrant@u12", config=config) as conn:
        conn.sudo("apt upgrade -y", hide=True)
# endregion

# region 示例2: 工作目录 (cd)
if False:  # 改为 True 可运行此示例
    with Connection("vagrant@u12") as conn:
        # 使用 cd 上下文管理器
        with conn.cd("/var/www/app"):
            conn.run("pwd")  # 输出: /var/www/app
            conn.run("ls -la")
            conn.run("git pull")
        
        # cd 可以嵌套
        with conn.cd("/home/user"):
            conn.run("pwd")  # /home/user
            with conn.cd("projects"):
                conn.run("pwd")  # /home/user/projects
                with conn.cd("myapp"):
                    conn.run("pwd")  # /home/user/projects/myapp
# endregion

# region 示例3: 命令前缀 (prefix)
if False:  # 改为 True 可运行此示例
    with Connection("vagrant@u12") as conn:
        # prefix 会在每个命令前添加指定内容
        # 常用于激活虚拟环境
        
        with conn.prefix("source /home/user/venv/bin/activate"):
            conn.run("which python")  # 虚拟环境中的 python
            conn.run("pip list")
            conn.run("python app.py")
        
        # 多个 prefix 可以嵌套
        with conn.prefix("export DEBUG=1"):
            with conn.prefix("source ~/.bashrc"):
                conn.run("echo $DEBUG")
                conn.run("python script.py")
# endregion

# region 示例4: 环境变量
if False:  # 改为 True 可运行此示例
    with Connection("vagrant@u12") as conn:
        # 方式1: 在命令中直接设置
        conn.run("DEBUG=1 python app.py")
        
        # 方式2: 使用 env 参数
        conn.run("python app.py", env={"DEBUG": "1", "PORT": "8080"})
        
        # 方式3: 使用 prefix
        with conn.prefix("export DEBUG=1"):
            conn.run("python app.py")
        
        # 方式4: 通过 Config 全局设置
        # 见下一个示例
# endregion

# region 示例5: 超时和重试
if False:  # 改为 True 可运行此示例
    from invoke.exceptions import CommandTimedOut
    
    with Connection("vagrant@u12") as conn:
        # 设置命令超时（秒）
        try:
            result = conn.run("sleep 60", timeout=5)
        except CommandTimedOut:
            print("命令执行超时！")
        
        # 连接超时在创建 Connection 时设置
        conn_with_timeout = Connection(
            "vagrant@u12",
            connect_timeout=10,  # 连接超时10秒
        )
# endregion

# region 示例6: 交互式输入
if False:  # 改为 True 可运行此示例
    with Connection("vagrant@u12") as conn:
        # 使用 watchers 自动响应交互式提示
        from invoke import Responder
        
        # 自动输入 yes
        yes_responder = Responder(
            pattern=r"Are you sure.*\?",
            response="yes\n"
        )
        
        conn.run("some_interactive_command", watchers=[yes_responder])
        
        # 自动输入密码
        password_responder = Responder(
            pattern=r"Password:",
            response="your_password\n"
        )
        
        conn.run("sudo -S apt update", watchers=[password_responder], hide=True)
# endregion

# region 示例7: 模拟演示
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("Fabric 高级执行演示（模拟）")
    print("=" * 50)
    
    print("\n1. sudo 执行：")
    print('   conn.sudo("apt update")')
    print('   conn.sudo("whoami", user="www-data")')
    print('   # 预设密码: Config(overrides={"sudo": {"password": "..."}})')
    
    print("\n2. 工作目录 cd()：")
    print('   with conn.cd("/var/www/app"):')
    print('       conn.run("git pull")')
    print('       conn.run("pip install -r requirements.txt")')
    
    print("\n3. 命令前缀 prefix()：")
    print('   with conn.prefix("source venv/bin/activate"):')
    print('       conn.run("python app.py")')
    
    print("\n4. 环境变量：")
    print('   conn.run("python app.py", env={"DEBUG": "1"})')
    print('   conn.run("DEBUG=1 python app.py")')
    
    print("\n5. 超时控制：")
    print('   conn.run("long_task", timeout=30)')
    print('   Connection("host", connect_timeout=10)')
    
    print("\n6. 交互式响应：")
    print('   responder = Responder(pattern=r"Password:", response="xxx\\n")')
    print('   conn.run("cmd", watchers=[responder])')
# endregion
