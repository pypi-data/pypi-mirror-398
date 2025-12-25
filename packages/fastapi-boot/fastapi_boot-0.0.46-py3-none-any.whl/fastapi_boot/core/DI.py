from collections.abc import Callable
from inspect import Parameter, _empty, signature, isclass
import time
from typing import Annotated, Any, TypeVar, cast, get_args, get_origin, overload

from .const import dep_store, app_store, task_store
from .model import DependencyNotFoundException, InjectFailException, AppRecord
from .utils import get_call_filename, is_position_only_param

T = TypeVar('T')


def _inject(app_record: AppRecord, tp: type[T], name: str | None) -> T:
    """注入单个依赖

    Args:
        app_record (AppRecord)
        tp (type[T])
        name (str | None)

    Returns:
        T: 注入的依赖
    """
    start = time.time()

    def raise_func():
        name_info = f"名为 '{name}' " if name is not None else ''
        raise DependencyNotFoundException(
            f"类型为 '{tp}' {name_info}的依赖未找到")
    while True:
        if res := dep_store.inject_dep(tp, name):
            return res
        # 没找到，不扫描，直接报错
        if not app_record.should_scan:
            raise_func()
        # 等待
        # TODO 是否需要尝试运行一次任务
        # task_store.emit(app_record)
        time.sleep(app_record.inject_retry_step)
        if time.time() - start > app_record.inject_timeout:
            raise_func()


def inject_params_deps(app_record: AppRecord, params: list[Parameter]):
    """

    Args:
        app_record (AppRecord): app_record
        params (list[Parameter]): params

    Raises:
        InjectFailException: _description_

    Returns:
        _type_: _description_
    """
    position_params = []
    kw_params = {}

    def add_param(param: Parameter, value: Any):
        if is_position_only_param(param):
            position_params.append(value)
        else:
            kw_params.update({param.name: value})

    for param in params:
        # 1. with default
        if param.default != _empty:
            add_param(param, param.default)
        else:
            # 2. without default
            # 2.1 no annotation
            if param.annotation == _empty:
                raise InjectFailException(
                    f'The annotation of param "{param.name}" is missing, add an annotation or give a default value'
                )
            # 2.2. with Annotated, has type and name
            if get_origin(param.annotation) == Annotated:
                tp, name, *_ = get_args(param.annotation)
                ins = _inject(app_record, tp, name)
                add_param(param, ins)
            else:
                # 2.2.2 only type, no name
                ins = _inject(app_record, param.annotation, None)
                add_param(param, ins)
    return position_params, kw_params


# ------------------------------------------------------- Bean ------------------------------------------------------- #


def collect_bean(app_record: AppRecord, func: Callable, name: str | None = None):
    """收集Bean装饰的函数运行结果

    Args:
        app_record (AppRecord): _description_
        func (Callable): _description_
        name (str | None, optional): _description_. Defaults to None.
    """
    params = list(signature(func).parameters.values())
    return_annotations = signature(func).return_annotation
    calling_params = inject_params_deps(app_record, params)
    instance = func(*calling_params[0], **calling_params[1])
    tp = return_annotations if return_annotations != _empty else type(instance)
    dep_store.add_dep(tp, name, instance)


@overload
def Bean(func_or_name: str, /): ...
@overload
def Bean(func_or_name: Callable[..., T], /): ...


def Bean(func_or_name: str | Callable[..., T], /):
    """用于装饰函数，将返回值收集为依赖；最好显式写出函数返回类型
    # Example
    1. collect by `type`
    ```python
    @dataclass
    class Foo:
        bar: str

    @Bean
    def _() -> Foo:
        return Foo('baz')
    ```

    2. collect by `name`
    ```python
    class User(BaseModel):
        name: str = Field(max_length=20)
        age: int = Field(gt=0)

    @Bean('user')
    def _() -> User:
        return User(name='zs', age=20)

    @Bean('user2)
    def _() -> User:
        return User(name='zs', age=21)
    ```
    """
    filename = get_call_filename()
    if callable(func_or_name):
        task_store.schedule(
            filename, lambda app_record: collect_bean(app_record, func_or_name))
        return func_or_name
    else:
        def wrapper(func: Callable[..., T]):
            task_store.schedule(filename, lambda app_record: collect_bean(
                app_record, func, func_or_name))
            return func
        return wrapper


