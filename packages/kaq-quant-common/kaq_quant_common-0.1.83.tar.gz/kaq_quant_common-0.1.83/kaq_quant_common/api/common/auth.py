import os
from typing import Any, Optional, Tuple

from kaq_quant_common.utils import yml_utils

# 统一的简单鉴权：基于一个共享的 token
# - 来源优先级：环境变量 KAQ_API_TOKEN > 配置文件 kaq.api_token
# - 如果未配置 token，则认为鉴权关闭（通过）


def _get_expected_token(pkg_name: Optional[str] = None) -> Optional[str]:
    # 环境变量优先
    token = os.getenv("KAQ_API_TOKEN")
    if token:
        return token.strip()
    # 配置文件兜底
    try:
        token_cfg = yml_utils.get(pkg_name or "kaq_quant_common", "api_token")
        if isinstance(token_cfg, str) and token_cfg.strip():
            return token_cfg.strip()
    except Exception as e:
        # 配置读取失败则视为未配置
        pass
    return None


def _extract_token_from_authorization(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    # 支持 Bearer/Token 两种前缀
    val = auth_header.strip()
    lower = val.lower()
    if lower.startswith("bearer "):
        return val[7:].strip()
    if lower.startswith("token "):
        return val[6:].strip()
    # 若为纯 token 也接受
    return val


def _extract_token_from_headers(headers: Any) -> Optional[str]:
    # 兼容 Flask/Werkzeug 和 websockets.Headers
    try:
        # Flask/requests：大小写不敏感
        auth = headers.get("Authorization") if hasattr(headers, "get") else None
        if not auth and hasattr(headers, "get"):
            auth = headers.get("authorization")
        token = _extract_token_from_authorization(auth)
        if token:
            return token
        # 备用头
        x_token = headers.get("X-API-Token") if hasattr(headers, "get") else None
        if not x_token and hasattr(headers, "get"):
            x_token = headers.get("x-api-token")
        return x_token.strip() if isinstance(x_token, str) and x_token.strip() else None
    except Exception:
        return None


def _extract_token_from_path_query(path: Optional[str]) -> Optional[str]:
    # 解析 ?token=xxx 简单查询参数
    if not path or "?" not in path:
        return None
    try:
        query = path.split("?", 1)[1]
        for pair in query.split("&"):
            if not pair:
                continue
            k, _, v = pair.partition("=")
            if k.lower() == "token" and v:
                return v
    except Exception:
        pass
    return None


# ----------------- 对外校验方法 -----------------


def verify_http_request(flask_request: Any, pkg_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """校验 HTTP 请求头中的 token。
    返回 (是否通过, 错误信息)。未配置 token 时默认放行。
    """
    expected = _get_expected_token(pkg_name)
    if not expected:
        return True, None
    # 从 Header 提取
    token = _extract_token_from_headers(getattr(flask_request, "headers", None))
    if token and token == expected:
        return True, None
    return False, "Unauthorized"


def verify_ws_handshake(path: Optional[str], headers: Any, pkg_name: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """校验 WebSocket 握手阶段的路径与请求头。
    支持从 Header 与 ?token=xx 解析。未配置 token 时默认放行。
    """
    expected = _get_expected_token(pkg_name)
    if not expected:
        return True, None
    # Header 优先
    token = _extract_token_from_headers(headers)
    if not token:
        # 再从路径查询参数解析
        token = _extract_token_from_path_query(path)
    if token and token == expected:
        return True, None
    return False, "Unauthorized"


# ----------------- 客户端复用：获取默认 token -----------------


def get_auth_token(pkg_name: Optional[str] = None) -> Optional[str]:
    """供客户端复用的获取默认 token 的方法。
    与服务器端校验使用相同的来源规则。
    """
    return _get_expected_token(pkg_name)
