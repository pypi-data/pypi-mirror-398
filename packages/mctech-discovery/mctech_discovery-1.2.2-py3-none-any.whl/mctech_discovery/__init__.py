import logging

from .discovery import get_discovery
from .rpc import get_rpc_client, get_service_info, RpcClient, WebError
from .rpc._rpc_types import RpcInvoker, PipeRpcInvoker, WebSocketInvoker, RpcServiceInfo

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)


__all__ = [
    "get_discovery",
    "get_rpc_client",
    "get_service_info",
    "RpcClient",
    "WebError",
    "RpcInvoker",
    "PipeRpcInvoker",
    "WebSocketInvoker",
    "RpcServiceInfo"
]
