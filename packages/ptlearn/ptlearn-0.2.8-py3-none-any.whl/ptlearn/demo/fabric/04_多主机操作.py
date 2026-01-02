"""
Fabric 多主机操作
=================
同时管理多台服务器，批量执行命令

核心概念：
- Group: 主机组，串行执行
- SerialGroup: 串行执行（同 Group）
- ThreadingGroup: 并行执行（多线程）
"""

from fabric import Connection, SerialGroup, ThreadingGroup
from fabric.exceptions import GroupException

# region 示例1: SerialGroup 串行执行
if False:  # 改为 True 可运行此示例
    # 创建主机组（串行执行，一台接一台）
    hosts = SerialGroup(
        "user@host1",
        "user@host2",
        "user@host3",
    )
    
    # 在所有主机上执行命令
    results = hosts.run("uname -a", hide=True)
    
    # results 是一个字典，key 是 Connection，value 是 Result
    for conn, result in results.items():
        print(f"{conn.host}: {result.stdout.strip()}")
    
    # 也可以执行其他操作
    hosts.put("config.json", "/etc/app/")
    hosts.get("/var/log/app.log", "./logs/{host}/")  # {host} 会被替换
# endregion

# region 示例2: ThreadingGroup 并行执行
if False:  # 改为 True 可运行此示例
    # 并行执行（多线程，速度更快）
    hosts = ThreadingGroup(
        "user@host1",
        "user@host2",
        "user@host3",
    )
    
    # 并行执行命令
    results = hosts.run("apt update && apt upgrade -y", hide=True)
    
    for conn, result in results.items():
        print(f"{conn.host}: 更新完成，返回码 {result.return_code}")
    
    # 注意：并行执行时输出可能交错
    # 建议使用 hide=True 然后统一处理结果
# endregion

# region 示例3: 从列表创建主机组
if False:  # 改为 True 可运行此示例
    # 从配置或文件读取主机列表
    host_list = [
        "user@192.168.1.101",
        "user@192.168.1.102",
        "user@192.168.1.103",
    ]
    
    # 使用 * 解包创建组
    group = ThreadingGroup(*host_list)
    
    # 或者使用 from_connections
    connections = [Connection(h) for h in host_list]
    # group = ThreadingGroup.from_connections(connections)
    
    results = group.run("hostname", hide=True)
    for conn, result in results.items():
        print(f"主机名: {result.stdout.strip()}")
# endregion

# region 示例4: 错误处理
if False:  # 改为 True 可运行此示例
    hosts = ThreadingGroup("user@host1", "user@host2", "user@host3")
    
    try:
        # 如果某台主机执行失败，默认会抛出 GroupException
        results = hosts.run("some_command_that_might_fail")
    except GroupException as e:
        # e.result 包含所有结果（成功和失败的）
        print("部分主机执行失败：")
        for conn, result in e.result.items():
            if isinstance(result, Exception):
                print(f"  {conn.host}: 错误 - {result}")
            else:
                print(f"  {conn.host}: 成功")
    
    # 或者使用 warn=True 忽略错误继续执行
    results = hosts.run("command", warn=True, hide=True)
    for conn, result in results.items():
        if result.failed:
            print(f"{conn.host}: 失败")
        else:
            print(f"{conn.host}: 成功")
# endregion

