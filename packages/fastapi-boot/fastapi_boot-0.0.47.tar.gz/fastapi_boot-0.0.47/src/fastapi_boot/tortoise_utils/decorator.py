from collections.abc import Callable, Coroutine
from functools import wraps
from inspect import signature
import inspect
import re
from string import Formatter
from typing import Any, ParamSpec, TypeVar, cast, get_args, get_origin, overload
from warnings import warn
from pydantic import BaseModel
from tortoise import Model, Tortoise
from tortoise.backends.sqlite.client import SqliteClient
from tortoise.backends.mysql.client import MySQLClient
from tortoise.backends.asyncpg.client import AsyncpgDBClient


def get_func_params_dict(func: Callable, *args, **kwds):
    """

    Args:
        func (Callable)

    Returns:
        _type_: dict
    """
    res = {}
    for i, (k, v) in enumerate(signature(func).parameters.items()):
        if len(args) > i:
            res[k] = args[i]
        elif v.default != inspect._empty:
            res[k] = v.default
        else:
            res[k] = kwds.get(k)
    return res


PM = TypeVar('PM', bound=BaseModel)
TM = TypeVar('TM', bound=Model)
P = ParamSpec('P')
formatter = Formatter()


class Sql:
    """执行原生sql语句

    1. 支持**装饰器**和**直接调用调用**两种写法
    2. 占位符`{var_name!r}`时**字符串带引号**
    3. 返回值类型注解**可省略**，固定返回元组: (rows: `int`, result: `list[dict]`)

    >>> Example
    ```python
    from fastapi_boot.tortoise_utils import Sql

    @Sql('select * from user where id={id}')
    async def get_user_by_id(id: str) -> tuple[int, list[dict]]:...

    class Bar:
        @Sql('select * from {table} where id={dto.id} and name={dto.name!r}').fill(table='User')
        async def get_user(self, dto: UserDTO):...

    async def get_user_by_id(id: str):
        return await Sql('select * from user where id={id}').fill(id=id).execute()


    # 结果可能像这样： (1, [{'id': 0, 'name': 'foo', 'age': 20}])
    ```
    """

    def __init__(self, sql: str, connection_name: str = 'default'):
        """

        Args:
            sql (str): 原始sql语句，用`{变量名}`占位，支持`{ins.a}`等方式取属性
            connection_name (str, optional): 连接名. Defaults to 'default'.
        """
        self.sql = sql.strip()
        self.connection_name = connection_name
        self.pattern = re.compile(r'{.*?}', flags=re.S)
        # 是否已将插值表达式替换为占位符，只运行一次
        self.formatted: bool = False
        # 占位符的变量，{xxx}、{xxx.xxx}、{xxx[0]}等字符串列表
        self.matched_params: list[str] = []

    @property
    def is_sqlite(self):
        conn = Tortoise.get_connection(self.connection_name)
        return conn.__class__ == SqliteClient

    @property
    def is_mysql(self):
        conn = Tortoise.get_connection(self.connection_name)
        return conn.__class__ == MySQLClient

    @property
    def is_postgresql(self):
        conn = Tortoise.get_connection(self.connection_name)
        return conn.__class__ == AsyncpgDBClient

    @property
    def placeholder(self):
        if self.is_sqlite:
            return '?'
        # pg、mysql的都看作%s，pg的后面再改
        return '%s'

    def _interpolation2placeholder(self):
        """插值表达式转为占位符"""
        # {xxx}替换为sql占位符
        self.sql = self.placeholder.join(self.pattern.split(self.sql))
        # 如果是pg，占位符改为$1、$2、...
        if self.is_postgresql:
            cnt = 1

            def fn(_):
                nonlocal cnt
                res = f'${cnt}'
                cnt += 1
                return res
            self.sql = re.compile(f'{self.placeholder}').sub(fn, self.sql)

    def fill(self, **kwds):
        """向sql语句中的占位符{}填充已知参数，**会直接替换**，不要填充不确定的值，防止sql注入

        Args:
            **kwds (Any)
        """
        for k, v in kwds.items():
            self.sql = self.sql.replace('{'+f'{k}'+'}', v)
        return self

    async def execute(self) -> tuple[int, list[dict[Any, Any]]]:
        """非装饰器用法时执行sql

        Returns:
            `tuple[int, list[dict[Any, Any]]]`
        """

        async def func(): ...

        return await self(func)()

    def __call__(
        self, func: Callable[P, Coroutine[Any, Any, None | tuple[int, list[dict]]]]
    ) -> Callable[P, Coroutine[Any, Any, tuple[int, list[dict]]]]:
        """装饰函数

        Args:
            func (Callable[P, Coroutine[Any, Any, None  |  tuple[int, list[dict]]]]): 不写返回值类型注解或写`tuple[int, list[dict]]`

        Returns:
            Callable[P, Coroutine[Any, Any, tuple[int, list[dict]]]]
        """
        if not self.formatted:
            self.formatted = True
            # 占位符的变量，{xxx}、{xxx.xxx}、{xxx[0]}等
            self.matched_params = self.pattern.findall(self.sql)
            self._interpolation2placeholder()

        @wraps(func)
        async def wrapper(*args: P.args, **kwds: P.kwargs):
            calling_params = get_func_params_dict(func, *args, **kwds)
            # 根据占位符
            actual_params = [eval(param[1:-1], calling_params)
                             for param in self.matched_params]
            rows, resp = await Tortoise.get_connection(self.connection_name).execute_query(self.sql, actual_params)
            if self.is_sqlite:
                resp = list(map(dict, resp))
            return rows, resp
        return cast(Callable[P, Coroutine[Any, Any, tuple[int, list[dict]]]], wrapper)