# ---------------------------------------------------- Injectable ---------------------------------------------------- #
def inject_init_deps_and_get_instance(app_record: AppRecord, cls: type[T]) -> T:
    """_inject cls's __init__ params and get params deps"""
    old_params = list(signature(cls.__init__).parameters.values())[1:]  # self
    new_params = [
        i for i in old_params if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)
    ]  # *args、**kwargs
    calling_params = inject_params_deps(app_record, new_params)
    if hasattr(cls.__init__, '__globals__'):
        cls.__init__.__globals__.update({cls.__name__: cls})
    return cls(*calling_params[0], **calling_params[1])


def collect_dep(app_record: AppRecord, cls: type, name: str | None = None):
    """收集cls初始化时需要的依赖

    Args:
        app_record (AppRecord): _description_
        cls (type): _description_
        name (str | None, optional): _description_. Defaults to None.
    """
    instance = inject_init_deps_and_get_instance(app_record, cls)
    dep_store.add_dep(cls, name, instance)


@overload
def Injectable(class_or_name: str, /) -> Callable[[type[T]], type[T]]: ...


@overload
def Injectable(class_or_name: type[T], /) -> type[T]: ...


def Injectable(class_or_name: str | type[T], /):
    """初始化并把实例收集为依赖
    # Example
    ```python
    @Injectable
    class Foo:...

    @Injectable('bar1')
    class Bar:...
    ```

    """
    filename = get_call_filename()
    if isclass(class_or_name):
        task_store.schedule(filename, lambda app_record: collect_dep(
            app_record, class_or_name))
        return class_or_name
    else:
        def wrapper(cls: type[T]):
            task_store.schedule(filename, lambda app_record: collect_dep(
                app_record, cls, class_or_name))
            return cls

        return cast(Callable[[type[T]], type[T]], wrapper)


# ------------------------------------------------------ Inject ------------------------------------------------------ #
class AtUsable(type):
    """support @"""

    def __matmul__(self, other: type[T]) -> T:
        filename = get_call_filename()
        return _inject(app_store.get_or_raise(filename), other, cast(type[Inject], self).latest_named_deps_record.get(filename))

    def __rmatmul__(self, other: type[T]) -> T:
        filename = get_call_filename()
        return _inject(app_store.get_or_raise(filename), other, cast(type[Inject], self).latest_named_deps_record.get(filename))


class Inject(metaclass=AtUsable):
    """注入依赖
    >>> Example

    - inject by **type**
    ```python
    a = Inject(Foo)
    b = Inject @ Foo
    c = Foo @ Inject

    @Injectable
    class Bar:
        a = Inject(Foo)
        b = Inject @ Foo
        c = Foo @ Inject

        def __init__(self, ia: Foo, ic: Foo):
            self.ia = ia
            self.ib = Inject @ Foo
            self.ic = ic
    ```

    - inject by **type** and **name**
    ```python
    a = Inject(Foo, 'foo1')
    b = Inject.Qualifier('foo2') @ Foo
    c = Foo @ Inject.Qualifier('foo3')

    @Injectable
    class Bar:
        a = Inject(Foo, 'foo1')
        b = Inject.Qualifier('foo2') @ Foo
        c = Foo @ Inject.Qualifier('foo3')

        def __init__(self, ia: Annotated[Foo, 'foo1'], ic: Annotated[Foo, 'foo3']):
            self.ia = ia
            self.ib = Inject.Qualifier('foo2') @ Foo
            self.ic = ic
    ```
    """

    latest_named_deps_record: dict[str, str | None] = {}

    def __new__(cls, tp: type[T], name: str | None = None) -> T:
        """Inject(Type, name = None)"""
        filename = get_call_filename()
        cls.latest_named_deps_record.update({filename: name})
        res = _inject(app_store.get_or_raise(filename), tp, name)
        cls.latest_named_deps_record.update({filename: None})  # set name None
        return res

    @classmethod
    def Qualifier(cls, name: str):
        """Inject.Qualifier(name)"""
        filename = get_call_filename()
        cls.latest_named_deps_record.update({filename: name})
        return cls
