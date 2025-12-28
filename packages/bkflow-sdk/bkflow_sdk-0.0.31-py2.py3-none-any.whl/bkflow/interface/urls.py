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

from django.urls import include, path
from rest_framework import routers

from bkflow.interface.views import (
    DecisionTableViewSet,
    InnerPluginViewSet,
    PluginServiceViewSet,
    SystemVariableViewSet,
    TemplateViewSet,
    UniformApiViewSet,
)

router = routers.DefaultRouter(trailing_slash=True)

router.register(r"decision_table", DecisionTableViewSet, basename="decision_table")
router.register(r"inner_plugin", InnerPluginViewSet, basename="inner_plugin")
router.register(r"template", TemplateViewSet, basename="template")
router.register(r"plugin", PluginServiceViewSet, basename="plugin")
router.register(r"variable", SystemVariableViewSet, basename="variable")
router.register(r"uniform", UniformApiViewSet, basename="uniform")

urlpatterns = [
    path("", include(router.urls)),
]
