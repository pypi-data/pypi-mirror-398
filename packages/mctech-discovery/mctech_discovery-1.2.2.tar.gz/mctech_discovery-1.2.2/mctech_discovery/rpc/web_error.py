from __future__ import absolute_import
from typing import Mapping, List, Optional
import json


class WebError(RuntimeError):
    code: Optional[str]
    desc: Optional[str]
    headers: Mapping[str, str]
    status: int

    def __init__(self,
                 message: str,
                 code: Optional[str] = None,
                 desc: Optional[str] = None,
                 headers: Optional[Mapping[str, str]] = None,
                 status: int = 400):
        super().__init__(message)
        self.code = code
        self.desc = desc
        self.headers = headers or {}
        self.status = status
        self.details: List[str] = []

    def __dir__(self):
        # 返回自定义的属性和方法列表
        lst = [k for k in super().__dir__()]
        lst.extend(['code', 'desc', 'headers', 'status', 'details'])
        return lst

    def __str__(self):
        obj = dict(self.__dict__)
        obj['message'] = super().__str__()
        return json.dumps(obj, ensure_ascii=False)
