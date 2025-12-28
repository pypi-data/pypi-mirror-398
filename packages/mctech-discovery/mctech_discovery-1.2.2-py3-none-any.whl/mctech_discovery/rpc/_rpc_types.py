from __future__ import absolute_import
from typing import Union, Optional, Mapping, Tuple, NamedTuple, Any, Literal, Iterable, AsyncIterable
from abc import ABC
from httpx import URL

RequestContent = Union[str, bytes, Iterable[bytes], AsyncIterable[bytes]]
RequestData = Mapping[str, Any]
JsonObject = Any

RpcResponseResult = Union[JsonObject, str, bytes]
RequestContentTypes = Union[JsonObject, RequestContent]

HttpMethod = Literal['get', 'post', 'put', 'delete', 'patch']
MixedMethod = Union[HttpMethod, Literal["ws"]]
ResponseTypes = Literal["json", "bytes", "text", "response"]
Seconds = float

CallMode = Literal["execute", "stream", "ws"]


class HttpRequestBody:
    content: Optional[RequestContent]
    json: Optional[Any]
    # body上的content_type比headers上的更优先
    content_type: Optional[str]

    def __init__(self, *,
                 content: Optional[RequestContent] = None,
                 json: Optional[JsonObject] = None,
                 content_type: Optional[str] = None):
        self.content = content
        self.json = json
        self.content_type = content_type

    def args(self) -> Tuple[Optional[str], RequestContentTypes]:
        if self.content is not None:
            return ("content", self.content)
        elif self.json is not None:
            return ("json", self.json)
        return (None, None)


MixedRequestBody = Union[HttpRequestBody, JsonObject, Mapping[str, Any], str, bytes]


class Invoker(ABC):
    path: str
    params: Optional[Mapping[str, Any]]
    query: Optional[Mapping[str, Any]]
    headers: Optional[Mapping[str, Any]]
    context: Optional[Mapping[str, Any]]

    def __init__(self, path: str, *,
                 params: Optional[Mapping[str, Any]] = None,
                 query: Optional[Mapping[str, Any]] = None,
                 headers: Optional[Mapping[str, Any]] = None,
                 context: Optional[Mapping[str, Any]] = None
                 ):
        '''
        path: api接口端点路径，可以包含':param'这样的参数格式
        params: 当传入的path对应的端点路径中包含参数时，params提供参数的替换值
        query: api接口端点路径的query参数
        headers: 需要传递的额外header头。
                 默认会设置'content-type'为'application/json'，如果需要别的类型可以在此替换
        context: 额外传递的上下文信息，最终会转换成通过header方式传递。
                 与headers参数不一样的是context里的值会把驼峰格式转换成'x-'开头的'-'分隔的小写字符格式。
                 例如tenantId会转换成 'x-tenant-id'，这个参数仅是为了兼容与目前node框架调用的服务
        '''
        self.path = path
        self.params = params
        self.query = query
        self.headers = headers
        self.context = context


class WebSocketInvoker(Invoker):
    pass


class RpcInvoker(Invoker):
    body: Optional[MixedRequestBody]
    response_type: Optional[ResponseTypes]
    retry: Optional[int]
    timeout: Optional[Seconds]

    def __init__(self, path: str, *,
                 response_type: Optional[ResponseTypes] = None,
                 params: Optional[Mapping[str, Any]] = None,
                 query: Optional[Mapping[str, Any]] = None,
                 body: Optional[Union[JsonObject, bytes, str]] = None,
                 headers: Optional[Mapping[str, Any]] = None,
                 retry: Optional[int] = None,
                 context: Optional[Mapping[str, Any]] = None,
                 timeout: Optional[Seconds] = None,
                 json: Optional[bool] = None
                 ):
        '''
        path: api接口端点路径，可以包含':param'这样的参数格式
        params: 当传入的path对应的端点路径中包含参数时，params提供参数的替换值
        query: api接口端点路径的query参数
        body: 传递给调用的api接口的body内容
        headers: 需要传递的额外header头。
                 默认会设置'content-type'为'application/json'，如果需要别的类型可以在此替换
        retry: 出错重试次数，默认值为0。目前并未使用
        context: 额外传递的上下文信息，最终会转换成通过header方式传递。
                 与headers参数不一样的是context里的值会把驼峰格式转换成'x-'开头的'-'分隔的小写字符格式。
                 例如tenantId会转换成 'x-tenant-id'，这个参数仅是为了兼容与目前node框架调用的服务
        timeout: 接口调用客户端超时时间，单位秒。超过设置的超时时间，调用端直接抛出超时异常
        '''
        super().__init__(path, params=params, query=query,
                         headers=headers, context=context)
        self.response_type = response_type
        self.body = body
        # 仅在execute方法内有效，调用返回的类型是否是json,如果为false则返回原始字符串文本
        self.json = True if json is None else json
        self.retry = 0 if retry is None else retry
        self.timeout = timeout


