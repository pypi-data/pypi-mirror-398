"""
Python 类型注释 - 类与协议
==========================
类的类型注释、Protocol（结构化子类型）、抽象基类
"""
from typing import Protocol, runtime_checkable, ClassVar
from abc import ABC, abstractmethod

# region 示例1: 类属性的类型注释
if True:  # 改为 False 可跳过此示例
    class Person:
        # 类变量（所有实例共享）
        species: ClassVar[str] = "Homo sapiens"
        count: ClassVar[int] = 0
        
        # 实例变量在 __init__ 中注释
        def __init__(self, name: str, age: int) -> None:
            self.name: str = name
            self.age: int = age
            Person.count += 1
    
    p1 = Person("Alice", 25)
    p2 = Person("Bob", 30)
    
    print(f"物种: {Person.species}")
    print(f"人数: {Person.count}")
    print(f"姓名: {p1.name}, 年龄: {p1.age}")
# endregion

# region 示例2: 方法的类型注释
if True:  # 改为 False 可跳过此示例
    class Calculator:
        def __init__(self, value: float = 0) -> None:
            self.value = value
        
        def add(self, x: float) -> 'Calculator':
            """返回 self 实现链式调用"""
            self.value += x
            return self
        
        def multiply(self, x: float) -> 'Calculator':
            self.value *= x
            return self
        
        @staticmethod
        def pi() -> float:
            """静态方法"""
            return 3.14159
        
        @classmethod
        def from_string(cls, s: str) -> 'Calculator':
            """类方法"""
            return cls(float(s))
    
    calc = Calculator(10).add(5).multiply(2)
    print(f"计算结果: {calc.value}")
    print(f"PI: {Calculator.pi()}")
    print(f"从字符串创建: {Calculator.from_string('100').value}")
# endregion

# region 示例3: Protocol - 结构化子类型（鸭子类型）
if True:  # 改为 False 可跳过此示例
    class Drawable(Protocol):
        """定义一个协议：任何有 draw 方法的对象"""
        def draw(self) -> str: ...
    
    # 不需要显式继承，只要有 draw 方法就符合协议
    class Circle:
        def draw(self) -> str:
            return "○"
    
    class Square:
        def draw(self) -> str:
            return "□"
    
    def render(shape: Drawable) -> None:
        """接受任何符合 Drawable 协议的对象"""
        print(f"绘制: {shape.draw()}")
    
    render(Circle())  # Circle 符合 Drawable 协议
    render(Square())  # Square 也符合
# endregion

# region 示例4: runtime_checkable Protocol
if True:  # 改为 False 可跳过此示例
    @runtime_checkable
    class Closeable(Protocol):
        """可关闭的资源协议"""
        def close(self) -> None: ...
    
    class FileWrapper:
        def close(self) -> None:
            print("文件已关闭")
    
    class Connection:
        def close(self) -> None:
            print("连接已关闭")
    
    # runtime_checkable 允许使用 isinstance 检查
    fw = FileWrapper()
    conn = Connection()
    
    print(f"FileWrapper 是 Closeable: {isinstance(fw, Closeable)}")
    print(f"Connection 是 Closeable: {isinstance(conn, Closeable)}")
    print(f"字符串 是 Closeable: {isinstance('hello', Closeable)}")
# endregion

# region 示例5: 抽象基类 vs Protocol
if True:  # 改为 False 可跳过此示例
    # 抽象基类：需要显式继承
    class Animal(ABC):
        @abstractmethod
        def speak(self) -> str:
            pass
    
    class Dog(Animal):  # 必须继承 Animal
        def speak(self) -> str:
            return "汪汪!"
    
    # Protocol：不需要继承，只看结构
    class Speaker(Protocol):
        def speak(self) -> str: ...
    
    class Robot:  # 不继承任何类
        def speak(self) -> str:
            return "嘟嘟!"
    
    def make_sound(speaker: Speaker) -> None:
        print(speaker.speak())
    
    make_sound(Dog())    # Dog 继承了 Animal
    make_sound(Robot())  # Robot 只是恰好有 speak 方法
    
    print("\n抽象基类: 强制继承关系，运行时检查")
    print("Protocol: 结构化类型，只看方法签名")
# endregion

# region 示例6: 带属性的 Protocol
if True:  # 改为 False 可跳过此示例
    class Named(Protocol):
        """带有 name 属性的协议"""
        @property
        def name(self) -> str: ...
    
    class User:
        def __init__(self, name: str) -> None:
            self._name = name
        
        @property
        def name(self) -> str:
            return self._name
    
    class Product:
        def __init__(self, name: str) -> None:
            self.name = name  # 普通属性也可以
    
    def greet(obj: Named) -> str:
        return f"Hello, {obj.name}!"
    
    print(greet(User("Alice")))
    print(greet(Product("iPhone")))
# endregion
