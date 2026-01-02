"""
Python 类型注释实战应用
======================
综合示例：数据类、装饰器、上下文管理器的类型注释
"""
from typing import TypeVar, Callable, ParamSpec, Generator, Iterator
from dataclasses import dataclass
from contextlib import contextmanager
from functools import wraps

# region 示例1: dataclass 与类型注释
if True:  # 改为 False 可跳过此示例
    @dataclass
    class Point:
        x: float
        y: float
        
        def distance_to(self, other: 'Point') -> float:
            return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    @dataclass
    class Rectangle:
        top_left: Point
        bottom_right: Point
        
        @property
        def width(self) -> float:
            return abs(self.bottom_right.x - self.top_left.x)
        
        @property
        def height(self) -> float:
            return abs(self.bottom_right.y - self.top_left.y)
        
        @property
        def area(self) -> float:
            return self.width * self.height
    
    p1 = Point(0, 0)
    p2 = Point(3, 4)
    print(f"两点距离: {p1.distance_to(p2)}")
    
    rect = Rectangle(Point(0, 0), Point(10, 5))
    print(f"矩形面积: {rect.area}")
# endregion

# region 示例2: 装饰器的类型注释 (ParamSpec)
if True:  # 改为 False 可跳过此示例
    P = ParamSpec('P')  # 捕获参数签名
    R = TypeVar('R')    # 返回类型
    
    def log_calls(func: Callable[P, R]) -> Callable[P, R]:
        """记录函数调用的装饰器，保持类型签名"""
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            print(f"调用: {func.__name__}")
            result = func(*args, **kwargs)
            print(f"返回: {result}")
            return result
        return wrapper
    
    @log_calls
    def add(a: int, b: int) -> int:
        return a + b
    
    @log_calls
    def greet(name: str) -> str:
        return f"Hello, {name}!"
    
    add(1, 2)
    print()
    greet("World")
# endregion

# region 示例3: 生成器的类型注释
if True:  # 改为 False 可跳过此示例
    # Generator[YieldType, SendType, ReturnType]
    def countdown(n: int) -> Generator[int, None, str]:
        """倒计时生成器"""
        while n > 0:
            yield n
            n -= 1
        return "发射!"
    
    # 简单情况可以用 Iterator
    def fibonacci(limit: int) -> Iterator[int]:
        """斐波那契数列"""
        a, b = 0, 1
        while a < limit:
            yield a
            a, b = b, a + b
    
    print("倒计时:", list(countdown(5)))
    print("斐波那契:", list(fibonacci(100)))
# endregion

# region 示例4: 上下文管理器的类型注释
if True:  # 改为 False 可跳过此示例
    @contextmanager
    def timer(name: str) -> Generator[None, None, None]:
        """计时上下文管理器"""
        import time
        start = time.time()
        print(f"[{name}] 开始")
        yield
        elapsed = time.time() - start
        print(f"[{name}] 结束，耗时: {elapsed:.4f}秒")
    
    with timer("计算"):
        total = sum(range(1000000))
        print(f"计算结果: {total}")
# endregion

# region 示例5: 类方法的 Self 类型 (Python 3.11+)
if True:  # 改为 False 可跳过此示例
    # Python 3.11+ 可以使用 Self
    # from typing import Self
    
    # 兼容旧版本的写法
    T = TypeVar('T', bound='Builder')
    
    class Builder:
        def __init__(self) -> None:
            self.parts: list[str] = []
        
        def add(self: T, part: str) -> T:
            """返回 self 以支持链式调用"""
            self.parts.append(part)
            return self
        
        def build(self) -> str:
            return " + ".join(self.parts)
    
    class AdvancedBuilder(Builder):
        def add_special(self: T, part: str) -> T:
            self.parts.append(f"[{part}]")
            return self
    
    # 链式调用，类型正确传递
    result = AdvancedBuilder().add("A").add_special("B").add("C").build()
    print(f"构建结果: {result}")
    
    # Python 3.11+ 写法:
    # from typing import Self
    # def add(self, part: str) -> Self:
    #     ...
# endregion

# region 示例6: 回调函数与高阶函数
if True:  # 改为 False 可跳过此示例
    T = TypeVar('T')
    
    def retry(
        times: int,
        exceptions: tuple[type[Exception], ...] = (Exception,)
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """重试装饰器"""
        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                last_exception: Exception | None = None
                for attempt in range(times):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        print(f"尝试 {attempt + 1}/{times} 失败: {e}")
                raise last_exception or RuntimeError("未知错误")
            return wrapper
        return decorator
    
    @retry(times=3, exceptions=(ValueError,))
    def unstable_function(succeed_on: int) -> str:
        import random
        if random.randint(1, 3) != succeed_on:
            raise ValueError("随机失败")
        return "成功!"
    
    try:
        result = unstable_function(2)
        print(f"结果: {result}")
    except ValueError as e:
        print(f"最终失败: {e}")
# endregion
