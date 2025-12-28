from typing import Optional, Type, TypeVar

import requests
from kaq_quant_common.api.common.auth import get_auth_token
from kaq_quant_common.utils import logger_utils
from pydantic import BaseModel

R = TypeVar("R", bound=BaseModel)


class ApiClientBase:
    """
    api 客户端
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        self._base_url = base_url.rstrip("/")
        self._token = token if token is not None else get_auth_token()
        self._logger = logger_utils.get_logger(self)

    # 发送请求
    def _make_request(self, method_name: str, request_data: BaseModel, response_model: Type[R]) -> R:
        url = f"{self._base_url}/api/{method_name}"
        headers = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        try:
            # 发送post请求
            response = requests.post(url, json=request_data.model_dump(), headers=headers or None)
            # 检查响应状态码，如果不成功，则尝试解析错误信息并抛出异常
            if not response.ok:
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", response.text)
                except ValueError:
                    error_message = response.text
                raise requests.exceptions.HTTPError(f"HTTP error occurred: {response.status_code} - {error_message}", response=response)
            # 返回请求结果
            return response_model(**response.json())
        except requests.exceptions.RequestException as e:
            self._logger.error(f"An error occurred: {e}")
            raise
