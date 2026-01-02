"""
Invoke 配置管理
===============
学习 invoke 的配置系统：配置层级、配置文件、运行时配置等。

适用版本: Python 3.6+
"""

from invoke import task, Context, Config

# region 示例1: 配置层级概述
if True:  # 改为 False 可跳过此示例
    """
    invoke 的配置按优先级从低到高：
    1. 硬编码默认值
    2. 集合级配置（Collection.configure()）
    3. 系统级配置文件（/etc/invoke.yaml）
    4. 用户级配置文件（~/.invoke.yaml）
    5. 项目级配置文件（./invoke.yaml）
    6. 环境变量（INVOKE_*）
    7. 命令行参数
    8. 运行时修改
    """
    
    print("=== 配置优先级（从低到高）===")
    priorities = [
        "1. 硬编码默认值",
        "2. 集合级配置",
        "3. 系统级配置文件 (/etc/invoke.yaml)",
        "4. 用户级配置文件 (~/.invoke.yaml)",
        "5. 项目级配置文件 (./invoke.yaml)",
        "6. 环境变量 (INVOKE_*)",
        "7. 命令行参数",
        "8. 运行时修改",
    ]
    for p in priorities:
        print(f"  {p}")
# endregion

# region 示例2: 使用 Config 对象
if True:  # 改为 False 可跳过此示例
    """
    Config 对象管理所有配置项
    """
    
    # 创建带有自定义配置的 Config
    config = Config(overrides={
        'run': {
            'echo': True,  # 默认打印执行的命令
            'hide': False,  # 默认显示输出
        },
        'my_app': {
            'debug': True,
            'log_level': 'INFO',
        }
    })
    
    # 使用配置创建 Context
    ctx = Context(config=config)
    
    print("=== 访问配置 ===")
    print(f"run.echo: {ctx.config.run.echo}")
    print(f"my_app.debug: {ctx.config.my_app.debug}")
    print(f"my_app.log_level: {ctx.config.my_app.log_level}")
# endregion

# region 示例3: 在任务中使用配置
if True:  # 改为 False 可跳过此示例
    """
    任务可以通过 Context 访问配置
    """
    
    @task
    def show_config(c):
        """显示当前配置"""
        print(f"Echo 模式: {c.config.run.echo}")
        
        # 安全地访问可能不存在的配置
        debug = c.config.get('my_app', {}).get('debug', False)
        print(f"调试模式: {debug}")
    
    # 创建带配置的 Context
    config = Config(overrides={
        'run': {'echo': False},
        'my_app': {'debug': True}
    })
    ctx = Context(config=config)
    
    print("=== 任务中访问配置 ===")
    show_config(ctx)
# endregion

# region 示例4: 配置文件格式
if True:  # 改为 False 可跳过此示例
    """
    invoke 支持多种配置文件格式：
    - invoke.yaml / invoke.yml
    - invoke.json
    - invoke.py
    """
    
    yaml_example = """
# invoke.yaml 示例
run:
  echo: true
  pty: false

my_app:
  database:
    host: localhost
    port: 5432
  cache:
    enabled: true
    ttl: 3600
"""
    
    json_example = """{
  "run": {
    "echo": true,
    "pty": false
  },
  "my_app": {
    "database": {
      "host": "localhost",
      "port": 5432
    }
  }
}"""
    
    py_example = """
# invoke.py 示例
run = {
    'echo': True,
    'pty': False,
}

my_app = {
    'database': {
        'host': 'localhost',
        'port': 5432,
    }
}
"""
    
    print("=== YAML 格式 (invoke.yaml) ===")
    print(yaml_example)
    
    print("=== JSON 格式 (invoke.json) ===")
    print(json_example)
    
    print("=== Python 格式 (invoke.py) ===")
    print(py_example)
# endregion

# region 示例5: 环境变量配置
if True:  # 改为 False 可跳过此示例
    """
    使用环境变量覆盖配置
    格式: INVOKE_<SECTION>_<KEY>=value
    """
    import os
    
    print("=== 环境变量配置示例 ===")
    env_examples = [
        ("INVOKE_RUN_ECHO", "true", "设置 run.echo = True"),
        ("INVOKE_RUN_HIDE", "both", "设置 run.hide = 'both'"),
        ("INVOKE_MY_APP_DEBUG", "1", "设置 my_app.debug = True"),
    ]
    
    for var, value, desc in env_examples:
        print(f"  {var}={value}")
        print(f"    -> {desc}")
    
    # 演示环境变量的效果
    print("\n=== 实际演示 ===")
    os.environ['INVOKE_RUN_ECHO'] = 'false'
    
    config = Config()
    config.load_shell_env()
    
    print(f"从环境变量读取 run.echo: {config.run.echo}")
    
    # 清理
    del os.environ['INVOKE_RUN_ECHO']
# endregion

# region 示例6: 运行时修改配置
if True:  # 改为 False 可跳过此示例
    """
    可以在运行时动态修改配置
    """
    
    @task
    def dynamic_config(c, verbose=False):
        """根据参数动态调整配置"""
        
        # 根据 verbose 参数调整 run 配置
        if verbose:
            # 修改配置
            c.config.run.echo = True
            print("已启用详细模式")
        else:
            c.config.run.echo = False
            print("静默模式")
        
        # 执行命令
        c.run("python --version")
    
    ctx = Context()
    print("=== verbose=False ===")
    dynamic_config(ctx, verbose=False)
    
    print("\n=== verbose=True ===")
    dynamic_config(ctx, verbose=True)
# endregion
