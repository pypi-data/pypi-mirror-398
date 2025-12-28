from __future__ import absolute_import

import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Mapping, Optional
from httpx import URL, Response
from urllib.parse import urljoin

from mctech_core.context import get_async_context

from .web_error import WebError

from ._rpc_types import Invoker, RpcInvoker, RpcServiceInfo, Seconds, RpcRequestOptions, MixedMethod

PARAM_PARTERN = re.compile(':(\\w+)')
HEADER_PARTTERN = re.compile('[A-Z]')


class RequestContext(ABC):
    method: MixedMethod
    invoker: Invoker
    service: RpcServiceInfo
    app_name: Optional[str]
    headers: Mapping[str, Any]
    url: URL

    def __init__(self, method: MixedMethod, invoker: Invoker, service: RpcServiceInfo,
                 app_name: Optional[str] = None,
                 product_line: Optional[str] = None):
        self.method = method
        self.invoker = invoker
        self.service = service
        self.app_name = app_name
        self.product_line = product_line

        path = invoker.path
        query = invoker.query if invoker.query is not None else {}
        params = invoker.params if invoker.params is not None else {}

        headers = dict(invoker.headers) if invoker.headers else {}
        if invoker.context:
            self._add_headers(headers, invoker.context)
        self.headers = headers

        base_url, path_and_query = self._get_path_and_query(path)
        url = URL(base_url).join(path_and_query)
        url = url.copy_merge_params(query)

        def _replacement(matched, params):
            var_name: str = matched.group(1)
            # 获取传入参数
            value = params.get(var_name)
            if (value is None):
                error_msg = "不存在的属性：'%s'" % var_name
                raise RuntimeError(error_msg)
            return str(value)

        new_path = PARAM_PARTERN.sub(
            lambda matched: _replacement(matched, params), url.path)
        url = url.copy_with(path=new_path)
        self.url = url

    @property
    def timeout(self) -> Optional[Seconds]:
        if isinstance(self.invoker, RpcInvoker) and self.invoker.timeout:
            return self.invoker.timeout
        return self.service.timeout

    def process_request_option(self, option: RpcRequestOptions):
        # 什么也不做
        pass

    @abstractmethod
    def resolve_error(self, res: Response, err: WebError):
        pass

    @abstractmethod
    def _get_path_and_query(self, path: str) -> Tuple[str, str]:
        '''
        :return [baseUrl: str, path_and_query: str]
        '''
        pass

    @abstractmethod
    def _add_headers(self, headers: Dict[str, Any], context: Mapping[str, Any]):
        pass

    def _to_header_name(self, name: str, prefix: str):
        key = HEADER_PARTTERN.sub(
            lambda matched: '-' + matched.group(0).upper(), name)

        # 补充'x-'前缀
        if key.startswith('-'):
            return prefix + key
        return prefix + '-' + key


class InternalRequestContext(RequestContext):
    def _get_path_and_query(self, path: str):
        base_url = self.service.url
        if not base_url:
            base_url = "http://%s" % self.service.service_id

        path_prefix = self.service.path if self.service.path else '/'
        path_and_query = urljoin(path_prefix, path)
        return (base_url, path_and_query)

    def _add_headers(self, headers: Dict[str, Any], context: Mapping[str, Any]):
        asynctx = get_async_context()
        principal: Mapping[str, Any] = {}
        extras: Mapping[str, Any] = {}
        webContext = asynctx.web_context
        if webContext:
            # 当前调用是在处理web请求的时候发生的
            if webContext.principal:
                # website身份认证信息
                principal['id'] = webContext.principal.get('id')
                if not principal.get('userId') and principal.get('id'):
                    principal['userId'] = principal['id']

                principal['tenantId'] = webContext.principal['tenantId']
                principal['tenantCode'] = webContext.principal['tenantCode']

                # TODO: 应该删除掉
                principal['orgId'] = webContext.principal['orgId']
                principal['applicationId'] = webContext.principal['applicationId']  # noqa
            extras = webContext.extras

        if not principal.get('tenantId'):
            # 当前调用是在消息队列或定时任务等其它非web请求中调用的
            # 消息队列处理器中中没有webContext对象
            principal['tenantId'] = asynctx.tenant_id

        mergedCtx = {**principal, **extras}
        # 用户调用api时显示设置的信息
        if context:
            mergedCtx.update(context)

        for name, value in mergedCtx.items():
            if value is None:
                continue
            key = self._to_header_name(name, 'x')
            headers[key] = str(value)

        if self.app_name:
            headers['i-rpc-client'] = self.app_name

        tracing = asynctx.tracing
        if not tracing:
            return

        # 用于调用链跟踪的信息
        for name, value in asynctx.tracing.items():
            headers[name] = value

    def resolve_error(self, res: Response, err: WebError):
        content_type = res.headers.get('content-type') or ''
        err.code = 'HTTP_CLIENT_ERROR' if res.status_code < 500 else 'HTTP_SERVER_ERROR'
        err.desc = '调用服务发生错误'
        err.status = res.status_code

        if content_type.find('json') >= 0:
            try:
                data = res.json()
            except Exception:
                # 什么也不做
                data: Mapping[str, Any] = {
                    'code': 'json_format_error',
                    'desc': res.text
                }
            # 默认json格式
            err.code = data.get("code")
            err.desc = data.get("desc")
            err.details = data.get("details") or []
        else:
            err.code = 'HTTP_CLIENT_ERROR' if res.status_code < 500 else 'HTTP_SERVER_ERROR'
            err.desc = res.text
