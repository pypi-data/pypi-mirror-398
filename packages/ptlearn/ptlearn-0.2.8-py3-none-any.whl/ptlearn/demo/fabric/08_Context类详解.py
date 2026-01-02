"""
Fabric Context 类详解

Context 是 Fabric/Invoke 的核心类，它：
1. 封装了命令执行环境
2. 管理配置信息
3. 提供 run()、sudo() 等命令执行方法
4. 支持 cd()、prefix() 等上下文管理器

本文件演示 Context 类的各种用法
"""

from invoke import Context, Config, MockContext
from invoke.runners import Result

# region 示例1: Context 基础用法
if False:
    print("=" * 50)
    print("示例1: Context 基础用法")
    print("=" * 50)
    
    # 创建默认 Context
    ctx = Context()
    
    # run() 执行本地命令
    # 返回 Result 对象，包含 stdout、stderr、return_code 等
    result = ctx.run("echo Hello from Context", hide=True)
    print(f"命令输出: {result.stdout.strip()}")
    print(f"返回码: {result.return_code}")
    print(f"命令: {result.command}")
    print()
# endregion

# region 示例2: 使用 Config 自定义 Context
if True:
    print("=" * 50)
    print("示例2: 使用 Config 自定义 Context")
    print("=" * 50)
    
    # 创建自定义配置
    config = Config(overrides={
        "run": {
            "echo": True,      # 执行前打印命令
            "warn": True,      # 命令失败时警告而非抛异常
        }
    })
    
    ctx = Context(config=config)
    
    # 通过 ctx.config 访问配置
    print(f"echo 配置: {ctx.config.run.echo}")
    print(f"warn 配置: {ctx.config.run.warn}")
    
    # Context 支持字典式访问配置（代理到 config）
    print(f"通过代理访问: {ctx['run']['echo']}")
    print()
# endregion

# region 示例3: cd() 上下文管理器
if True:
    print("=" * 50)
    print("示例3: cd() 上下文管理器")
    print("=" * 50)
    
    ctx = Context()
    
    # cd() 改变后续命令的工作目录
    # 注意：这不会真正改变 Python 进程的 cwd
    # 而是在命令前添加 "cd xxx &&"
    
    print(f"初始 cwd: '{ctx.cwd}'")  # 空字符串
    
    with ctx.cd("src"):
        print(f"进入 src 后 cwd: '{ctx.cwd}'")
        
        # cd() 可以嵌套
        with ctx.cd("ptlearn"):
            print(f"嵌套进入 ptlearn 后 cwd: '{ctx.cwd}'")
        
        print(f"退出内层后 cwd: '{ctx.cwd}'")
    
    print(f"完全退出后 cwd: '{ctx.cwd}'")
    print()
# endregion

# region 示例4: prefix() 命令前缀
if True:
    print("=" * 50)
    print("示例4: prefix() 命令前缀")
    print("=" * 50)
    
    ctx = Context()
    
    # prefix() 在每个命令前添加前缀命令
    # 常用于激活虚拟环境等场景
    
    print("prefix() 会在命令前添加 '前缀 &&'")
    print()
    
    # 模拟虚拟环境激活场景
    with ctx.prefix("echo [激活虚拟环境]"):
        # 实际执行: echo [激活虚拟环境] && echo 运行测试
        result = ctx.run("echo 运行测试", hide=True)
        print(f"组合命令输出:\n{result.stdout}")
    
    # prefix() 也可以嵌套
    with ctx.prefix("echo [步骤1]"):
        with ctx.prefix("echo [步骤2]"):
            result = ctx.run("echo [步骤3]", hide=True)
            print(f"嵌套 prefix 输出:\n{result.stdout}")
    print()
# endregion

# region 示例5: cd() 和 prefix() 组合使用
if False:
    print("=" * 50)
    print("示例5: cd() 和 prefix() 组合使用")
    print("=" * 50)
    
    ctx = Context()
    
    # cd() 和 prefix() 可以组合
    # 执行顺序: cd xxx && prefix1 && prefix2 && 实际命令
    
    # 使用当前目录的 src 文件夹（确保存在）
    with ctx.cd("src"):
        with ctx.prefix("echo [环境准备]"):
            # 查看内部状态
            print(f"当前目录: {ctx.cwd}")
            print(f"命令前缀列表: {ctx.command_prefixes}")
            
            # 实际命令会被组装成:
            # cd src && echo [环境准备] && echo 执行任务
            result = ctx.run("echo 执行任务", hide=True)
            print(f"输出:\n{result.stdout}")
    
    # 演示命令组装原理（不实际执行）
    print("命令组装示例:")
    print("  cd project && source venv/bin/activate && pip install && python app.py")
    print()
# endregion

# region 示例6: run() 的常用参数
if False:
    print("=" * 50)
    print("示例6: run() 的常用参数")
    print("=" * 50)
    
    ctx = Context()
    
    # hide: 隐藏输出 (True, False, "stdout", "stderr", "both")
    result = ctx.run("echo 隐藏输出测试", hide=True)
    print(f"hide=True 时仍可通过 result.stdout 获取: {result.stdout.strip()}")
    
    # warn: 命令失败时不抛异常，只警告
    result = ctx.run("exit 1", warn=True, hide=True)
    print(f"warn=True 时失败命令返回码: {result.return_code}")
    print(f"命令是否失败: {result.failed}")
    print(f"命令是否成功: {result.ok}")
    
    # echo: 执行前打印命令
    print("\necho=True 效果:")
    ctx.run("echo 这条命令会先被打印", echo=True, hide="stdout")
    
    # pty: 使用伪终端（某些命令需要）
    # encoding: 指定输出编码
    print()
