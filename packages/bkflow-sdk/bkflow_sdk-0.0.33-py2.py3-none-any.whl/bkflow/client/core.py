"""
Tencent is pleased to support the open source community by making 蓝鲸智云 - PaaS平台 (BlueKing - PaaS System) available.
Copyright (C) 2022 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""

import json
import logging

import requests
from django.conf import settings

from bkflow.client.apis.bkflow import CollectionsBKFlow
from bkflow.common.exceptions import APIException
from bkflow.common.loader import call_config_function

logger = logging.getLogger(__name__)

__all__ = [
    "get_client_by_request",
    "get_client_by_user",
]

HEADER_BK_AUTHORIZATION = "X-Bkapi-Authorization"
DEFAULT_STAGE = getattr(settings, "BK_APIGW_STAGE_NAME", "prod")
AVAILABLE_COLLECTIONS = {
    "bkflow": CollectionsBKFlow,
}


class BaseAPIClient:
    """Base client class for api"""

    def __init__(
        self,
        app_code=None,
        app_secret=None,
        headers=None,
        common_args=None,
        stage="prod",
        timeout=None,
        bk_apigw_ver="v3",
    ):
        """
        :param str app_code: App code to use
        :param str app_secret: App secret to use
        :param dict headers: headers be sent to api
        :param dict common_args: Args that will apply to every request
        :param str stage: Stage for api gateway
        :param int timeout: timeout for request
        """

        self.app_code = app_code or settings.APP_CODE
        self.app_secret = app_secret or settings.SECRET_KEY
        self.headers = headers or {}
        self.common_args = common_args or {}
        self.stage = stage
        self.bk_apigw_ver = bk_apigw_ver
        self.timeout = timeout
        self._cached_collections = {}
        self._log_warning()
        self.available_collections = AVAILABLE_COLLECTIONS

    def _log_warning(self):
        _, _, api_name = __package__.partition(".")
        logger.warning(
            "%s is no longer maintained, recommend to use bkapi.%s as a replacement",
            __package__,
            api_name,
        )

    def merge_params_data_with_common_args(self, method, params, data):
        """Add common args to params every request"""
        common_args = dict(app_code=self.app_code, **self.common_args)
        if method in ["GET", "HEAD"]:
            _params = common_args.copy()
            _params.update(params or {})
            params = _params
        elif method in ["POST", "PUT", "PATCH", "DELETE"]:
            _data = common_args.copy()
            _data.update(data or {})
            data = json.dumps(_data)
        return params, data

    def __getattr__(self, key):
        if key not in self.available_collections:
            return getattr(super(), key)

        if key not in self._cached_collections:
            collection = self.available_collections[key]
            self._cached_collections[key] = collection(self)
        return self._cached_collections[key]

    def request(self, method, url, params=None, data=None, path_params=None, **kwargs):
        # Merge custom headers with instance headers
        headers = self.headers.copy()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        return requests.request(method, url, headers=headers, params=params, json=data, timeout=self.timeout, **kwargs)


class RedirectAPIClient(BaseAPIClient):
    """用于根据View的request配置重定向请求."""

    def redirect(self, request):
        pass


class RequestAPIClient(BaseAPIClient):
    def request(self, *args, **kwargs):
        # update headers
        headers = kwargs.pop("headers", {})
        headers.update(self.headers)
        method = kwargs.get("method", "GET")
        if method.upper() in ["POST", "PUT", "PATCH", "DELETE"]:
            headers["Content-Type"] = "application/json"
        return self._request(headers=headers, *args, **kwargs)

    def _request(self, method, url, params=None, data=None, **kwargs):
        """Send request direct"""
        params, data = self.merge_params_data_with_common_args(method, params, data)
        logger.info("Calling %s %s with params=%s, data=%s", method, url, params, data)
        return requests.request(method, url, params=params, json=data, timeout=self.timeout, **kwargs)


def get_client_by_request(request, stage=DEFAULT_STAGE, common_args=None, headers=None):
    """
    根据当前请求返回一个client
    :param request: 一个django request实例
    :param stage: 请求环境，默认为prod
    :param common_args: 公共请求参数
    :param headers: 头部信息
    :returns: 一个初始化好的APIClint对象
    """
    headers = headers or {}

    is_authenticated = request.user.is_authenticated
    if callable(is_authenticated):
        is_authenticated = is_authenticated()
    if is_authenticated:
        headers.update(
            {
                HEADER_BK_AUTHORIZATION: json.dumps(
                    {
                        "bk_ticket": request.COOKIES.get("bk_ticket", ""),
                        "bk_app_code": settings.APP_CODE,
                        "bk_app_secret": settings.SECRET_KEY,
                    }
                )
            }
        )
    else:
        raise APIException("用户未通过验证")

    return RedirectAPIClient(
        app_code=settings.APP_CODE,
        app_secret=settings.SECRET_KEY,
        headers=headers,
        common_args=common_args,
        stage=stage,
    )


def get_client_by_user(user, stage=DEFAULT_STAGE, common_args=None, headers=None):
    """
    根据user实例返回一个client
    :param user: 用户
    :param stage: 请求环境，默认为prod
    :param common_args: 公共请求参数
    :param common_args: 公共请求参数
    :param headers: 头部信息
    :returns: 一个初始化好的APIClint对象
    """
    headers = headers or {}
    common_args = common_args or {}
    if hasattr(user, "username"):
        user = user.username
    try:
        from bkoauth import get_access_token_by_user

        access_token = get_access_token_by_user(user)
        headers.update(
            {
                HEADER_BK_AUTHORIZATION: json.dumps({"access_token": access_token.access_token}),
            }
        )
    except Exception as e:
        logger.warning("get_access_token_by_user error %s, using header authorization", str(e))
        headers.update(
            {
                HEADER_BK_AUTHORIZATION: json.dumps(
                    {"bk_username": user, "bk_app_code": settings.APP_CODE, "bk_app_secret": settings.SECRET_KEY}
                )
            }
        )

    return RedirectAPIClient(
        app_code=settings.APP_CODE,
        app_secret=settings.SECRET_KEY,
        headers=headers,
        common_args=common_args,
        stage=stage,
    )


def get_headers_by_generator(request):
    """
    通过配置的 generator 函数获取 headers

    优先级：
    1. 如果配置了 BKFLOW_SDK_APIGW_HEADERS_GENERATOR，则调用该函数获取
    2. 否则返回 None，使用默认的 headers 生成逻辑

    :param request: 一个django request实例
    :return: headers 字典，如果 generator 未配置或返回 None，则返回 None
    """
    generator_path = getattr(settings, "BKFLOW_SDK_APIGW_HEADERS_GENERATOR", None)

    if generator_path:
        headers = call_config_function(
            generator_path,
            "BKFLOW_SDK_APIGW_HEADERS_GENERATOR",
            error_message_prefix="调用 BKFLOW_SDK_APIGW_HEADERS_GENERATOR",
            request=request,
        )
        # 验证返回值为字典类型
        if headers is not None and isinstance(headers, dict):
            return headers

    return None


def get_redirect_client_with_auth(request, **kwargs):
    """
    根据当前请求返回一个带有认证信息的client
    :param request: 一个django request实例
    :returns: 一个初始化好的APIClint对象
    """
    # 尝试通过 generator 函数获取 headers
    generator_headers = get_headers_by_generator(request)

    if generator_headers is not None:
        # 如果 generator 返回了 headers，直接使用
        headers = generator_headers
    else:
        # 否则使用默认的 headers 生成逻辑
        bk_ticket = request.COOKIES.get("bk_ticket", None)
        bk_token = request.COOKIES.get("bk_token", None)
        if not bk_ticket and not bk_token:
            raise APIException("用户未通过验证")
        headers = {
            HEADER_BK_AUTHORIZATION: json.dumps(
                {
                    "bk_app_code": settings.APP_CODE,
                    "bk_app_secret": settings.SECRET_KEY,
                    "bk_ticket": bk_ticket,
                    "bk_token": bk_token,
                }
            )
        }

    return RedirectAPIClient(
        app_code=settings.APP_CODE, app_secret=settings.SECRET_KEY, headers=headers, common_args={}, stage=DEFAULT_STAGE
    )


def get_redirect_client(request):
    """
    根据当前请求返回一个client
    :param request: 一个django request实例
    :returns: 一个初始化好的APIClint对象
    """
    headers = {
        HEADER_BK_AUTHORIZATION: json.dumps(
            {
                "bk_app_code": settings.APP_CODE,
                "bk_app_secret": settings.SECRET_KEY,
            }
        )
    }

    return RedirectAPIClient(
        app_code=settings.APP_CODE, app_secret=settings.SECRET_KEY, headers=headers, common_args={}, stage=DEFAULT_STAGE
    )