class Select(Sql):
    """Select实现，返回`None` | `BaseModel` | `Model` | `list[BaseModel]` | `list[Model]` | `list[dict]`
    >>> Example

    ```python
    # 1. 返回值类型注解为`BaseModel`、`Model`
    class User(BaseModel):
        id: str
        name: str
        age: int

    @Select('select * from user where id={id!r}')
    async def get_user_by_id1(id: str) -> User:...


    async def get_user_by_id2(id: str) -> User:
        return await Select('select * from user where id={id!r}').fill(id=id).execute(User)

    # 可能的返回值 User(id='1', name='foo', age=20) 或 None

    # ----------------------------------------------------------------------------------

    # 2. 返回值类型注解为`list[BaseModel]`、`list[Model]`
    @dataclass
    class UserDTO:
        agegt: int

    @Repository
    class Bar:
        @Select('select * from user where age>{dto.agegt}')
        async def query_users(self, dto: UserDTO) -> list[User]:...

    # 可能的返回值 [User(id='2', name='bar', age=21), User(id='3', name='baz', age=22)] 或 []

    # ----------------------------------------------------------------------------------

    # 3. 返回值类型注解为`list[dict]`、None, 返回值是`Sql`返回元组的第二项, 即`list[dict]`


    # ----------------------------------------------------------------------------------
    # 4. Summary

    from pydantic import BaseModel
    from tortoise import Model

    T = TypeVar('T', BaseModel, Model)

    # |       return annotation     |      return value type      |
    # |               T             |            T|None           |
    # |            list[T]          |            list[T]          |
    # |      None|list|list[dict]   |           list[dict]        |

    ```
    """

    @overload
    async def execute(self, expect: type[PM]) -> PM | None: ...
    @overload
    async def execute(self, expect: type[PM]) -> PM | None: ...
    @overload
    async def execute(self, expect: type[TM]) -> TM | None: ...

    @overload
    async def execute(self, expect: type[list[PM]]) -> list[PM]: ...
    @overload
    async def execute(self, expect: type[list[TM]]) -> list[TM]: ...

    @overload
    async def execute(self, expect: None | type[list] |
                      type[list[dict]] = None) -> list[dict]: ...

    async def execute(
        self, expect: type[PM] | type[TM] | type[list[PM]] | type[list[TM]] | None | type[list] | type[list[dict]] = None
    ) -> PM | TM | list[PM] | list[TM] | None | list[dict]:
        """非装饰器用法时执行sql

        Args:
            expect (`type[PM] | type[TM] | type[list[PM]] | type[list[TM]] | None | type[list] | type[list[dict]]`, optional): _description_. Defaults to None.

        Returns:
            `PM | TM | list[PM] | list[TM] | None | list[dict]`: _description_
        """
        async def func(): ...

        setattr(func, '__annotations__', {'return': expect})
        return await self(func)()

    @overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, PM]]) -> Callable[P,
                                                                               Coroutine[Any, Any, PM | None]]: ...

    @overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, TM]]) -> Callable[P,
                                                                               Coroutine[Any, Any, TM | None]]: ...

    @overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, list[PM]]]) -> Callable[P,
                                                                                     Coroutine[Any, Any, list[PM]]]: ...

    @overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, list[TM]]]) -> Callable[P,
                                                                                     Coroutine[Any, Any, list[TM]]]: ...

    @overload
    def __call__(
        self, func: Callable[P, Coroutine[Any, Any, None | list | list[dict]]]
    ) -> Callable[P, Coroutine[Any, Any, list[dict]]]: ...

    def __call__(
        self,
        func: Callable[P, Coroutine[Any, Any, PM | TM | list[PM] | list[TM] | None | list | list[dict]]] | None,
    ) -> Callable[P, Coroutine[Any, Any, PM | TM | list[PM] | list[TM] | None | list[dict]]]:
        """

        Args:
            func (`Callable[P, Coroutine[Any, Any, PM  |  list[PM]  |  TM  |  list[TM]  |  list[dict]  |  None]] | None`): _description_

        Returns:
            `Callable[P, Coroutine[Any, Any, PM | list[PM] | TM | list[TM] | list[dict] | None]]`: _description_
        """
        anno = func.__annotations__.get('return')
        super_class = super()

        @wraps(func)  # type: ignore
        async def wrapper(*args: P.args, **kwds: P.kwargs):
            lines, resp = await super_class.__call__(cast(Callable[P, Coroutine[Any, Any, None | tuple[int, list[dict]]]], func))(*args, **kwds)
            if anno is None or anno is list:
                return resp
            elif get_origin(anno) is list:
                arg = get_args(anno)[0]
                return [arg(**i) for i in resp]
            else:
                if lines > 1:
                    warn(
                        f'查到了 {lines} 条结果, 但期望类型是 "{anno.__name__}", 因此只返回第一条结果'
                    )
                return anno(**resp[0]) if len(resp) > 0 else None
        return wrapper


