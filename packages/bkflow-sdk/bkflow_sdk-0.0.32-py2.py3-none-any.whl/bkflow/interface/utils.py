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

from bkflow.common.loader import call_config_function
from bkflow.config.default import bkflow_sdk_settings


def get_space_id(scope_type=None, scope_value=None):
    """
    获取 space_id

    优先级：
    1. 如果配置了 BKFLOW_SDK_SPACE_TRANSFORMER，则调用该函数获取
    2. 否则使用 settings.BKFLOW_SDK_DEFAULT_SPACE_ID

    :param scope_type: 流程范围类型，如 project/organization/global 等
    :param scope_value: 流程范围值，与 scope_type 配合使用
    :return: space_id
    """
    transformer_path = getattr(settings, "BKFLOW_SDK_SPACE_TRANSFORMER", None)

    # 尝试通过 transformer 函数获取 space_id
    if transformer_path:
        space_id = call_config_function(
            transformer_path,
            "BKFLOW_SDK_SPACE_TRANSFORMER",
            error_message_prefix="调用 BKFLOW_SDK_SPACE_TRANSFORMER",
            scope_type=scope_type,
            scope_value=scope_value,
        )
        if space_id is not None:
            return space_id

    # 使用默认值
    default_space_id = getattr(bkflow_sdk_settings, "BKFLOW_SDK_DEFAULT_SPACE_ID", None)
    if default_space_id is not None and default_space_id != "":
        return default_space_id

    raise ValueError("未配置 BKFLOW_SDK_DEFAULT_SPACE_ID 或 BKFLOW_SDK_SPACE_TRANSFORMER，无法获取 space_id")
