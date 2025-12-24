"""
Python 类型注释高级技巧
======================
TypedDict, Final, Annotated, overload, cast 等高级用法
"""
from typing import (
    TypedDict, Final, Annotated, 
    overload, cast, get_type_hints,
    TYPE_CHECKING, NewType
)

# region 示例1: TypedDict - 带类型的字典
if True:  # 改为 False 可跳过此示例
    class UserDict(TypedDict):
        """定义字典的结构"""
        name: str
        age: int
        email: str
    
    # 可选字段使用 total=False 或 NotRequired (3.11+)
    class ConfigDict(TypedDict, total=False):
        debug: bool
        timeout: int
        host: str
    
    user: UserDict = {
        "name": "Alice",
        "age": 25,
        "email": "alice@example.com"
    }
    
    config: ConfigDict = {"debug": True}  # 其他字段可选
    
    print(f"用户: {user}")
    print(f"配置: {config}")
    
    # TypedDict 在运行时就是普通 dict
    print(f"类型: {type(user)}")
# endregion

# region 示例2: Final - 常量标记
if True:  # 改为 False 可跳过此示例
    # Final 表示值不应被修改
    MAX_SIZE: Final[int] = 100
    API_URL: Final = "https://api.example.com"  # 类型可推断
    
    class Settings:
        DEBUG: Final[bool] = False
        
        def __init__(self) -> None:
            self.name: Final[str] = "MyApp"
    
    print(f"最大尺寸: {MAX_SIZE}")
    print(f"API地址: {API_URL}")
    
    # MAX_SIZE = 200  # 类型检查器会警告，但运行时不会报错
    print("Final 只是提示，运行时不强制")
# endregion

# region 示例3: Annotated - 附加元数据
if True:  # 改为 False 可跳过此示例
    # Annotated 可以给类型添加额外信息
    PositiveInt = Annotated[int, "必须是正整数"]
    Email = Annotated[str, "邮箱格式"]
    
    def create_user(
        name: str,
        age: Annotated[int, "年龄必须 >= 0"],
        email: Email
    ) -> dict[str, str | int]:
        return {"name": name, "age": age, "email": email}
    
    # 常用于验证框架（如 Pydantic）
    # from pydantic import Field
    # age: Annotated[int, Field(ge=0, le=150)]
    
    user = create_user("Bob", 30, "bob@example.com")
    print(f"创建用户: {user}")
    
    # 获取注释信息
    hints = get_type_hints(create_user, include_extras=True)
    print(f"age 的类型注释: {hints['age']}")
# endregion

# region 示例4: overload - 函数重载
if True:  # 改为 False 可跳过此示例
    # overload 用于声明同一函数的多个签名
    @overload
    def process(value: int) -> int: ...
    @overload
    def process(value: str) -> str: ...
    @overload
    def process(value: list[int]) -> list[int]: ...
    
    def process(value: int | str | list[int]) -> int | str | list[int]:
        """实际实现"""
        if isinstance(value, int):
            return value * 2
        elif isinstance(value, str):
            return value.upper()
        else:
            return [x * 2 for x in value]
    
    # 类型检查器能根据输入推断输出类型
    result1 = process(5)        # 推断为 int
    result2 = process("hello")  # 推断为 str
    result3 = process([1, 2])   # 推断为 list[int]
    
    print(f"整数处理: {result1}")
    print(f"字符串处理: {result2}")
    print(f"列表处理: {result3}")
# endregion

# region 示例5: cast - 类型转换提示
if True:  # 改为 False 可跳过此示例
    # cast 告诉类型检查器"相信我，这是这个类型"
    data: dict[str, object] = {"name": "Alice", "age": 25}
    
    # 类型检查器不知道 data["name"] 是 str
    # name = data["name"].upper()  # 类型检查器会报错
    
    # 使用 cast 告诉检查器
    name = cast(str, data["name"])
    print(f"姓名: {name.upper()}")  # 现在可以调用 str 方法
    
    # cast 在运行时什么都不做，只是返回原值
    wrong = cast(int, "hello")  # 运行时不会报错！
    print(f"cast 不做运行时检查: {wrong}, 类型: {type(wrong)}")
# endregion

# region 示例6: TYPE_CHECKING - 避免循环导入
if True:  # 改为 False 可跳过此示例
    # TYPE_CHECKING 只在类型检查时为 True，运行时为 False
    if TYPE_CHECKING:
        # 这里的导入只用于类型检查，不会在运行时执行
        # from some_module import SomeClass
        pass
    
    print(f"TYPE_CHECKING 的值: {TYPE_CHECKING}")
    
    # 常用于解决循环导入问题
    # 文件 a.py:
    #   if TYPE_CHECKING:
    #       from b import B
    #   def func(b: 'B') -> None: ...  # 使用字符串形式
    
    # 文件 b.py:
    #   if TYPE_CHECKING:
    #       from a import A
    #   def func(a: 'A') -> None: ...
# endregion

# region 示例7: NewType - 创建独特类型
if True:  # 改为 False 可跳过此示例
    # NewType 创建一个独特的类型，用于区分相同底层类型
    UserId = NewType('UserId', int)
    OrderId = NewType('OrderId', int)
    
    def get_user(user_id: UserId) -> str:
        return f"User #{user_id}"
    
    def get_order(order_id: OrderId) -> str:
        return f"Order #{order_id}"
    
    uid = UserId(123)
    oid = OrderId(456)
    
    print(get_user(uid))
    print(get_order(oid))
    
    # 类型检查器会区分 UserId 和 OrderId
    # get_user(oid)  # 类型检查器会报错
    
    # 但运行时它们都是 int
    print(f"UserId 类型: {type(uid)}")
# endregion
