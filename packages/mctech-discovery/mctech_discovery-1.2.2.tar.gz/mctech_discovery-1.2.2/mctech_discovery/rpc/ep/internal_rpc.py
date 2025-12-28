from __future__ import absolute_import
import asyncio
import re
from functools import partial
from typing import Optional, Dict, Mapping, Tuple, Any, Iterable, AsyncIterable
from httpx import URL, Request, Response

from .httpx_clients import clients, async_clients
from ..web_error import WebError
from ..request_context import RequestContext
from ...discovery import get_discovery

from .._rpc_types import Invoker, RpcInvoker, EndPoint, HttpRequestBody, RequestOptions, \
    WebSocketRequestOptions, RpcRequestOptions, \
    ResponseTypes, RpcResponseResult

_loop = asyncio.new_event_loop()

_CONTENT_TYPE_VALUE = 'application/json; charset=UTF-8'


def _create_websocket_options(context: RequestContext, ep: EndPoint) -> Tuple[str, Mapping[str, Any]]:
    option = _create_request_options(context, ep, None)

    address = URL(option.url)
    if address.scheme == 'https':
        address = URL(context.url, scheme='wss')
    else:
        address = URL(context.url, scheme='ws')
    headers = option.headers
    import ssl
    ws_options = {
        'header': headers,
        'timeout': option.timeout,
        'sslopt': {"cert_reqs": ssl.CERT_NONE} if option.verify else None,
        'host': headers.get('Host')
    }
    return (str(address), ws_options)


def _create_httpx_request(context: RequestContext, ep: EndPoint, url: Optional[str]) -> Tuple[bool, Request]:
    option = _create_request_options(context, ep, url)
    assert isinstance(option, RpcRequestOptions)

    kwargs = {
        'url': option.url,
        'method': option.method,
        'headers': dict(option.headers),
        'timeout': clients.create_timeout(option.timeout)
    }
    headers: Dict[str, Any] = kwargs['headers']
    if option.body is not None:
        body = option.body
        content_type = headers.get('Content-Type') or ''
        if isinstance(body, HttpRequestBody):
            name, value = body.args()
            if name:
                kwargs[name] = value
            if body.content_type:
                # body上的content_type优先
                headers['Content-Type'] = body.content_type
        elif isinstance(body, (str, bytes)):
            kwargs['content'] = body
        elif content_type.lower().find('json'):
            kwargs['json'] = body
        else:
            raise RuntimeError('不支持的数据类型: %s' % type(body).__name__)
        if 'Content-Type' not in headers:
            # content-type 不存在，设置默认值
            headers['Content-Type'] = _CONTENT_TYPE_VALUE

    return (option.verify, clients.build_request(**kwargs))


def _create_request_options(context: RequestContext, ep: EndPoint, url: Optional[str]) -> RequestOptions:
    target_url = context.url
    if not ep.vip_address:
        # URL构造函数支持 URL参数类型
        target_url = URL(context.url, scheme="http", host=ep.host, port=ep.port)

    kwargs = {
        'headers': _normalize_headers(context.headers),
        'url': url or target_url,
        'verify': context.service.reject_unauthorized,
        'timeout': context.timeout
    }

    if context.method == 'ws':
        return WebSocketRequestOptions(**kwargs)

    invoker = context.invoker
    assert isinstance(invoker, RpcInvoker)

    kwargs['method'] = context.method
    kwargs['body'] = invoker.body
    kwargs['response_type'] = invoker.response_type or ('json' if invoker.json else 'text')
    reqOption = RpcRequestOptions(**kwargs)
    context.process_request_option(reqOption)
    return reqOption


__HEADER_PATTERN = re.compile('(-|^)[a-z]', re.IGNORECASE)


def _normalize_headers(headers: Mapping[str, Any]) -> Mapping[str, Any]:
    new_headers = {}
    if not headers:
        return new_headers

    for key, value in headers.items():
        new_key = __HEADER_PATTERN.sub(lambda m: m.group(0).upper(), key)
        new_headers[new_key] = value
    return new_headers


