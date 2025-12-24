"""
Fabric 文件传输
===============
使用 Fabric 进行文件上传和下载操作
支持单文件传输，目录传输需要配合其他方法

核心方法：
- put(): 上传本地文件到远程
- get(): 下载远程文件到本地
"""

from fabric import Connection
from pathlib import Path

# region 示例1: 上传文件 (put)
if False:  # 改为 True 可运行此示例
    with Connection("vagrant@u12") as conn:
        # 基本上传：本地文件 -> 远程路径
        conn.put("local_file.txt", "/home/vagrant/file.txt")
        
        # 上传到远程目录（保持原文件名）
        conn.put("local_file.txt", "/home/vagrant/")
        
        # 使用 Path 对象
        local_path = Path("./data/config.json")
        conn.put(local_path, "/etc/app/config.json")
        
        # put() 返回 Result 对象，包含传输信息
        result = conn.put("app.py", "/home/user/")
        print(f"本地路径: {result.local}")
        print(f"远程路径: {result.remote}")
# endregion

# region 示例2: 下载文件 (get)
if False:  # 改为 True 可运行此示例
    with Connection("vagrant@u12") as conn:
        # 基本下载：远程文件 -> 本地路径
        conn.get("/remote/path/file.txt", "local_file.txt")
        
        # 下载到本地目录（保持原文件名）
        conn.get("/var/log/app.log", "./logs/")
        
        # 使用 Path 对象
        local_path = Path("./backup")
        conn.get("/etc/nginx/nginx.conf", local_path / "nginx.conf")
        
        # get() 同样返回 Result 对象
        result = conn.get("/home/user/data.csv", "./")
        print(f"远程路径: {result.remote}")
        print(f"本地路径: {result.local}")
# endregion

# region 示例3: 传输目录（跨平台方案）
if True:  # 改为 True 可运行此示例
    import shutil
    import tarfile
    
    with Connection("vagrant@u12") as conn:
        # Fabric 不直接支持目录传输，需要先打包
        # 使用 tar.gz 格式：Linux 自带 tar，无需额外安装
        
        # --- 上传目录 ---
        # 本地用 Python 打包为 tar.gz
        shutil.make_archive("project", "gztar", ".", ".")
        # 上传 tar.gz 文件
        conn.put("project.tar.gz", "/home/vagrant/")
        # 远程解压（tar 是 Linux 标准工具，无需安装）
        conn.run("cd /home/vagrant && tar -xzf project.tar.gz", hide=True)
        # 清理临时文件
        conn.run("rm /home/vagrant/project.tar.gz", hide=True)
        Path("project.tar.gz").unlink()
        
        print("目录上传完成")
        
        # # --- 下载目录 ---
        # # 远程打包（Linux 用 tar，更通用）
        # conn.run("cd /home/user && tar -czf backup.tar.gz ./data/", hide=True)
        # conn.get("/home/user/backup.tar.gz", "./")
        # conn.run("rm /home/user/backup.tar.gz", hide=True)
        # # 本地用 Python 解压 tar.gz（Windows 兼容）
        # shutil.unpack_archive("backup.tar.gz", ".", "gztar")
        # Path("backup.tar.gz").unlink()
        
        # print("目录下载完成")
# endregion

# region 示例4: 文件权限和所有者
if False:  # 改为 True 可运行此示例
    with Connection("vagrant@u12") as conn:
        # 上传后修改权限
        conn.put("script.sh", "/home/user/script.sh")
        conn.run("chmod +x /home/user/script.sh")
        
        # 上传后修改所有者（需要 sudo 权限）
        conn.put("config.conf", "/tmp/config.conf")
        conn.run("sudo mv /tmp/config.conf /etc/app/")
        conn.run("sudo chown root:root /etc/app/config.conf")
        conn.run("sudo chmod 644 /etc/app/config.conf")
        
        print("文件权限设置完成")
# endregion

# region 示例5: 模拟演示
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("Fabric 文件传输演示（模拟）")
    print("=" * 50)
    
    print("\n1. 上传文件 put()：")
    print('   conn.put("local.txt", "/remote/path/file.txt")')
    print('   conn.put("local.txt", "/remote/dir/")  # 保持文件名')
    print('   result = conn.put(...)  # 返回 Result 对象')
    
    print("\n2. 下载文件 get()：")
    print('   conn.get("/remote/file.txt", "local.txt")')
    print('   conn.get("/remote/file.txt", "./local_dir/")')
    
    print("\n3. 目录传输（需要打包）：")
    print("   上传: 本地 tar -> put -> 远程 untar")
    print("   下载: 远程 tar -> get -> 本地 untar")
    
    print("\n4. Result 对象属性：")
    print("   result.local  - 本地路径")
    print("   result.remote - 远程路径")
    
    print("\n5. 常见模式：")
    print('   conn.put("app.py", "/home/user/")')
    print('   conn.run("chmod +x /home/user/app.py")')
# endregion
