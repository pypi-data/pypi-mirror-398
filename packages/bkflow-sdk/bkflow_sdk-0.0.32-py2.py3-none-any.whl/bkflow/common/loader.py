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
import logging

logger = logging.getLogger(__name__)


def load_function_from_path(function_path, setting_name):
    """
    从配置的函数路径动态加载函数

    :param function_path: 函数路径，格式：module.path.function_name 或 module.path.ClassName.method_name
    :param setting_name: 配置项名称，用于错误消息
    :return: 加载的函数对象，如果无法加载则返回 None
    :raises ValueError: 当函数路径格式错误或无法解析时
    """
    if not function_path:
        return None

    # 解析函数路径，格式：module.path.function_name 或 module.path.ClassName.method_name
    # 从右到左尝试解析，找到最长的可导入模块路径
    parts = function_path.split(".")
    if len(parts) < 2:
        raise ValueError(f"{setting_name} 格式错误，应为 'module.path.function_name'" " 或 'module.path.ClassName.method_name'")

    # 尝试导入模块，从最长的路径开始
    func = None
    last_exception = None
    for i in range(len(parts) - 1, 0, -1):
        try:
            module_path = ".".join(parts[:i])
            attr_path = parts[i:]
            module = importlib.import_module(module_path)
            # 递归获取属性（支持类方法）
            func = module
            for attr_name in attr_path:
                func = getattr(func, attr_name)
            break
        except ImportError:
            # ImportError 表示模块不存在，继续尝试下一个路径
            continue
        except AttributeError as e:
            # AttributeError 表示模块存在但属性不存在
            # 如果这是第一个成功的模块导入，说明路径格式正确但属性不存在，应该抛出异常
            # 否则继续尝试其他路径
            last_exception = e
            # 如果已经成功导入了模块，说明路径是正确的，只是属性不存在，应该立即抛出异常
            if module is not None:
                raise ValueError(
                    f"无法解析 {setting_name}: {function_path}，" f"模块 '{module_path}' 存在但属性 '{'.'.join(attr_path)}' 不存在"
                )
            continue

    if func is None:
        # 如果所有尝试都失败，抛出异常
        if last_exception:
            raise ValueError(f"无法解析 {setting_name}: {function_path}，原因：{str(last_exception)}")
        else:
            raise ValueError(f"无法解析 {setting_name}: {function_path}")

    return func


def call_config_function(function_path, setting_name, error_message_prefix=None, **kwargs):
    """
    调用配置的函数并返回结果

    :param function_path: 函数路径，格式：module.path.function_name 或 module.path.ClassName.method_name
    :param setting_name: 配置项名称，用于错误消息
    :param error_message_prefix: 错误消息前缀，用于日志记录
    :param kwargs: 传递给函数的参数
    :return: 函数返回值，如果函数未配置或调用失败则返回 None
    """
    if not function_path:
        return None

    try:
        func = load_function_from_path(function_path, setting_name)
        if func is None:
            return None

        # 调用函数
        result = func(**kwargs)
        return result
    except Exception as e:
        # 如果函数调用失败，记录错误
        error_prefix = error_message_prefix or f"调用 {setting_name}"
        logger.warning(f"{error_prefix} 失败: {e}，将使用默认逻辑")
        return None
