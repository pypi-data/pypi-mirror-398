from collections.abc import AsyncGenerator, Sequence
import concurrent
import concurrent.futures
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import asdict, is_dataclass
from functools import lru_cache
import os
from collections.abc import Callable, Coroutine
from pathlib import Path
import re
from types import NoneType
from typing import Any, Final, Protocol, TypeVar, cast, ParamSpec
from inspect import isclass, iscoroutinefunction
import concurrent
import warnings
from pydantic import BaseModel

from fastapi import Depends, FastAPI, Request, Response, WebSocket
from starlette.middleware import _MiddlewareFactory
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi.responses import JSONResponse
from .const import (
    PropNameConstant,
    UseMiddlewareReturnValuePlaceholder,
    app_store,
    task_store,
    dep_store,
    use_dep_record_store
)
from .model import AppRecord, UseMiddlewareRecord
from .utils import get_call_filename, match_path
from .shared import ScanMode

T = TypeVar('T')


def use_dep(dependency: Callable[..., T | Coroutine[Any, Any, T]] | None, use_cache: bool = True) -> T:
    """作为类变量，用于给Controller中所有endpoint添加依赖，效果等同于FastAPI的Depends

    >>> Example
    ```python
    def get_ua(request: Request):
        return request.headers.get('user-agent','')

    @Controller('/foo')
    class Foo:
        ua = use_dep(get_ua)

        @Get('/ua')
        def foo(self):
            return self.ua

    ```
    """
    value: T = Depends(dependency=dependency, use_cache=use_cache)
    use_dep_record_store.add(value)
    return value


def _create_use_middleware_return_value(record: UseMiddlewareRecord):
    bp = UseMiddlewareReturnValuePlaceholder()
    setattr(bp, PropNameConstant.USE_MIDDLEWARE, record)
    return bp


def use_http_middleware(*dispatches: Callable[[Request, Callable[[Request], Coroutine[Any, Any, Response]]], Any]):
    """给类中所有 **直接** http的endpoint添加http中间件

    ```python

    from collections.abc import Callable
    from typing import Any
    from fastapi import Request
    from fastapi_boot.core import Controller, use_http_middleware


    async def middleware_foo(request: Request, call_next: Callable[[Request], Any]):
        print('middleware_foo before')
        resp = await call_next(request)
        print('middleware_foo after')
        return resp

    async def middleware_bar(request: Request, call_next: Callable[[Request], Any]):
        print('middleware_bar before')
        resp = await call_next(request)
        print('middleware_bar after')
        return resp

    @Controller('/foo')
    class FooController:
        _ = use_http_middleware(middleware_foo, middleware_bar)

        # 1. middleware_bar before
        # 2. middleware_foo before
        # 3. call endpoint
        # 4. middleware_foo after
        # 5. middleware_bar after

        # ...
    ```

    """
    record = UseMiddlewareRecord(http_dispatches=list(dispatches))
    return _create_use_middleware_return_value(record)


def use_ws_middleware(
        *dispatches: Callable[[WebSocket, Callable[[WebSocket], Coroutine[Any, Any, None]]], Any],
        only_message: bool = False
):
    """给类中所有 **直接** websocket的endpoint添加websocket中间件
    >>> Params
    only_message=False: 只有收到消息会触发，连接等事件不会触发

    >>> Examples:
    ```python

    from collections.abc import Callable
    from typing import Any
    from fastapi import Request, WebSocket
    from fastapi_boot.core import Controller, use_http_middleware, middleware_ws_foo

    async def middleware_ws_foo(websocket: WebSocket, call_next: Callable):
        print('before ws send data foo') # as pos a
        await call_next(websocket)
        print('after ws send data foo') # as pos b

    async def middleware_ws_bar(websocket: WebSocket, call_next: Callable):
        print('before ws send data bar') # as pso c
        await call_next()
        print('after ws send data bar') # as pso d

    async def middleware_bar(request: Request, call_next: Callable[[Request], Any]):
        print('middleware_bar before') # as pos e
        resp = await call_next(request)
        print('middleware_bar after') # as pos f
        return resp


    @Controller('/chat')
    class WsController:
        _ = use_http_middleware(middleware_bar)
        ___ = use_ws_middleware(middleware_ws_bar, middleware_ws_foo, only_message=True)

        @Socket('/chat')
        async def chat(self, websocket: WebSocket):
            try:
                await websocket.accept()
                while True:
                    message = await websocket.receive_text()
                    # a c
                    await self.send_text(message)
                    # d b
            except:
                ...


        # e a c d b f
        @Post('/broadcast')
        async def send_broadcast_msg(self, msg: str = Query()):
            await self.broadcast(msg)
            return 'ok'
    ```

    """
    record = UseMiddlewareRecord(ws_dispatches=list(
        dispatches), ws_only_message=only_message)
    return _create_use_middleware_return_value(record)