class Insert(Sql):
    """用法同`Sql`

    > 返回值类型注解为`None`|`int`，始终返回`int`，表示`操作行数`

    """

    async def execute(self):
        """执行`insert`

        >>> Exampe

        ```python
        @Insert('insert into {user} values("foo", 20, 1)').fill(user=UserDO.Meta.table)
        async def insert_user():...

        rows: int = await insert_user()

        rows: int = await Insert('insert into {user} values("foo", 20, 1)').fill(user=UserDO.Meta.table).execute()
        ```

        """

        return super().execute()

    def __call__(self, func: Callable[P, Coroutine[Any, Any, None | int]]) -> Callable[P, Coroutine[Any, Any, int]]:
        """

        Args:
            func (`Callable[P, Coroutine[Any, Any, None  |  int]]`): _description_

        Returns:
            `Callable[P, Coroutine[Any, Any, int]]`: _description_
        """
        super_class = super()

        @wraps(func)
        async def wrapper(*args: P.args, **kwds: P.kwargs) -> int:
            return (await super_class.__call__(cast(Callable[P, Coroutine[Any, Any, None | tuple[int, list[dict]]]], func))(*args, **kwds))[0]
        return wrapper


class Update(Insert):
    """

    > 返回值类型注解为`None`|`int`，始终返回`int`，表示`操作行数`

    """

    async def execute(self):
        """执行`update`

        用法同`Insert`
        """

        return super().execute()


class Delete(Insert):
    """

    > 返回值类型注解为`None`|`int`，始终返回`int`，表示`操作行数`

    """

    async def execute(self):
        """执行`update`

        用法同`Insert`
        """

        return super().execute()
