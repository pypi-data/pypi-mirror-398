

class ScanOnTemplate:
    @classmethod
    def gen_main_template(cls, host: str, port: int, reload: bool, name: str):
        return f"""from fastapi_boot.core import provide_app
import uvicorn

app = provide_app()


if __name__ == '__main__':
    uvicorn.run('main:app', host='{host}', port={port}, reload={reload})
"""

    @classmethod
    def gen_controller(cls, name: str):
        constroller_cls_name = f'{name}Controller'
        return f"""from fastapi import Query
from fastapi_boot.core import Controller, Get, Post


@Controller('/fbv', tags=['fbv controller']).get('')
def _():
    return 'fbv'


@Controller('/cbv', tags=['cbv controller'])
class {constroller_cls_name}:
    @Get('/foo', summary='foo')
    async def foo(self):
        return 'foo'

    @Post('/bar', summary='bar')
    async def bar(self, p: str = Query(default='p')):
        return p        
"""


class ScanOffTemplate:
    @classmethod
    def gen_main_template(cls, host: str, port: int, reload: bool, name: str):
        constroller_cls_name = f'{name}Controller'
        return f"""from fastapi_boot.core import provide_app
from src.controller.{name} import {constroller_cls_name}
import uvicorn

app = provide_app(controllers=[{constroller_cls_name}])


if __name__ == '__main__':
    uvicorn.run('main:app', host='{host}', port={port}, reload={reload})
"""

    @classmethod
    def gen_controller(cls, name: str):
        constroller_cls_name = f'{name}Controller'
        return f"""from fastapi import Query
from fastapi_boot.core import Controller, Get, Post


@Controller('/fbv', tags=['fbv controller']).get('')
def _():
    return 'fbv'


@Controller('/cbv', tags=['cbv controller'])
class {constroller_cls_name}:
    @Get('/foo', summary='foo')
    async def foo(self):
        return 'foo'

    @Post('/bar', summary='bar')
    async def bar(self, p: str = Query(default='p')):
        return p        
"""
