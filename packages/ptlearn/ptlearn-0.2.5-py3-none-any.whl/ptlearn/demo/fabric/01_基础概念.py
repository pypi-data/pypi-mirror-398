"""
Fabric 基础概念
===============
Fabric 是一个用于 SSH 远程执行命令和文件传输的 Python 库
适用于 Python 3.6+，需要安装: pip install fabric

核心概念：
- Connection: 与远程主机的 SSH 连接
- run(): 在远程主机执行命令
- local(): 在本地执行命令
- put()/get(): 文件上传/下载
"""

from fabric import Connection
from invoke import run as local_run

# region 示例1: 创建连接
if False:  # 改为 True 可运行此示例（需要有效的 SSH 主机）
    # 基本连接方式
    # 方式1: 使用用户名@主机名
    conn = Connection("vagrant@u12")
    
    # 方式2: 分开指定参数
    conn = Connection(
        host="192.168.1.100",
        user="root",
        port=22,  # 默认端口22，可省略
    )
    
    # 方式3: 使用密码连接（不推荐，建议使用密钥）
    conn = Connection(
        host="192.168.1.100",
        user="root",
        connect_kwargs={"password": "your_password"}
    )
    
    # 方式4: 使用私钥文件
    conn = Connection(
        host="192.168.1.100",
        user="root",
        connect_kwargs={"key_filename": "/path/to/private_key"}
    )
    
    print("连接对象创建成功（尚未实际连接）")
# endregion

# region 示例2: 执行远程命令
if True:  # 改为 True 可运行此示例
    conn = Connection("vagrant@u12")
    
    # run() 执行远程命令并返回 Result 对象
    result = conn.run("uname -a")
    
    # Result 对象的常用属性
    print(f"命令: {result.command}")
    print(f"标准输出: {result.stdout}")
    print(f"标准错误: {result.stderr}")
    print(f"返回码: {result.return_code}")
    print(f"是否成功: {result.ok}")
    print(f"是否失败: {result.failed}")
    
    # 隐藏输出（静默执行）
    # 设置 LANG 环境变量避免中文乱码
    result = conn.run("ls -la", hide=True, env={"LANG": "en_US.UTF-8"})
    print(f"静默执行结果: {result.stdout.strip()}")
    
    # 允许命令失败而不抛出异常
    # 使用 hide=True 隐藏输出，避免远程服务器 locale 导致的乱码
    result = conn.run("command_not_exist", warn=True, hide=True)
    if result.failed:
        print("命令执行失败，但程序继续运行")
# endregion

# region 示例3: 本地命令执行
if True:  # 改为 True 可运行此示例
    import platform
    
    # 使用 invoke 的 run 执行本地命令
    # 注意：这不需要 SSH 连接
    
    # 基本用法
    result = local_run("echo Hello from local", hide=True)
    print(f"本地输出: {result.stdout.strip()}")
    
    # 根据操作系统选择命令
    # 注意：invoke 在 Windows 上不支持 shell=True 参数
    if platform.system() == "Windows":
        result = local_run("dir", hide=True)
    else:
        result = local_run("ls -la", hide=True)
    print(f"目录列表:\n{result.stdout}")
    
    # Connection 对象也有 local() 方法
    # 注意：这里只是演示语法，实际执行需要有效的主机
    # conn = Connection("vagrant@u12")
    # result = conn.local("echo 本地命令", hide=True)
    # print(f"通过 Connection 执行本地命令: {result.stdout.strip()}")
# endregion

# region 示例4: 上下文管理器
if True:  # 改为 True 可运行此示例
    # 推荐使用 with 语句管理连接，确保资源正确释放
    with Connection("vagrant@u12") as conn:
        result = conn.run("whoami", hide=True)
        print(f"当前用户: {result.stdout.strip()}")
        
        result = conn.run("pwd", hide=True)
        print(f"当前目录: {result.stdout.strip()}")
    # 退出 with 块后连接自动关闭
    
    print("连接已自动关闭")
# endregion

# region 示例5: 模拟演示（无需真实服务器）
if False:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("Fabric 基础概念演示（模拟）")
    print("=" * 50)
    
    # 演示 Connection 对象的创建（不实际连接）
    print("\n1. 创建连接对象的几种方式：")
    print('   conn = Connection("vagrant@u12")')
    print('   conn = Connection(host="192.168.1.100", user="root")')
    print('   conn = Connection(host="...", connect_kwargs={"password": "..."})')
    
    print("\n2. 执行远程命令：")
    print('   result = conn.run("uname -a")')
    print('   result = conn.run("ls", hide=True)  # 静默执行')
    print('   result = conn.run("cmd", warn=True)  # 允许失败')
    
    print("\n3. Result 对象属性：")
    print("   result.stdout    - 标准输出")
    print("   result.stderr    - 标准错误")
    print("   result.return_code - 返回码")
    print("   result.ok / result.failed - 执行状态")
    
    print("\n4. 推荐使用上下文管理器：")
    print('   with Connection("user@host") as conn:')
    print('       conn.run("command")')
# endregion