# endregion

# region 示例7: MockContext 用于测试
if False:
    print("=" * 50)
    print("示例7: MockContext 用于测试")
    print("=" * 50)
    
    # MockContext 允许预设命令的返回值
    # 非常适合单元测试
    
    # 方式1: 使用字典预设多个命令的结果
    mock_ctx = MockContext(run={
        "ls": Result("file1.txt\nfile2.txt"),
        "pwd": Result("/home/user"),
        "whoami": Result("testuser"),
    })
    
    print("预设的命令结果:")
    print(f"  ls: {mock_ctx.run('ls').stdout.strip()}")
    print(f"  pwd: {mock_ctx.run('pwd').stdout.strip()}")
    print(f"  whoami: {mock_ctx.run('whoami').stdout.strip()}")
    
    # 方式2: 使用布尔值表示成功/失败
    mock_ctx2 = MockContext(run={
        "success_cmd": True,   # 等价于 Result(exited=0)
        "fail_cmd": False,     # 等价于 Result(exited=1)
    })
    
    print(f"\n布尔值预设:")
    print(f"  success_cmd 返回码: {mock_ctx2.run('success_cmd').return_code}")
    print(f"  fail_cmd 返回码: {mock_ctx2.run('fail_cmd').return_code}")
    
    # 方式3: 使用列表预设多次调用的结果
    mock_ctx3 = MockContext(run={
        "counter": [
            Result("第1次调用"),
            Result("第2次调用"),
            Result("第3次调用"),
        ]
    })
    
    print(f"\n列表预设（多次调用）:")
    print(f"  第1次: {mock_ctx3.run('counter').stdout.strip()}")
    print(f"  第2次: {mock_ctx3.run('counter').stdout.strip()}")
    print(f"  第3次: {mock_ctx3.run('counter').stdout.strip()}")
    print()
# endregion

# region 示例8: MockContext 正则匹配
if False:
    print("=" * 50)
    print("示例8: MockContext 正则匹配")
    print("=" * 50)
    
    import re
    
    # MockContext 支持正则表达式作为键
    mock_ctx = MockContext(run={
        re.compile(r"echo .*"): Result("匹配到 echo 命令"),
        re.compile(r"ls -.*"): Result("匹配到 ls 带参数"),
        "ls": Result("精确匹配 ls"),
    })
    
    print("正则匹配测试:")
    print(f"  echo hello: {mock_ctx.run('echo hello').stdout.strip()}")
    print(f"  echo world: {mock_ctx.run('echo world').stdout.strip()}")
    print(f"  ls -la: {mock_ctx.run('ls -la').stdout.strip()}")
    print(f"  ls: {mock_ctx.run('ls').stdout.strip()}")
    print()
# endregion

# region 示例9: set_result_for 动态修改 Mock 结果
if False:
    print("=" * 50)
    print("示例9: set_result_for 动态修改 Mock 结果")
    print("=" * 50)
    
    # 创建空的 MockContext
    mock_ctx = MockContext(run={})
    
    # 动态添加命令结果
    mock_ctx.set_result_for("run", "dynamic_cmd", Result("动态添加的结果"))
    
    print(f"动态添加后: {mock_ctx.run('dynamic_cmd').stdout.strip()}")
    
    # 修改已有命令的结果
    mock_ctx.set_result_for("run", "dynamic_cmd", Result("修改后的结果"))
    print(f"修改后: {mock_ctx.run('dynamic_cmd').stdout.strip()}")
    print()
# endregion

# region 示例10: 实战 - 封装部署任务
if False:
    print("=" * 50)
    print("示例10: 实战 - 封装部署任务")
    print("=" * 50)
    
    def deploy(ctx, project_dir, venv_path=".venv"):
        """
        模拟部署流程，展示 Context 的实际应用
        """
        print(f"开始部署项目: {project_dir}")
        
        with ctx.cd(project_dir):
            # 激活虚拟环境（Windows 和 Unix 不同）
            activate_cmd = f"source {venv_path}/bin/activate"
            
            with ctx.prefix(activate_cmd):
                # 安装依赖
                ctx.run("pip install -r requirements.txt")
                print("  ✓ 依赖安装完成")
                
                # 运行迁移
                ctx.run("python manage.py migrate")
                print("  ✓ 数据库迁移完成")
                
                # 收集静态文件
                ctx.run("python manage.py collectstatic --noinput")
                print("  ✓ 静态文件收集完成")
                
                # 重启服务
                ctx.run("systemctl restart myapp")
                print("  ✓ 服务重启完成")
        
        print("部署完成!\n")
    
    # 使用 MockContext 测试部署函数
    # 这样可以在不实际执行命令的情况下验证逻辑
    print("使用 MockContext 模拟部署流程:")
    mock_ctx = MockContext(run={
        re.compile(r".*"): True  # 所有命令都返回成功
    })
    deploy(mock_ctx, "/var/www/myapp")
    
    # 验证 mock_ctx.run 被调用了
    print(f"run() 被调用次数: {mock_ctx.run.call_count}")
    print("调用的命令:")
    for call in mock_ctx.run.call_args_list:
        print(f"  - {call[0][0]}")
# endregion

print("\n" + "=" * 50)
print("Context 类学习完成!")
print("=" * 50)
