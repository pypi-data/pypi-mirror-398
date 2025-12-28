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
import importlib

from django.conf import settings

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

    if transformer_path:
        try:
            # 解析函数路径，格式：module.path.function_name 或 module.path.ClassName.method_name
            # 从右到左尝试解析，找到最长的可导入模块路径
            parts = transformer_path.split(".")
            if len(parts) < 2:
                raise ValueError(
                    "BKFLOW_SDK_SPACE_TRANSFORMER 格式错误，应为 'module.path.function_name'"
                    " 或 'module.path.ClassName.method_name'"
                )

            # 尝试导入模块，从最长的路径开始
            transformer_func = None
            for i in range(len(parts) - 1, 0, -1):
                try:
                    module_path = ".".join(parts[:i])
                    attr_path = parts[i:]
                    module = importlib.import_module(module_path)
                    # 递归获取属性（支持类方法）
                    transformer_func = module
                    for attr_name in attr_path:
                        transformer_func = getattr(transformer_func, attr_name)
                    break
                except (ImportError, AttributeError):
                    continue

            if transformer_func is None:
                raise ValueError(f"无法解析 BKFLOW_SDK_SPACE_TRANSFORMER: {transformer_path}")

            # 调用函数获取 space_id
            space_id = transformer_func(scope_type=scope_type, scope_value=scope_value)
            if space_id is not None:
                return space_id
        except Exception as e:
            # 如果 transformer 调用失败，记录错误并使用默认值
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"调用 BKFLOW_SDK_SPACE_TRANSFORMER 失败: {e}，将使用默认值")

    # 使用默认值
    default_space_id = getattr(bkflow_sdk_settings, "BKFLOW_SDK_DEFAULT_SPACE_ID", None)
    if default_space_id is not None and default_space_id != "":
        return default_space_id

    raise ValueError("未配置 BKFLOW_SDK_DEFAULT_SPACE_ID 或 BKFLOW_SDK_SPACE_TRANSFORMER，无法获取 space_id")
