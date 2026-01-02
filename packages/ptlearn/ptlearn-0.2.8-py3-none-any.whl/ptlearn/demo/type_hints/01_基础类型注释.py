"""
Python 类型注释基础
===================
类型注释(Type Hints)是Python 3.5+引入的特性，用于标注变量和函数的类型
它不会影响运行时行为，但能提升代码可读性和IDE支持
"""

# region 示例1: 变量类型注释
if True:  # 改为 False 可跳过此示例
    # 基本类型注释
    name: str = "Alice"
    age: int = 25
    height: float = 1.75
    is_student: bool = True
    
    # 也可以只声明类型，不赋值
    score: int  # 此时变量未定义，访问会报错
    
    print(f"姓名: {name}, 年龄: {age}, 身高: {height}, 是否学生: {is_student}")
# endregion

# region 示例2: 函数参数和返回值注释
if True:  # 改为 False 可跳过此示例
    def greet(name: str) -> str:
        """带类型注释的函数"""
        return f"Hello, {name}!"
    
    def add(a: int, b: int) -> int:
        """两数相加"""
        return a + b
    
    def no_return(msg: str) -> None:
        """无返回值的函数使用 None"""
        print(msg)
    
    print(greet("World"))
    print(f"1 + 2 = {add(1, 2)}")
    no_return("这个函数没有返回值")
# endregion

# region 示例3: 容器类型注释 (Python 3.9+ 原生支持)
if True:  # 改为 False 可跳过此示例
    # Python 3.9+ 可以直接使用内置类型
    names: list[str] = ["Alice", "Bob", "Charlie"]
    scores: dict[str, int] = {"Alice": 95, "Bob": 87}
    coordinates: tuple[float, float] = (3.14, 2.71)
    unique_ids: set[int] = {1, 2, 3}
    
    print(f"名字列表: {names}")
    print(f"成绩字典: {scores}")
    print(f"坐标元组: {coordinates}")
    print(f"ID集合: {unique_ids}")
# endregion

# region 示例4: 使用 typing 模块 (兼容旧版本)
if True:  # 改为 False 可跳过此示例
    from typing import List, Dict, Tuple, Set
    
    # Python 3.8 及更早版本需要从 typing 导入
    names_old: List[str] = ["Alice", "Bob"]
    scores_old: Dict[str, int] = {"Alice": 95}
    coords_old: Tuple[int, int] = (10, 20)
    ids_old: Set[int] = {1, 2, 3}
    
    print(f"(旧语法) 名字: {names_old}")
    print(f"(旧语法) 成绩: {scores_old}")
# endregion

# region 示例5: 类型注释不影响运行时
if True:  # 改为 False 可跳过此示例
    # 类型注释只是"提示"，Python 不会强制检查
    wrong_type: int = "这其实是字符串"  # 运行时不会报错！
    print(f"类型注释写的是int，实际值: {wrong_type}, 实际类型: {type(wrong_type)}")
    
    # 要进行类型检查，需要使用 mypy 等工具
    # 安装: pip install mypy
    # 使用: mypy your_file.py
# endregion