class PipeRpcInvoker(RpcInvoker):
    method: HttpMethod

    def __init__(self, path: str, method: HttpMethod, *,
                 params: Optional[Mapping[str, Any]] = None,
                 query: Optional[Mapping[str, Any]] = None,
                 body: Optional[MixedRequestBody] = None,
                 headers: Optional[Mapping[str, Any]] = None,
                 retry: Optional[int] = None,
                 context: Optional[Mapping[str, Any]] = None,
                 timeout: Optional[Seconds] = None):
        '''
        method: stream调用模式下使用的http请求方法
        path: api接口端点路径，可以包含':param'这样的参数格式
        params: 当传入的path对应的端点路径中包含参数时，params提供参数的替换值
        query: api接口端点路径的query参数
        body: 传递给调用的api接口的body内容
        headers: 需要传递的额外header头。
                 默认会设置'content-type'为'application/json'，如果需要别的类型可以在此替换
        retry: 出错重试次数，默认值为0。目前并未使用
        context: 额外传递的上下文信息，最终会转换成通过header方式传递。
                 与headers参数不一样的是context里的值会把驼峰格式转换成'x-'开头的'-'分隔的小写字符格式。
                 例如tenantId会转换成 'x-tenant-id'，这个参数仅是为了兼容与目前node框架调用的服务
        timeout: 接口调用客户端超时时间，单位秒。超过设置的超时时间，调用端直接抛出超时异常
        '''
        super().__init__(path, params=params, query=query, body=body,
                         headers=headers, retry=retry,
                         context=context, timeout=timeout)
        self.method = method


class RpcServiceInfo:
    reject_unauthorized: bool
    service_id: Optional[str]
    url: Optional[str]
    rpc_type: Optional[str]
    path: Optional[str]
    timeout: Optional[Seconds]

    def __init__(self, *,
                 reject_unauthorized: Optional[bool] = None,
                 service_id: Optional[str] = None,
                 url: Optional[str] = None,
                 rpc_type: Optional[str] = None,
                 path: Optional[str] = None,
                 timeout: Optional[Seconds] = None
                 ):
        '''
        reject_unauthorized: 使用'https'协议时，是否拒绝验证未通过的服务端证书。默认值为true
                             值为true时，表示强制一定要验证证书，且证书必须验证通过
                             值为false时，表示不会验证证书，任何证书都会被当作可信任的对待
        service_id:          需要调用的服务标识（serviceId与url不能同时为空）
        param url:           指定服务的绝对路径的前缀部分。
                             serviceId与url不能同时为空，优先于serviceId
        path:                服务的基准路径，不允许出现参数占位符。
                             设置了此路径时，所有调用该服务的方法都会在调用路径的基础上加上当前路径前缀
        timeout              rpc调用超时时间，默认值为1s，如果RpcInvoker上设置了，以RpcInvoker上的优先
        '''
        self.reject_unauthorized = True if reject_unauthorized is None else reject_unauthorized
        self.service_id = service_id
        self.url = url
        self.path = path
        self.rpc_type = rpc_type
        self.timeout = timeout


class EndPoint(NamedTuple):
    id: str
    host: str
    port: int
    vip_address: bool

    def to_url(self, **kwargs) -> URL:
        kwargs = {**kwargs, 'scheme': "http", 'host': self.host, 'port': self.port}
        return URL(**kwargs)


class RequestOptions(ABC):
    url: Union[URL, str]
    headers: Mapping[str, Any]
    verify: bool
    timeout: Optional[Seconds]

    def __init__(self, url: Union[URL, str], headers: Mapping[str, Any], verify: bool,
                 timeout: Optional[Seconds] = None):
        self.url = url
        self.headers = headers
        self.verify = verify
        self.timeout = timeout


class RpcRequestOptions(RequestOptions):
    method: Optional[HttpMethod]
    body: Optional[MixedRequestBody]
    response_type: ResponseTypes

    def __init__(self, url: Union[URL, str], headers: Mapping[str, Any], verify: bool,
                 method: HttpMethod, response_type: ResponseTypes,
                 body: Optional[MixedRequestBody] = None,
                 timeout: Optional[Seconds] = None):
        super().__init__(url, headers, verify, timeout)
        self.method = method
        self.body = body
        self.response_type = response_type


class WebSocketRequestOptions(RequestOptions):
    pass