def resolve_error(context: RequestContext, res: Response):
    timeout = context.timeout if context.timeout else 0
    service = context.service

    message = "%s --> %s --> [timeout:%ds, cost: %fs] [%s] [%s] %s" % (
        res.reason_phrase, res.text, timeout, res.elapsed.total_seconds(),  # noqa
        service.service_id, context.method, context.url)
    err = WebError(message, status=res.status_code)
    context.resolve_error(res, err)
    raise err


async def _walk_using_urllib_async(context: RequestContext, ep: EndPoint, stream: bool, url: Optional[str] = None) -> Response:  # noqa
    verify, req = _create_httpx_request(context, ep, url)
    res = await async_clients.get_client(verify).send(req, stream=stream)
    return res


def _walk_using_urllib(context: RequestContext, ep: EndPoint, stream: bool, url: Optional[str] = None) -> Response:  # noqa
    verify, req = _create_httpx_request(context, ep, url)
    res = clients.get_client(verify).send(req, stream=stream)
    return res


async def _do_request_async(context: RequestContext, ep: EndPoint, stream: bool) -> Response:
    if not ep.vip_address:
        url = ep.to_url(path=context.url.path, params=context.url.params)
        res = await _walk_using_urllib_async(context, ep, stream, str(url))
    else:
        res = await get_discovery().client.walk_nodes(
            app_name=context.service.service_id,
            service=context.url.path,
            walker=partial(_walk_using_urllib_async, context, ep, stream)
        )

    if res.is_error:
        try:
            if res.stream and not res.is_stream_consumed:
                # stream方式且未读取过，先读取到content里
                await res.aread()
            resolve_error(context, res)
        finally:
            # 处理完异常后可关闭
            await res.aclose()
    elif not res.stream:
        # 非stream模式，已经读取完所有内容，可关闭
        res.aclose()
    return res


def _do_request(context: RequestContext, ep: EndPoint, stream: bool) -> Response:
    if ep:
        url = ep.to_url(path=context.url.path, params=context.url.params)
        res = _walk_using_urllib(context, ep, stream, str(url))
    else:
        r = get_discovery().client.walk_nodes(
            app_name=context.service.service_id,
            service=context.path_and_query,
            walker=partial(_walk_using_urllib, context, ep, stream)
        )
        res = _loop.run_until_complete(r)

    if res.is_error:
        try:
            if res.stream and not res.is_stream_consumed:
                # stream方式且未读取过，先读取到content里
                res.read()
            resolve_error(context, res)
        finally:
            # 处理完异常后可关闭
            res.close()
    elif not res.stream:
        # 非stream模式，已经读取完所有内容，可关闭
        res.close()
    return res

#####################################################################################


def _convert_result(res: Response, invoker: Invoker) -> RpcResponseResult:
    assert isinstance(invoker, RpcInvoker)
    response_type: ResponseTypes = 'json' if invoker.json else 'text'
    if invoker.response_type:
        response_type = invoker.response_type

    content_type = res.headers.get('content-type') or ''
    if response_type == 'json':
        if content_type.find('json') >= 0:
            return res.json()
        else:
            return res.text
    elif response_type == 'text':
        return res.text
    elif response_type == 'bytes':
        return res.read()
    return res


def execute(context: RequestContext, ep: EndPoint) -> RpcResponseResult:
    res = _do_request(context, ep, False)
    return _convert_result(res, context.invoker)


def stream(context: RequestContext, ep: EndPoint) -> Iterable[bytes]:
    res = _do_request(context, ep, True)
    return res.iter_bytes()


def ws(context: RequestContext, ep: EndPoint):
    address, option = _create_websocket_options(context, ep)
    from websocket import create_connection
    conn = create_connection(url=address, **option)

    return conn

###########################################################################################


async def execute_async(context: RequestContext, ep: EndPoint) -> RpcResponseResult:
    res = await _do_request_async(context, ep, False)
    return _convert_result(res, context.invoker)


async def stream_async(context: RequestContext, ep: EndPoint) -> AsyncIterable[bytes]:
    res = await _do_request_async(context, ep, True)
    return res.aiter_bytes()


async def ws_async(context: RequestContext, ep: EndPoint):
    return ws(context, ep)
