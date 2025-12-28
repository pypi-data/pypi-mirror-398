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
from django.dispatch import Signal

request_signal = Signal()

pre_request_signal = Signal()
post_request_signal = Signal()

pre_template_signal = Signal()
post_template_signal = Signal()

pre_task_signal = Signal()
post_task_signal = Signal()

pre_mock_task_signal = Signal()
post_mock_task_signal = Signal()
