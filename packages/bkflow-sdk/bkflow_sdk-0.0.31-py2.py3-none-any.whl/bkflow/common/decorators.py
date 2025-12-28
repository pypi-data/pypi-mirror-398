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
from functools import wraps

from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.request import Request

from bkflow.common.exceptions import ValidationError
from bkflow.common.validator import custom_params_valid
from bkflow.config.default import REQUEST_TOKEN_HEADER_KEY


def token_inject(view_func):
    """
    token注入
    :param view_func: 被装饰的view函数
    """

    def wrapper(*args, **kwargs):
        request = args[1]
        if not hasattr(request, "token"):
            token = request.META.get(REQUEST_TOKEN_HEADER_KEY, "")

            if not token:
                raise ValidationError(
                    _("当前接口需要token，请在请求头中添加${REQUEST_TOKEN_HEADER_KEY}").format(
                        REQUEST_TOKEN_HEADER_KEY=REQUEST_TOKEN_HEADER_KEY
                    )
                )

            setattr(request, "token", token)

        return view_func(*args, **kwargs)

    return wraps(view_func)(wrapper)


def params_valid(serializer: serializers.Serializer, add_params: bool = True):
    """参数校验装饰器

    :param serializer: serializer类
    :param add_params: 是否将校验后的参数添加到request.cleaned_params中
    :return: 参数校验装饰器
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # 获得Django的request对象
            _request = kwargs.get("request")

            if not _request:
                for arg in args:
                    if isinstance(arg, (Request, WSGIRequest)):
                        _request = arg
                        break

            if not _request:
                raise ValidationError(_("该装饰器只允许用于Django的View函数(包括普通View函数和Class-base的View函数)"))

            # 校验request中的参数
            params = {}
            if _request.method in ["GET"]:
                if isinstance(_request, Request):
                    params = _request.query_params
                else:
                    params = _request.GET
            elif _request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                if isinstance(_request, Request):
                    params = _request.data
                else:
                    params = _request.json()
            else:
                if isinstance(_request, Request):
                    params = _request.data
                else:
                    params = _request.POST

            cleaned_params = custom_params_valid(serializer=serializer, params=params)
            _request.cleaned_params = cleaned_params

            # 执行实际的View逻辑
            params_add = False
            try:
                # 语法糖，使用这个decorator的话可直接从view中获得参数的字典
                if "params" not in kwargs and add_params:
                    kwargs["params"] = cleaned_params
                    params_add = True
            except TypeError:
                if params_add:
                    del kwargs["params"]
            resp = view_func(*args, **kwargs)
            return resp

        return wrapper

    return decorator
