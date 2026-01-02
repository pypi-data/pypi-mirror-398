"""
Invoke YAML 配置文件
====================
演示如何使用 invoke.yaml 配置文件来管理 Invoke 的各种设置
配置文件支持 invoke.yaml、invoke.yml、.invoke.yaml、.invoke.yml 等命名
"""

# region 示例1: 基础配置文件结构
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 基础配置文件结构")
    print("=" * 50)
    
    # invoke.yaml 基础结构示例
    basic_config = """
# invoke.yaml - Invoke 配置文件
# 放置在项目根目录下

# 任务相关配置
tasks:
  # 自动加载的任务模块搜索路径
  search_root: .
  # 默认任务集合模块名（默认为 tasks）
  collection_name: tasks

# 命令执行配置
run:
  # 是否回显执行的命令（默认 False）
  echo: true
  # 是否在命令失败时抛出异常（默认 True）
  warn: false
  # 是否隐藏命令输出
  hide: false
  # 使用的 shell（默认系统 shell）
  shell: /bin/bash
  # 命令执行的环境变量
  env:
    PYTHONPATH: ./src
    DEBUG: "1"
"""
    print(basic_config)
# endregion

# region 示例2: 完整配置文件示例
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例2: 完整配置文件示例")
    print("=" * 50)
    
    full_config = """
# invoke.yaml - 完整配置示例

# ============================================
# 任务配置
# ============================================
tasks:
  search_root: .
  collection_name: tasks
  # 是否自动将下划线转为短横线（task_name -> task-name）
  auto_dash_names: true
  # 是否忽略未知的子命令
  ignore_unknown_help: false

# ============================================
# 命令执行配置 (run)
# ============================================
run:
  # 回显命令到标准输出
  echo: true
  # 命令失败时只警告不抛异常
  warn: false
  # 隐藏输出: false / true / 'stdout' / 'stderr' / 'both'
  hide: false
  # 使用伪终端（PTY）
  pty: false
  # 命令超时（秒）
  timeout: null
  # 工作目录
  # cwd: /path/to/dir
  # 使用的 shell
  shell: /bin/bash
  # 环境变量
  env:
    PYTHONPATH: ./src
    LANG: en_US.UTF-8

# ============================================
# sudo 配置
# ============================================
sudo:
  # sudo 密码（不建议明文存储）
  # password: your_password
  # 使用的 sudo 程序
  # program: sudo
  # 是否使用 PTY
  pty: true

# ============================================
# 超时配置
# ============================================
timeouts:
  # 命令执行超时
  command: 300

# ============================================
# 自定义配置（供任务使用）
# ============================================
my_app:
  # 项目名称
  name: my-project
  # 版本号
  version: 1.0.0
  # 调试模式
  debug: true
  # 部署配置
  deploy:
    host: production.example.com
    user: deploy
    path: /var/www/app
  # 数据库配置
  database:
    host: localhost
    port: 5432
    name: mydb
"""
    print(full_config)
# endregion

# region 示例3: 多环境配置
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例3: 多环境配置")
    print("=" * 50)
    
    # 可以创建多个配置文件用于不同环境
    env_configs = """
# 方式1: 使用不同的配置文件
# invoke.yaml       - 默认/开发环境
# invoke.prod.yaml  - 生产环境
# invoke.test.yaml  - 测试环境

# 运行时指定配置文件:
# inv --config invoke.prod.yaml deploy

# ============================================
# invoke.yaml (开发环境)
# ============================================
run:
  echo: true
  
my_app:
  debug: true
  database:
    host: localhost
    name: dev_db

# ============================================
# invoke.prod.yaml (生产环境)
# ============================================
run:
  echo: false
  warn: false
  
my_app:
  debug: false
  database:
    host: db.production.com
    name: prod_db
  deploy:
    host: prod-server.com
    user: deploy
"""
    print(env_configs)
# endregion

# region 示例4: 在任务中读取配置
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例4: 在任务中读取配置")
    print("=" * 50)
    
    code_example = '''
from invoke import task

@task
def deploy(c):
    """使用配置文件中的部署设置"""
    # 读取自定义配置
    app_name = c.config.my_app.name
    host = c.config.my_app.deploy.host
    user = c.config.my_app.deploy.user
    path = c.config.my_app.deploy.path
    
    print(f"部署 {app_name} 到 {user}@{host}:{path}")
    
    # 读取 run 配置
    echo_enabled = c.config.run.echo
    print(f"命令回显: {echo_enabled}")

@task
def db_info(c):
    """显示数据库配置"""
    db = c.config.my_app.database
    print(f"数据库: {db.host}:{db.port}/{db.name}")

@task
def show_env(c):
    """显示环境变量配置"""
    env = c.config.run.get('env', {})
    for key, value in env.items():
        print(f"  {key}={value}")
'''
    print(code_example)
    
    # 实际演示配置读取
    from invoke import Config
    
    # 模拟配置
    overrides = {
        'my_app': {
            'name': 'demo-project',
            'debug': True,
            'deploy': {
                'host': 'example.com',
                'user': 'admin',
                'path': '/var/www'
            }
        }
    }
    
    config = Config(overrides=overrides)
    print("\n实际读取配置演示:")
    print(f"  项目名: {config.my_app.name}")
    print(f"  调试模式: {config.my_app.debug}")
    print(f"  部署主机: {config.my_app.deploy.host}")
