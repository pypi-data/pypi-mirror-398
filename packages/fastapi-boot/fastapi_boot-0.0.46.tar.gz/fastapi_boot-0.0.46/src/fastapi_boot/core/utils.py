import inspect
import re


def get_call_filename(layer: int = 1):
    """获取本函数调用栈中第layer+1层所在的文件名

    Args:
        layer (int, optional): 调用层级. Defaults to 1.

    Returns:
        _type_: 文件名
    """
    return inspect.stack()[layer + 1].filename.capitalize()


def match_path(pattern: str | re.Pattern, target: str):
    if isinstance(pattern, str):
        return target == pattern or (target.startswith(pattern) and target[len(pattern)] == '.')
    return re.match(pattern, target) is not None


def is_position_only_param(param: inspect.Parameter):
    return param.kind == inspect.Parameter.POSITIONAL_ONLY