DispatchFunc = Callable[[
    Request, Callable[[Request], Coroutine[Any, Any, Response]]], Any]
P = ParamSpec('P')


class DispatchCls(Protocol):
    async def dispatch(self, request: Request, call_next: Callable): ...


def HTTPMiddleware(dispatch: DispatchFunc | type[DispatchCls]):
    """添加全局http middleware.

    Args:
        dispatch: Callable[[Request, Callable[[Request], Coroutine[Any, Any, Response]]], Any] or class with async `dispatch` method.
    Example:
    ```python
    from collections.abc import Callable
    from fastapi import Request
    from fastapi_boot.core import HTTPMiddleware

    @HTTPMiddleware
    async def barMiddleware(request: Request, call_next: Callable):
        print("before")
        res = await call_next(request)
        print("after")
        return res

    @HTTPMiddleware
    class FooMiddleware:
        async def foo(self, a: int):
            return a

        async def dispatch(self, request: Request, call_next: Callable):
            print('before')
            res = await call_next(request)
            print('after')
            print(await self.foo(1))
            return res
    ```
    """
    def task(app_record: AppRecord):
        if isclass(dispatch):
            Cls = type('Cls', (dispatch, BaseHTTPMiddleware), {})
            app_record.app.add_middleware(cast(_MiddlewareFactory, Cls))
        else:
            app_record.app.add_middleware(
                BaseHTTPMiddleware, cast(Callable, dispatch))
    task_store.schedule(get_call_filename(), task)
    return dispatch


DEFAULT_SCAN_PRIORITY: Final[int] = 1000


def provide_app(
        app: FastAPI | None = None,
        scan_mode: ScanMode = 'on',
        max_workers: int = 20,
        inject_timeout: float = 20,
        inject_retry_step: float = 0.05,
        exclude_scan_paths: Sequence[str | re.Pattern] = [],
        scan_priority: dict[str, int] = {},
        controllers: Sequence[Any] = [],
        beans: Sequence[Any] = []) -> FastAPI:
    """启动入口

    Args:
        app (FastAPI, optional): FastAPi实例. Defaults to None.
        scan_mode (ScanMode, optional): 扫描模式开关(默认开启，会扫描项目下的所有.py文件). Defaults to 'on'.
        max_workers (int, optional): 扫描最大线程数. Defaults to 20.
        inject_timeout (float, optional): 扫描注入超时时间. Defaults to 20.
        inject_retry_step (float, optional): 注入依赖重试间隔，单位s. Defaults to 0.05.
        exclude_scan_paths (Iterable[str | re.Pattern], optional): 排除扫描的目录/模块路径列表. Defaults to [].
        scan_priority (dict[str, int], optional): 扫描优先级，`{模块路径: 优先级}`，数字越小优先级越高，避免出现前面执行注入的模块数量超过max_workers，一直卡住导致后面无法收集. Defaults to {}.
        controllers (Sequence[Any], optional): scan_mode关闭时需手动导入Controller，可以传到这里，防止未使用被代码格式化工具移除. Defaults to [].
        beans (Sequence[Any], optional): scan_mode关闭时需手动导入bean，可以传到这里，防止未使用被代码格式化工具移除. Defaults to [].

    Raises:
        e: _description_

    Returns:
        FastAPI: _description_
    """
    app = app or FastAPI()
    provide_filepath = get_call_filename()
    # 缓存
    if app_record := app_store.get_or_none(provide_filepath):
        return app_record.repalce_app(app)
    # 清除
    app_store.clear()
    dep_store.clear()
    # provide_app所在的文件
    app_root_dir = os.path.dirname(provide_filepath)
    app_record = AppRecord(app, inject_timeout, inject_retry_step, scan_mode)
    app_store.add(app_root_dir, app_record)
    if not app_record.should_scan:
        task_store.emit(app_record=app_record)
        return app
    # app's prefix
    app_parts = Path(app_root_dir).parts
    proj_parts = Path(os.getcwd()).parts
    prefix_parts = app_parts[len(proj_parts):]
    # 收集扫描路径
    dot_paths = set()
    for root, _, files in os.walk(app_root_dir):
        for file in files:
            fullpath = os.path.join(root, file)
            if not file.endswith('.py') or fullpath == provide_filepath:
                continue
            dot_path = '.'.join(
                prefix_parts +
                Path(fullpath.replace('.py', '').replace(
                    app_root_dir, '')).parts[1:]
            )
            if any(match_path(p, dot_path) for p in exclude_scan_paths):
                continue
            dot_paths.add(dot_path)
    # 优先级排序
    for p in scan_priority:
        if p not in dot_paths:
            warnings.warn(f'模块{p}未被扫描，优先级配置无效')
    scan_priority = {pa: pr for pa,
                     pr in scan_priority.items() if pa in dot_paths}
    for p in dot_paths:
        scan_priority[p] = scan_priority.get(p, DEFAULT_SCAN_PRIORITY)
    dot_paths = sorted(
        scan_priority, key=lambda x: scan_priority[x])
    # 扫描
    futures: list[Future] = []
    with ThreadPoolExecutor(max_workers) as executor:
        for dot_path in dot_paths:
            future = executor.submit(__import__, dot_path)
            futures.append(future)
        concurrent.futures.wait(futures)
        for future in futures:
            try:
                future.result()
            except Exception as e:
                executor.shutdown(True, cancel_futures=True)
                raise e
    task_store.emit(app_record=app_record)
    return app