# endregion


# region 示例5: 配置文件加载顺序
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例5: 配置文件加载顺序与优先级")
    print("=" * 50)
    
    load_order = """
Invoke 配置加载顺序（后加载的覆盖先加载的）:

1. 系统级配置
   - /etc/invoke.yaml
   
2. 用户级配置
   - ~/.invoke.yaml
   - ~/.invoke.yml
   
3. 项目级配置（当前目录）
   - invoke.yaml
   - invoke.yml
   - .invoke.yaml
   - .invoke.yml
   - tasks.yaml (与 tasks.py 同名)
   
4. 命令行指定
   - inv --config custom.yaml ...
   
5. 环境变量
   - INVOKE_RUN_ECHO=1
   - INVOKE_MY_APP_DEBUG=true
   
6. 代码中的 Config 覆盖

优先级: 代码 > 环境变量 > 命令行 > 项目 > 用户 > 系统
"""
    print(load_order)
# endregion

# region 示例6: 环境变量覆盖配置
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例6: 使用环境变量覆盖配置")
    print("=" * 50)
    
    env_override = """
# 环境变量命名规则:
# INVOKE_{SECTION}_{KEY} = value
# 嵌套配置用下划线连接

# 示例:
export INVOKE_RUN_ECHO=1           # run.echo = True
export INVOKE_RUN_WARN=0           # run.warn = False
export INVOKE_MY_APP_DEBUG=true    # my_app.debug = True
export INVOKE_MY_APP_NAME=prod-app # my_app.name = "prod-app"

# 在 CI/CD 中很有用:
# GitHub Actions 示例
# env:
#   INVOKE_RUN_ECHO: "0"
#   INVOKE_MY_APP_DEBUG: "false"
"""
    print(env_override)
    
    # 演示环境变量读取
    import os
    
    # 设置测试环境变量
    os.environ['INVOKE_RUN_ECHO'] = '1'
    os.environ['INVOKE_MY_APP_DEBUG'] = 'true'
    
    from invoke import Config
    config = Config()
    
    print("\n从环境变量加载的配置:")
    print(f"  run.echo = {config.run.echo}")
    
    # 清理
    del os.environ['INVOKE_RUN_ECHO']
    del os.environ['INVOKE_MY_APP_DEBUG']
# endregion

# region 示例7: 实用配置模板
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例7: 实用配置模板")
    print("=" * 50)
    
    practical_template = """
# invoke.yaml - 实用项目配置模板

# 任务配置
tasks:
  search_root: .
  collection_name: tasks
  auto_dash_names: true

# 命令执行
run:
  echo: true
  pty: false
  env:
    PYTHONPATH: ./src
    PYTHONDONTWRITEBYTECODE: "1"

# 项目信息
project:
  name: my-project
  version: 1.0.0
  python: "3.11"

# 路径配置
paths:
  src: src
  tests: tests
  docs: docs
  dist: dist

# 构建配置
build:
  clean_dirs:
    - dist
    - build
    - "*.egg-info"
    - __pycache__
    - .pytest_cache
    - .mypy_cache

# 测试配置
test:
  runner: pytest
  coverage: true
  markers:
    - unit
    - integration
    - slow

# 代码质量
quality:
  formatters:
    - black
    - isort
  linters:
    - flake8
    - mypy
  line_length: 88

# 部署配置
deploy:
  staging:
    host: staging.example.com
    user: deploy
    path: /var/www/staging
  production:
    host: prod.example.com
    user: deploy
    path: /var/www/prod

# Docker 配置
docker:
  image_name: my-project
  registry: docker.io/myorg
  build_args:
    PYTHON_VERSION: "3.11"
"""
    print(practical_template)
# endregion

# region 示例8: 配置验证与默认值
if True:  # 改为 False 可跳过此示例
    print("\n" + "=" * 50)
    print("示例8: 配置验证与默认值处理")
    print("=" * 50)
    
    code_example = '''
from invoke import task

@task
def safe_deploy(c):
    """安全地读取配置，处理缺失值"""
    
    # 方式1: 使用 get() 方法
    debug = c.config.get('my_app', {}).get('debug', False)
    
    # 方式2: 使用 try-except
    try:
        host = c.config.deploy.production.host
    except AttributeError:
        host = 'localhost'
    
    # 方式3: 使用 getattr
    timeout = getattr(c.config.run, 'timeout', 30)
    
    print(f"Debug: {debug}, Host: {host}, Timeout: {timeout}")

@task
def validate_config(c):
    """验证必需的配置项"""
    required = ['my_app.name', 'deploy.production.host']
    
    for path in required:
        parts = path.split('.')
        value = c.config
        try:
            for part in parts:
                value = getattr(value, part)
            print(f"✓ {path} = {value}")
        except AttributeError:
            print(f"✗ {path} 未配置!")
'''
    print(code_example)
    
    # 实际演示
    from invoke import Config
    
    config = Config(overrides={
        'my_app': {'name': 'test', 'debug': True}
    })
    
    print("\n配置读取演示:")
    # 安全读取
    name = config.get('my_app', {}).get('name', 'default')
    missing = config.get('not_exist', {}).get('key', '默认值')
    print(f"  my_app.name = {name}")
    print(f"  not_exist.key = {missing}")
# endregion