# region 示例5: 官方配置文件方式
if False:  # 改为 True 可运行此示例
    from fabric import Config
    
    # ========================================
    # 方式1: fabric.yaml（官方配置文件）
    # ========================================
    # Fabric 会自动按顺序查找以下位置的配置文件：
    #   - /etc/fabric.yaml
    #   - ~/.fabric.yaml
    #   - ./fabric.yaml（当前目录）
    #
    # fabric.yaml 示例：
    # ---
    # user: deploy                    # 默认用户
    # connect_kwargs:
    #   key_filename: /path/to/key    # 默认密钥
    # sudo:
    #   password: mypassword          # sudo 密码
    # timeouts:
    #   connect: 10                   # 连接超时
    # load_ssh_configs: true          # 是否加载 SSH config
    
    # 使用时，Connection 会自动读取这些默认值
    conn = Connection("myhost")  # 自动使用 fabric.yaml 中的 user、key 等
    
    # ========================================
    # 方式2: SSH config（推荐用于多主机）
    # ========================================
    # Fabric 自动读取 ~/.ssh/config，这是管理多主机的官方推荐方式
    #
    # ~/.ssh/config 示例：
    # Host web-01
    #     HostName 192.168.1.101
    #     User deploy
    #     Port 22
    #     IdentityFile ~/.ssh/web_key
    #
    # Host web-02
    #     HostName 192.168.1.102
    #     User deploy
    #     IdentityFile ~/.ssh/web_key
    #
    # Host db-01
    #     HostName 192.168.1.103
    #     User admin
    #     Port 2222
    #     IdentityFile ~/.ssh/db_key
    
    # 直接使用 Host 别名连接，Fabric 自动读取对应配置
    hosts = ThreadingGroup("web-01", "web-02", "db-01")
    results = hosts.run("hostname", hide=True)
    
    # ========================================
    # 方式3: 结合 fabric.yaml 和 SSH config
    # ========================================
    # fabric.yaml 设置全局默认值
    # SSH config 设置每台主机的具体参数
    # Connection 参数优先级：代码参数 > SSH config > fabric.yaml
    
    # 禁用 SSH config 加载（如需要）
    # 在 fabric.yaml 中设置：
    # load_ssh_configs: false
# endregion

# region 示例6: 自定义配置文件方式
if False:  # 改为 True 可运行此示例
    import json
    from fabric import Config
    
    # 如果需要更灵活的配置，可以自定义配置文件
    # hosts.json 示例：
    # {
    #     "hosts": [
    #         {"host": "192.168.1.101", "user": "deploy", "key": "~/.ssh/key1"},
    #         {"host": "192.168.1.102", "user": "admin", "port": 2222}
    #     ]
    # }
    
    def load_hosts(config_path: str) -> list[Connection]:
        """从 JSON 配置文件加载主机"""
        from pathlib import Path
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
        
        connections = []
        for h in data["hosts"]:
            connect_kwargs = {}
            if key := h.get("key"):
                connect_kwargs["key_filename"] = str(Path(key).expanduser())
            if pwd := h.get("password"):
                connect_kwargs["password"] = pwd
            
            config = Config(overrides={
                "sudo": {"password": h.get("sudo_password", "")},
                "connect_kwargs": connect_kwargs,
            })
            connections.append(Connection(
                host=h["host"],
                user=h.get("user", "root"),
                port=h.get("port", 22),
                config=config,
            ))
        return connections
    
    # connections = load_hosts("hosts.json")
    # group = ThreadingGroup.from_connections(connections)
# endregion





# region 示例7: 模拟演示
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("Fabric 多主机操作演示（模拟）")
    print("=" * 50)
    
    print("\n1. SerialGroup（串行执行）：")
    print('   hosts = SerialGroup("user@host1", "user@host2")')
    print('   results = hosts.run("uname -a")')
    print("   # 一台接一台执行，适合有依赖的场景")
    
    print("\n2. ThreadingGroup（并行执行）：")
    print('   hosts = ThreadingGroup("user@host1", "user@host2")')
    print('   results = hosts.run("apt update", hide=True)')
    print("   # 多线程并行，速度快")
    
    print("\n3. 处理结果：")
    print("   for conn, result in results.items():")
    print("       print(f'{conn.host}: {result.stdout}')")
    
    print("\n4. 错误处理：")
    print("   try:")
    print('       results = hosts.run("cmd")')
    print("   except GroupException as e:")
    print("       for conn, result in e.result.items():")
    print("           # 处理失败的主机")
    
    print("\n5. 从列表创建：")
    print('   host_list = ["user@h1", "user@h2", "user@h3"]')
    print("   group = ThreadingGroup(*host_list)")
    
    # 模拟多主机执行结果
    print("\n--- 模拟执行结果 ---")
    mock_hosts = ["web-01", "web-02", "db-01"]
    for host in mock_hosts:
        print(f"  {host}: Linux {host} 5.4.0-generic")
# endregion
