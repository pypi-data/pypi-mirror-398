from abc import ABC
from functools import wraps
from typing import Callable, Type

from pydantic import BaseModel


def api_method(request_model: Type[BaseModel], response_model: Type[BaseModel]):
    """
    api 方法注解
    :param request_model: 请求模型
    :param response_model: 响应模型
    :return:
    """

    def decorator(func: Callable):
        # 将注解信息绑定到原始函数
        func._is_api_method = True
        func._request_model = request_model
        func._response_model = response_model

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # 同步注解信息到包装函数，便于通过inspect发现
        wrapper._is_api_method = True
        wrapper._request_model = request_model
        wrapper._response_model = response_model

        return wrapper

    return decorator


# 定义 api 接口，暂时没啥用
class ApiInterface(ABC):
    pass
