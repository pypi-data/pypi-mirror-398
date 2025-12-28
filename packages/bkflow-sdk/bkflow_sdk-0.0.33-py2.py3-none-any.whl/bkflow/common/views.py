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
import urllib

from django.conf import settings
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from bkflow.config.default import BK_TOKEN_EXPIRED_CODE


class SimpleGenericViewSet(GenericViewSet):
    """
    最基础的视图函数，不支持model, view_set 的 创建，查看，更新，删除方法，只支持用户自定义的action
    """

    renderer_classes = [JSONRenderer]
    EXEMPT_STATUS_CODES = {status.HTTP_204_NO_CONTENT}
    RESPONSE_WRAPPER = None

    def default_response_wrapper(self, data):
        return {"result": True, "data": data, "code": "0", "message": ""}

    def finalize_response(self, request, response, *args, **kwargs):

        if isinstance(response, Response):
            res_data = {
                "result": response.data.get("result"),
                "code": response.data.get("code"),
                "data": response.data.get("data"),
                "message": response.data.get("message"),
            }
            if response.data.get("count"):
                res_data["count"] = response.data.get("count")
            response.data = res_data
            if str(response.data.get("code")) == BK_TOKEN_EXPIRED_CODE:
                response.status_code = 401
                curl = urllib.parse.quote(request.build_absolute_uri())
                res_data["data"] = {"login_url": f"{getattr(settings,'BKPAAS_LOGIN_URL','')}?curl={curl}"}
        return super(SimpleGenericViewSet, self).finalize_response(request, response, *args, **kwargs)
