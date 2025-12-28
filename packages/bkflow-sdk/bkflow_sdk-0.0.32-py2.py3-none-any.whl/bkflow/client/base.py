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
import logging

from bkflow.common.exceptions import APIException
from bkflow.config.default import API_TOKEN_HEADER_KEY
from bkflow.interface.utils import get_space_id

logger = logging.getLogger(__name__)


def render_string(tmpl, context):
    return tmpl.format(**context)


class RequestAPI:
    """Single request api"""

    HTTP_STATUS_OK = 200

    def __init__(self, client, method, host=None, path=None, description="", token_required=False):
        self.host = host
        self.path = path
        self.client = client
        self.method = method
        self.token_required = token_required

    def __call__(self, *args, path_params=None, headers=None, **kwargs):
        try:
            return self._call(*args, path_params=path_params, headers=headers, **kwargs)
        except APIException as e:
            # Combine log message
            log_message = [
                e.error_message,
            ]
            log_message.append("url=%s" % e.url)
            if e.resp:
                log_message.append("content=%s" % e.resp.text)

            logger.exception("\n".join(log_message))

            # Try return error message from remote service
            if e.resp is not None:
                try:
                    return e.resp.json()
                except Exception:
                    pass
            return {"result": False, "message": e.error_message, "data": None}

    def _call(self, *args, path_params=None, headers=None, space_id=None, **kwargs):
        if not path_params:
            path_params = {"stage": self.client.stage, "bk_apigw_ver": self.client.bk_apigw_ver}
        else:
            path_params.update({"stage": self.client.stage, "bk_apigw_ver": self.client.bk_apigw_ver})

        params, data = {}, {}
        for arg in args:
            if isinstance(arg, dict):
                params.update(arg)
        params.update(kwargs)

        # 获取 space_id（如果未通过关键字参数传递，则自动获取）
        if space_id is None:
            # 尝试从 params 中获取 scope_type 和 scope_value
            scope_type = params.get("scope_type")
            scope_value = params.get("scope_value")
            space_id = get_space_id(scope_type=scope_type, scope_value=scope_value)

        # 如果路径中包含 {space_id}，添加到 path_params
        if "{space_id}" in self.path and "space_id" not in path_params:
            path_params["space_id"] = space_id

        if self.token_required:
            if not headers or API_TOKEN_HEADER_KEY not in headers:
                raise APIException(f"当前接口需要token，请在请求头中添加${API_TOKEN_HEADER_KEY}")

        if self.method in ["POST", "PUT", "PATCH", "DELETE"]:
            data = params
            params = None
            # 对于 POST/PUT/PATCH/DELETE 请求，如果路径中不包含 {space_id}，添加到 data 中
            if "{space_id}" not in self.path and "space_id" not in data:
                data["space_id"] = space_id
        else:
            # 对于 GET/HEAD 请求，如果路径中不包含 {space_id}，添加到 params 中
            if "{space_id}" not in self.path and "space_id" not in params:
                params["space_id"] = space_id
        path = self.path
        # Request remote server
        if path_params:
            try:
                path = render_string(path, path_params)
            except KeyError as e:
                raise APIException(f"{e} is not in path_params")
        url = self.host.rstrip("/") + path
        try:
            # Pass headers to client.request if provided
            request_kwargs = {}
            if headers:
                request_kwargs["headers"] = headers
            resp = self.client.request(method=self.method, url=url, params=params, data=data, **request_kwargs)
        except Exception as e:
            logger.exception("Error occurred when requesting method=%s, url=%s", self.method, url)
            raise APIException("API调用出错, Exception: %s" % str(e), url=url)

        # Parse result
        if resp and resp.status_code != self.HTTP_STATUS_OK:
            message = "请求出现错误，请求HTTP状态码：%s" % resp.status_code
            raise APIException(message, resp=resp, url=url)

        # Response format json or text
        try:
            response = resp.json()
            return response
        except Exception:
            raise APIException("返回数据格式不正确，统一为json", resp=resp, url=url)
