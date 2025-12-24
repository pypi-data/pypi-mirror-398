"""
Python 泛型与类型变量
=====================
使用 TypeVar 和 Generic 创建可复用的泛型类型
"""
from typing import TypeVar, Generic, Sequence, Iterable

# region 示例1: TypeVar 基础 - 类型变量
if True:  # 改为 False 可跳过此示例
    # 定义类型变量
    T = TypeVar('T')
    
    def first(items: list[T]) -> T:
        """返回列表第一个元素，保持类型一致"""
        return items[0]
    
    # 类型检查器能推断返回类型
    num = first([1, 2, 3])        # 推断为 int
    text = first(["a", "b", "c"]) # 推断为 str
    
    print(f"第一个数字: {num}, 类型: {type(num).__name__}")
    print(f"第一个字符: {text}, 类型: {type(text).__name__}")
# endregion

# region 示例2: 受约束的 TypeVar
if True:  # 改为 False 可跳过此示例
    # 限制类型变量只能是特定类型
    Number = TypeVar('Number', int, float)
    
    def double(value: Number) -> Number:
        """只接受 int 或 float"""
        return value * 2
    
    print(f"整数翻倍: {double(5)}")
    print(f"浮点翻倍: {double(3.14)}")
    # double("hello")  # 类型检查器会报错
    
    # 使用 bound 限制为某类型的子类
    from typing import Sized
    S = TypeVar('S', bound=Sized)
    
    def get_length(item: S) -> int:
        """接受任何有 __len__ 方法的对象"""
        return len(item)
    
    print(f"列表长度: {get_length([1, 2, 3])}")
    print(f"字符串长度: {get_length('hello')}")
# endregion

# region 示例3: Generic 类 - 泛型容器
if True:  # 改为 False 可跳过此示例
    T = TypeVar('T')
    
    class Box(Generic[T]):
        """一个泛型盒子，可以存放任意类型"""
        def __init__(self, content: T) -> None:
            self.content = content
        
        def get(self) -> T:
            return self.content
        
        def set(self, content: T) -> None:
            self.content = content
    
    # 使用时指定具体类型
    int_box: Box[int] = Box(42)
    str_box: Box[str] = Box("hello")
    
    print(f"整数盒子: {int_box.get()}")
    print(f"字符串盒子: {str_box.get()}")
# endregion

# region 示例4: 多类型参数的泛型
if True:  # 改为 False 可跳过此示例
    K = TypeVar('K')
    V = TypeVar('V')
    
    class Pair(Generic[K, V]):
        """键值对泛型类"""
        def __init__(self, key: K, value: V) -> None:
            self.key = key
            self.value = value
        
        def swap(self) -> 'Pair[V, K]':
            """交换键值，返回新的 Pair"""
            return Pair(self.value, self.key)
    
    pair: Pair[str, int] = Pair("age", 25)
    print(f"原始: key={pair.key}, value={pair.value}")
    
    swapped = pair.swap()
    print(f"交换后: key={swapped.key}, value={swapped.value}")
# endregion

# region 示例5: 泛型函数的多种写法
if True:  # 改为 False 可跳过此示例
    T = TypeVar('T')
    
    # 方式1: 使用 Sequence（只读序列）
    def first_of_seq(items: Sequence[T]) -> T:
        return items[0]
    
    # 方式2: 使用 Iterable（可迭代对象）
    def first_of_iter(items: Iterable[T]) -> T:
        return next(iter(items))
    
    # Sequence 支持索引，Iterable 更通用
    print(f"从列表: {first_of_seq([1, 2, 3])}")
    print(f"从元组: {first_of_seq((4, 5, 6))}")
    print(f"从集合: {first_of_iter({7, 8, 9})}")  # 集合不支持索引
# endregion

# region 示例6: Python 3.12+ 新语法
if True:  # 改为 False 可跳过此示例
    # Python 3.12 引入了更简洁的泛型语法
    # 旧写法:
    # T = TypeVar('T')
    # def old_first(items: list[T]) -> T: ...
    
    # 新写法 (3.12+):
    # def new_first[T](items: list[T]) -> T:
    #     return items[0]
    
    # class NewBox[T]:
    #     def __init__(self, content: T) -> None:
    #         self.content = content
    
    print("Python 3.12+ 支持更简洁的泛型语法: def func[T](x: T) -> T")
    print("当前示例使用兼容旧版本的写法")
# endregion
