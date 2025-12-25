from typing import Self
from uuid import uuid4

import urllib.parse
import httpx

from ._consts import JF_BASE_URL
from ._consts import JF_ACCESS_TOKEN
from ._consts import HK_AUTHORIZATION
from ._consts import HK_REQUEST_ID
from ._config import CurliConfig
from ._decorators import deprecated
from ._helpers import RequestWrapper
from ._helpers import ResponseWrapper
from ._helpers import ErrorWrapper
from ._store import Store
from ._utils import normalize_header

from ..errors import map_httpx_exception


class Curli:

    def __init__(self, invoker, session_store: Store, account_store: Store, config: CurliConfig|None = None):
        self._invoker = invoker
        self._session = session_store
        self._account = account_store
        self._config = config or CurliConfig()

    @property
    def config(self):
        return self._config

    @property
    def invoker(self):
        return self._invoker

    @invoker.setter
    def invoker(self, value):
        self._invoker = value

    @deprecated
    def globals(self, **kwargs) -> Self:
        return self.default(**kwargs)

    def default(self, **kwargs) -> Self:
        self._session.default(**kwargs)
        return self

    def as_account(self, profile = None, **kwargs) -> Self:
        if profile is not None:
            self._account.profile = profile
        self._account.update(**kwargs)
        return self

    def in_session(self, profile = None, **kwargs) -> Self:
        if profile is not None:
            self._session.profile = profile

        kwargs = dict(kwargs)
        if JF_BASE_URL in kwargs:
            if kwargs[JF_BASE_URL] is not None:
                self._session[JF_BASE_URL] = kwargs[JF_BASE_URL]
            del kwargs[JF_BASE_URL]
        self._session.update(**kwargs)

        return self

    def _build_params(self, url, *args, headers = None, **kwargs):
        base_url = kwargs.get(JF_BASE_URL, self._session[JF_BASE_URL])
        if not url.startswith('http') and base_url:
            url = urllib.parse.urljoin(base_url + '/', url.lstrip('/'))

        if not isinstance(headers, dict):
            headers = {}

        # normalize request headers and apply default header values
        headers = normalize_header(headers, HK_REQUEST_ID)

        session_headers = self._session['headers']
        if isinstance(session_headers, dict):
            headers = {**session_headers, **headers}

        access_token = kwargs.get(JF_ACCESS_TOKEN, self._account[JF_ACCESS_TOKEN])
        if access_token and isinstance(access_token, str):
            headers = {HK_AUTHORIZATION: f"Bearer {access_token}", **headers}
        if JF_ACCESS_TOKEN in kwargs:
            del kwargs[JF_ACCESS_TOKEN]

        headers = {HK_REQUEST_ID: str(uuid4()), **headers}

        other_kwargs = { key: value for key, value in kwargs.items() if key in ("timeout")}

        return (url, args, dict(kwargs, headers=headers), other_kwargs)

    def _wrap_response(self, response, **others):
        return ResponseWrapper(response, session_store=self._session, account_store=self._account, **others)

    def _wrap_request(self, request, **others):
        return RequestWrapper(request, session_store=self._session, account_store=self._account, **others)

    def _wrap_error(self, error, **others):
        return ErrorWrapper(error)

    #--------------------------------------------------------------------------

    class PrepareObject:
        def __init__(self, parent):
            self._parent = parent

        def request(self, method, url, *args, **kwargs):
            return self._parent.pre_request(method=method, url=url, *args, **kwargs)

        def get(self, url, *args, **kwargs):
            return self.request("GET", url, *args, **kwargs)

        def head(self, url, *args, **kwargs):
            return self.request("HEAD", url, *args, **kwargs)

        def options(self, url, *args, **kwargs):
            return self.request("OPTIONS", url, *args, **kwargs)

        def post(self, url, *args, **kwargs):
            return self.request("POST", url, *args, **kwargs)

        def put(self, url, *args, **kwargs):
            return self.request("PUT", url, *args, **kwargs)

        def patch(self, url, *args, **kwargs):
            return self.request("PATCH", url, *args, **kwargs)

        def delete(self, url, *args, **kwargs):
            return self.request("DELETE", url, *args, **kwargs)

    @property
    def prepare(self):
        return self.PrepareObject(self)

    def pre_request(self, method, url, *args, **kwargs):
        url, args, kwargs, others = self._build_params(url, *args, **kwargs)
        return self._wrap_request(httpx.Request(method=method, url=url, *args, **kwargs), **others)

    def pre_get(self, url, *args, **kwargs):
        return self.pre_request("GET", url, *args, **kwargs)

    def pre_head(self, url, *args, **kwargs):
        return self.pre_request("HEAD", url, *args, **kwargs)

    def pre_options(self, url, *args, **kwargs):
        return self.pre_request("OPTIONS", url, *args, **kwargs)

    def pre_post(self, url, *args, **kwargs):
        return self.pre_request("POST", url, *args, **kwargs)

    def pre_put(self, url, *args, **kwargs):
        return self.pre_request("PUT", url, *args, **kwargs)

    def pre_patch(self, url, *args, **kwargs):
        return self.pre_request("PATCH", url, *args, **kwargs)

    def pre_delete(self, url, *args, **kwargs):
        return self.pre_request("DELETE", url, *args, **kwargs)

    #--------------------------------------------------------------------------

    def request(self, method, url, *args, **kwargs):
        url, args, kwargs, others = self._build_params(url, *args, **kwargs)
        try:
            return self._wrap_response(self._invoker.request(method, url, *args, **kwargs), **others)
        except httpx.RequestError as exc:
            error = map_httpx_exception(exc, **others)
            if callable(self._config.error_presenter):
                if self._config.error_presenter(error):
                    return self._wrap_error(error, **others)
            raise error from exc

    def get(self, url, *args, **kwargs):
        return self.request("GET", url, *args, **kwargs)

    def head(self, url, *args, **kwargs):
        return self.request("HEAD", url, *args, **kwargs)

    def options(self, url, *args, **kwargs):
        return self.request("OPTIONS", url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self.request("POST", url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        return self.request("PUT", url, *args, **kwargs)

    def patch(self, url, *args, **kwargs):
        return self.request("PATCH", url, *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        return self.request("DELETE", url, *args, **kwargs)
