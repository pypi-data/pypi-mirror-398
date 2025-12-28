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
from django.conf import settings

BKFLOW_SDK_APIGW_HOST = getattr(settings, "BKFLOW_SDK_APIGW_HOST", "")
DEFAULT_SETTINGS = {
    "BKFLOW_SDK_APIGW_HOST": BKFLOW_SDK_APIGW_HOST,
    "BKFLOW_SDK_DEFAULT_SPACE_ID": "",
    "BKFLOW_SDK_SPACE_TRANSFORMER": "",  # 可执行函数路径，格式：module.path.function_name 或 module.path.ClassName.method_name
    "BKFLOW_SDK_APIGW_HEADERS_GENERATOR": "",  # 可执行函数路径，格式：module.path.function_name 或 module.path.ClassName.method_name # noqa: E501
    "common_key1": "common_value2",
    "interface": {"interface_key1": "interface_value1"},
}
REQUEST_TOKEN_HEADER_KEY = "HTTP_BKFLOW_TOKEN"
API_TOKEN_HEADER_KEY = "BKFLOW-TOKEN"
BK_TOKEN_EXPIRED_CODE = "1640001"


class BkflowSDKSettings:
    SETTING_PREFIX = "BKFLOW_SDK"
    NESTING_SEPARATOR = "_"

    def __init__(self, default_settings=None):
        self.project_settings = self.get_flatten_settings(getattr(settings, self.SETTING_PREFIX, {}))
        self.default_settings = self.get_flatten_settings(default_settings or DEFAULT_SETTINGS)

    def __getattr__(self, key):
        if key not in self.project_settings and key not in self.default_settings:
            raise AttributeError

        value = self.project_settings.get(key) or self.default_settings.get(key)
        if value is not None:
            setattr(self, key, value)
        return value

    def get_flatten_settings(self, inputted_settings: dict, cur_prefix: str = ""):
        def get_cur_key(cur_key):
            return f"{cur_prefix}{self.NESTING_SEPARATOR}{cur_key}" if cur_prefix else cur_key

        flatten_settings = {}
        for key, value in inputted_settings.items():
            if isinstance(value, dict):
                flatten_sub_settings = self.get_flatten_settings(value, key)
                flatten_settings.update(
                    {
                        get_cur_key(flatten_key): flatten_value
                        for flatten_key, flatten_value in flatten_sub_settings.items()
                    }
                )
            else:
                flatten_settings[get_cur_key(key)] = value
        return flatten_settings


bkflow_sdk_settings = BkflowSDKSettings(DEFAULT_SETTINGS)
