"""
Rich 语法高亮与日志
===================
本文件涵盖：
- Syntax 代码语法高亮
- Markdown 渲染
- 日志处理器 RichHandler
- 异常美化输出
"""

from rich.console import Console
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.traceback import install as install_traceback
import logging

console = Console()

# region 示例1: 代码语法高亮
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例1: 代码语法高亮")
    print("=" * 50)
    
    python_code = '''
def fibonacci(n):
    """计算斐波那契数列"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 打印前10个斐波那契数
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
'''
    
    # 创建语法高亮对象
    syntax = Syntax(python_code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)
    print()
# endregion

# region 示例2: 不同语言和主题
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例2: 不同语言和主题")
    print("=" * 50)
    
    # JavaScript 代码
    js_code = '''
const greet = (name) => {
    return `Hello, ${name}!`;
};

console.log(greet("World"));
'''
    
    console.print("[bold cyan]JavaScript (dracula 主题):[/bold cyan]")
    syntax_js = Syntax(js_code, "javascript", theme="dracula", line_numbers=True)
    console.print(syntax_js)
    
    # JSON 数据
    json_code = '''
{
    "name": "Rich",
    "version": "13.0.0",
    "features": ["colors", "tables", "progress"]
}
'''
    
    print()
    console.print("[bold cyan]JSON (github-dark 主题):[/bold cyan]")
    syntax_json = Syntax(json_code, "json", theme="github-dark")
    console.print(syntax_json)
    print()
# endregion

# region 示例3: Markdown 渲染
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例3: Markdown 渲染")
    print("=" * 50)
    
    markdown_text = """
# Rich Markdown 演示

这是一段 **粗体** 和 *斜体* 文本。

## 列表示例

- 项目一
- 项目二
  - 子项目
- 项目三

## 代码示例

行内代码: `print("Hello")`

```python
def hello():
    print("Hello, Rich!")
```

> 这是一段引用文字

---

更多信息请访问 [Rich 文档](https://rich.readthedocs.io)
"""
    
    md = Markdown(markdown_text)
    console.print(md)
    print()
# endregion

# region 示例4: Rich 日志处理器
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例4: Rich 日志处理器")
    print("=" * 50)
    
    from rich.logging import RichHandler
    
    # 配置日志使用 RichHandler
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    
    log = logging.getLogger("rich_demo")
    
    log.debug("这是调试信息")
    log.info("这是普通信息")
    log.warning("这是警告信息")
    log.error("这是错误信息")
    log.critical("这是严重错误")
    print()
# endregion

# region 示例5: 美化异常输出
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例5: 美化异常输出")
    print("=" * 50)
    
    # 安装 Rich 异常处理器（全局生效）
    # install_traceback()  # 取消注释可全局启用
    
    # 手动打印异常
    def divide(a, b):
        return a / b
    
    def calculate():
        return divide(10, 0)
    
    try:
        calculate()
    except Exception:
        console.print_exception(show_locals=True)
    
    print()
# endregion

# region 示例6: 从文件读取并高亮
if True:  # 改为 False 可跳过此示例
    print("=" * 50)
    print("示例6: 高亮指定行")
    print("=" * 50)
    
    code = '''
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

data = [1, -2, 3, -4, 5]
output = process_data(data)
print(output)
'''
    
    # 高亮特定行（第4-6行）
    syntax = Syntax(
        code, 
        "python", 
        theme="monokai",
        line_numbers=True,
        highlight_lines={4, 5, 6},  # 高亮这些行
    )
    console.print(syntax)
    print()
# endregion
