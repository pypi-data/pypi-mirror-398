"""
Python 类型注释进阶
===================
介绍 Optional, Union, Any, Callable 等常用类型
"""
from typing import Optional, Union, Any, Callable, Literal

# region 示例1: Optional - 可选类型（值可能为 None）
if True:  # 改为 False 可跳过此示例
    def find_user(user_id: int) -> Optional[str]:
        """查找用户，可能返回 None"""
        users = {1: "Alice", 2: "Bob"}
        return users.get(user_id)  # 找不到返回 None
    
    # Optional[str] 等价于 Union[str, None] 或 str | None (3.10+)
    result: Optional[str] = find_user(1)
    print(f"找到用户: {result}")
    
    result = find_user(999)
    print(f"未找到用户: {result}")
# endregion

# region 示例2: Union - 联合类型（多种类型之一）
if True:  # 改为 False 可跳过此示例
    def process_id(id_value: Union[int, str]) -> str:
        """处理ID，可以是整数或字符串"""
        return f"ID: {id_value}"
    
    # Python 3.10+ 可以用 | 语法
    # def process_id(id_value: int | str) -> str:
    
    print(process_id(123))
    print(process_id("ABC-456"))
    
    # 多类型联合
    Number = Union[int, float, complex]
    value: Number = 3.14
    print(f"数值类型: {value}")
# endregion

# region 示例3: Any - 任意类型
if True:  # 改为 False 可跳过此示例
    def debug_print(value: Any) -> None:
        """打印任意类型的值"""
        print(f"值: {value}, 类型: {type(value).__name__}")
    
    debug_print(42)
    debug_print("hello")
    debug_print([1, 2, 3])
    debug_print({"key": "value"})
    
    # Any 表示跳过类型检查，应谨慎使用
# endregion

# region 示例4: Callable - 可调用对象（函数类型）
if True:  # 改为 False 可跳过此示例
    # Callable[[参数类型列表], 返回类型]
    def apply_operation(
        x: int, 
        y: int, 
        operation: Callable[[int, int], int]
    ) -> int:
        """应用一个操作函数"""
        return operation(x, y)
    
    def add(a: int, b: int) -> int:
        return a + b
    
    def multiply(a: int, b: int) -> int:
        return a * b
    
    print(f"加法: {apply_operation(3, 4, add)}")
    print(f"乘法: {apply_operation(3, 4, multiply)}")
    print(f"Lambda: {apply_operation(3, 4, lambda a, b: a - b)}")
# endregion

# region 示例5: Literal - 字面量类型（限定具体值）
if True:  # 改为 False 可跳过此示例
    def set_mode(mode: Literal["read", "write", "append"]) -> str:
        """只接受特定的字符串值"""
        return f"模式设置为: {mode}"
    
    print(set_mode("read"))
    print(set_mode("write"))
    # set_mode("delete")  # 类型检查器会报错，但运行时不会
    
    # 也可以用于数字
    Direction = Literal[1, -1, 0]
    def move(direction: Direction) -> str:
        return f"移动方向: {direction}"
    
    print(move(1))
# endregion

# region 示例6: 类型别名
if True:  # 改为 False 可跳过此示例
    # 简单类型别名
    UserId = int
    Username = str
    
    # 复杂类型别名
    UserInfo = dict[str, Union[str, int]]
    UserList = list[UserInfo]
    
    def get_users() -> UserList:
        return [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30}
        ]
    
    users: UserList = get_users()
    print(f"用户列表: {users}")
    
    # Python 3.10+ 推荐使用 TypeAlias
    # from typing import TypeAlias
    # UserId: TypeAlias = int
# endregion