def on_app_ready(callback: Callable[[FastAPI], NoneType]):
    """app准备完毕后的回调"""
    task_store.schedule(get_call_filename(),
                        lambda app_record: callback(app_record.app))


def Lifespan(func: Callable[[FastAPI], AsyncGenerator[None, None]]):
    """生命周期装饰器，等于FastAPI(lifespan = xxx)

    ```python
    @Lifespan
    async def _(app:FastAPI):
        # init db
        yield
        # close db
    ```
    """
    def task(app_record: AppRecord):
        app_record.app.router.lifespan_context = asynccontextmanager(func)
    task_store.schedule(get_call_filename(), task)
    return func


# -------------------------------------------------------------------------------------------------------------------- #
E = TypeVar('E', bound=Exception)

HttpHandler = Callable[[Request, E], Any]
WsHandler = Callable[[WebSocket, E], Any]


def ExceptionHandler(exp: int | type[E]):
    """声明式全局异常处理，用法同`@app.exception_handler`, 被装饰的函数可以返回`BaseModel instance`、`dataclass`、`dict` or `JSONResponse`.
    ```python
    @ExceptionHandler(MyException)
    async def _(req: Request, exp: AException):
        ...
    ```
    Declarative style of the following code:
    ```python
    @app.exception_handler(AException)
    async def _(req: Request, exp: AException):
        ...
    @app.exception_handler(BException)
    def _(req: Request, exp: BException):
        ...

    @app.exception_handler(CException)
    async def _(req: WebSocket, exp: CException):
        ...
    @app.exception_handler(DException)
    def _(req: WebSocket, exp: DException):
        ...
    ```
    """

    def decorator(handler: HttpHandler | WsHandler):
        # wrap handler
        async def wrapper(*args, **kwds):
            resp = await handler(*args, **kwds) if iscoroutinefunction(handler) else handler(*args, **kwds)
            if isinstance(resp, BaseModel):
                resp = resp.model_dump()
            elif is_dataclass(resp) and not isinstance(resp, type):
                resp = asdict(resp)
            if isinstance(resp, dict):
                return JSONResponse(resp)
            elif isinstance(resp, Response):
                return resp
            else:
                return Response(resp)
        task_store.schedule(get_call_filename(
        ), lambda app_record: app_record.app.add_exception_handler(exp, wrapper))
        return handler

    return decorator


def Lazy(func: Callable[[], T]) -> T:
    """依赖懒注入，首次用到才会注入并缓存

    >>> Example

    ```python
    @dataclass
    class User:
        name: str
        age: int
    Bean('bar')(lambda: User('bar', 20))

    @Service
    class FooService:
        bar = Lazy(lambda: Inject(User, 'bar'))

        def some_method(self) -> User:
            # called after sacn
            return self.bar
    ```
    """
    return cast(T, property(lru_cache(None)(lambda _: func())))
