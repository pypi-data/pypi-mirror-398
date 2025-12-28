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
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from bkflow.client.core import get_redirect_client, get_redirect_client_with_auth
from bkflow.common.decorators import params_valid, token_inject
from bkflow.common.views import SimpleGenericViewSet
from bkflow.config.default import API_TOKEN_HEADER_KEY
from bkflow.interface.serializers import (
    AnalysisConstantsRefSerializer,
    BatchTaskStatesSerializer,
    BKPluginSerializer,
    CalculateVersionSerializer,
    CheckVariableKeySerializer,
    CopyTemplateSerializer,
    CreateTaskSerializer,
    CreateTemplateSerializer,
    DecisionTableSerializer,
    DeleteTemplateSerializer,
    GetConstantPreviewResultSerializer,
    GetDraftTemplateSerializer,
    GetServicePluginSerializer,
    InnerPluginDetailSerializer,
    OperateTaskSerializer,
    PluginCodeQuerySerializer,
    PreviewTaskTreeSerializer,
    ScopeSerializer,
    ServicePluginDetailSerializer,
    SnapshotSerializer,
    TaskListSerializer,
    TaskSerializer,
    TemplateDetailQuerySerializer,
    TemplateListSerializer,
    TemplateReleaseSerializer,
    TemplateRollbackSerializer,
    UniFormAPiSerializer,
    UpdateTemplateSerializer,
)
from bkflow.interface.signals import (
    post_mock_task_signal,
    post_task_signal,
    post_template_signal,
    pre_mock_task_signal,
    pre_task_signal,
    pre_template_signal,
)


class TemplateViewSet(SimpleGenericViewSet):
    """流程模板视图集

    提供流程模板的创建、查询、更新、删除等操作
    """

    lookup_field = "template_id"

    @swagger_auto_schema(
        operation_summary="获取流程模板列表",
        operation_description="获取指定空间下的流程模板列表，支持按名称、创建者、更新人等条件筛选，支持分页查询",
        query_serializer=TemplateListSerializer,
        tags=["流程模板"],
    )
    @params_valid(TemplateListSerializer)
    def list(self, request, params):
        """获取流程列表"""
        pre_template_signal.send(sender="list_template", request_data=params)

        client = get_redirect_client(request)
        data = client.bkflow.list_templates(**params)

        post_template_signal.send(sender="list_template", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="创建流程模板",
        operation_description="在指定空间下创建新的流程模板，支持从已有模板复制或创建空白模板",
        request_body=CreateTemplateSerializer,
        tags=["流程模板"],
    )
    @action(methods=["POST"], detail=False)
    @params_valid(CreateTemplateSerializer)
    def create_template(self, request, params):
        """创建流程"""
        pre_template_signal.send(sender="create_template", request_data=params)

        client = get_redirect_client_with_auth(request)
        data = client.bkflow.create_template(**params)

        post_template_signal.send(sender="create_template", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="创建流程任务",
        operation_description="基于流程模板创建任务实例，可指定任务参数和常量值",
        request_body=CreateTaskSerializer,
        tags=["流程任务"],
    )
    @action(methods=["POST"], detail=False)
    @params_valid(CreateTaskSerializer)
    def create_task(self, request, params):
        """创建任务"""
        pre_task_signal.send(sender="create_task", request_data=params)

        client = get_redirect_client(request)
        data = client.bkflow.create_task(params)

        post_task_signal.send(sender="create_task", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取流程模板详情",
        operation_description="获取指定流程模板的完整信息，包括流程树、变量配置等，支持获取 Mock 数据",
        query_serializer=TemplateDetailQuerySerializer,
        tags=["流程模板"],
    )
    @action(methods=["GET"], detail=True)
    @token_inject
    @params_valid(TemplateDetailQuerySerializer)
    def fetch_template(self, request, template_id, params):
        """获取流程详情"""
        pre_template_signal.send(sender="fetch_template", request_data=params)

        client = get_redirect_client_with_auth(request)
        data = client.bkflow.fetch_template(
            params, path_params={"template_id": template_id}, headers={API_TOKEN_HEADER_KEY: request.token}
        )

        post_template_signal.send(sender="fetch_template", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="PUT",
        operation_summary="更新流程模板",
        operation_description="更新指定流程模板的配置信息，包括流程树、变量、触发器等",
        request_body=UpdateTemplateSerializer,
        tags=["流程模板"],
    )
    @action(methods=["PUT"], detail=True)
    @token_inject
    @params_valid(UpdateTemplateSerializer)
    def update_template(self, request, template_id, params):
        pre_template_signal.send(sender="update_template", request_data=params)

        client = get_redirect_client_with_auth(request)
        data = client.bkflow.update_template(
            path_params={"template_id": template_id}, headers={API_TOKEN_HEADER_KEY: request.token}, **params
        )

        post_template_signal.send(sender="update_template", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="复制流程",
        operation_description="",
        request_body=CopyTemplateSerializer,
        tags=["流程模板"],
    )
    @action(methods=["POST"], detail=True)
    @params_valid(CopyTemplateSerializer)
    def copy_template(self, request, template_id, params):
        pre_template_signal.send(sender="copy_template", request_data=params)

        client = get_redirect_client_with_auth(request)
        data = client.bkflow.copy_template(
            {
                "template_id": template_id,
            }
        )

        post_template_signal.send(sender="copy_template", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取空间相关配置",
        operation_description="获取流程模板所在空间的相关配置信息，包括权限配置、资源配置等",
        tags=["流程模板"],
    )
    @action(methods=["GET"], detail=True)
    @token_inject
    def get_space_related_configs(self, request, template_id):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.get_space_related_configs(
            path_params={"template_id": template_id}, headers={API_TOKEN_HEADER_KEY: request.token}
        )
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="变量引用统计分析",
        operation_description="分析流程中变量的引用情况，包括活动节点、网关、常量等对变量的引用关系",
        request_body=AnalysisConstantsRefSerializer,
        tags=["流程变量"],
    )
    @action(methods=["POST"], detail=False)
    @token_inject
    @params_valid(AnalysisConstantsRefSerializer)
    def analysis_constants_ref(self, request, params):
        pre_template_signal.send(sender="analysis_constants_ref", request_data=params)

        client = get_redirect_client_with_auth(request)
        data = client.bkflow.analysis_constants_ref(**params, headers={API_TOKEN_HEADER_KEY: request.token})

        post_task_signal.send(sender="analysis_constants_ref", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取流程操作记录",
        operation_description="获取指定流程模板的操作历史记录，包括创建、更新、删除等操作日志",
        query_serializer=ScopeSerializer,
        tags=["流程模板"],
    )
    @action(methods=["GET"], detail=True)
    @token_inject
    @params_valid(ScopeSerializer)
    def operation_record(self, request, template_id, params):
        pre_template_signal.send(sender="operation_record", request_data=params)

        client = get_redirect_client_with_auth(request)
        data = client.bkflow.operation_record(
            path_params={"template_id": template_id},
            headers={API_TOKEN_HEADER_KEY: request.token},
        )

        post_template_signal.send(sender="operation_record", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="操作流程任务",
        operation_description="对流程任务进行操作控制，支持启动、暂停、继续、撤销、重试等操作",
        request_body=OperateTaskSerializer,
        tags=["流程任务"],
    )
    @action(methods=["POST"], detail=False)
    @token_inject
    @params_valid(OperateTaskSerializer)
    def operate_task(self, request, params):
        pre_task_signal.send(sender="operate_task", request_data=params)
        client = get_redirect_client_with_auth(request, with_apply_token=True)
        data = client.bkflow.front_operate_task(
            path_params={"task_id": params.get("task_id"), "action": params.get("action")},
            headers={API_TOKEN_HEADER_KEY: request.token},
        )
        post_task_signal.send(sender="operate_task", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取任务 Mock 数据",
        operation_description="获取任务节点的 Mock 测试数据，用于调试和测试流程",
        query_serializer=TaskSerializer,
        tags=["流程任务"],
    )
    @action(methods=["GET"], detail=False)
    @token_inject
    @params_valid(TaskSerializer)
    def get_task_mock_data(self, request, params):
        pre_mock_task_signal.send(sender="get_task_mock_data", request_data=params)

        client = get_redirect_client_with_auth(request)
        data = client.bkflow.get_task_mock_data(
            path_params={"task_id": params.get("task_id")}, headers={API_TOKEN_HEADER_KEY: request.token}
        )

        post_mock_task_signal.send(sender="get_task_mock_data", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取任务列表",
        operation_description="获取指定空间下的任务列表，支持按状态、创建时间等条件筛选",
        query_serializer=ScopeSerializer,
        tags=["流程任务"],
    )
    @action(methods=["GET"], detail=False)
    @params_valid(TaskListSerializer)
    def get_task_list(self, request, params):
        pre_task_signal.send(sender="get_task_list", request_data=params)
        client = get_redirect_client(request)
        data = client.bkflow.get_task_list(**params)
        post_task_signal.send(sender="get_task_list", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取任务状态",
        operation_description="获取指定任务的执行状态信息，包括各节点的执行情况",
        query_serializer=TaskSerializer,
        tags=["流程任务"],
    )
    @action(methods=["GET"], detail=False)
    @params_valid(TaskSerializer)
    def get_task_states(self, request, params):
        pre_task_signal.send(sender="get_task_states", request_data=params)
        client = get_redirect_client(request)
        data = client.bkflow.get_task_states(path_params={"task_id": params.get("task_id")})
        post_task_signal.send(sender="get_task_states", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取任务详情",
        operation_description="获取指定任务的完整详细信息，包括任务配置、执行参数等",
        query_serializer=TaskSerializer,
        tags=["流程任务"],
    )
    @action(methods=["GET"], detail=False)
    @params_valid(TaskSerializer)
    def get_task_detail(self, request, params):
        pre_task_signal.send(sender="get_task_detail", request_data=params)
        client = get_redirect_client(request)
        data = client.bkflow.get_task_detail(path_params={"task_id": params.get("task_id")})
        post_task_signal.send(sender="get_task_detail", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="批量获取任务状态",
        operation_description="批量获取多个任务的执行状态信息，提高查询效率",
        request_body=BatchTaskStatesSerializer,
        tags=["流程任务"],
    )
    @action(methods=["POST"], detail=False)
    @params_valid(BatchTaskStatesSerializer)
    def get_tasks_states(self, request, params):
        pre_task_signal.send(sender="get_tasks_states", request_data=params)
        client = get_redirect_client(request)
        data = client.bkflow.get_tasks_states(**params)
        post_task_signal.send(sender="get_tasks_states", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="DELETE",
        operation_summary="删除流程",
        operation_description="删除指定流程实例",
        request_body=DeleteTemplateSerializer,
        tags=["流程任务"],
    )
    @action(methods=["DELETE"], detail=True)
    @params_valid(DeleteTemplateSerializer)
    def delete_template(self, request, template_id, params):
        pre_template_signal.send(sender="delete_template", request_data=params)
        client = get_redirect_client(request)
        data = client.bkflow.delete_template(path_params={"template_id": template_id})
        post_template_signal.send(sender="delete_template", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="预览任务树",
        operation_description="预览指定任务的执行树结构",
        request_body=PreviewTaskTreeSerializer,
        tags=["流程任务"],
    )
    @action(methods=["POST"], detail=False)
    @token_inject
    @params_valid(PreviewTaskTreeSerializer)
    def preview_task_tree(self, request, template_id, params):
        pre_task_signal.send(sender="preview_task_tree", request_data=params)
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.preview_task_tree(
            path_params={"template_id": template_id}, headers={API_TOKEN_HEADER_KEY: request.token}, **params
        )
        post_task_signal.send(sender="preview_task_tree", response_data=data, request_data=params)
        return Response(data)

    swagger_auto_schema(
        method="GET",
        operation_summary="获取流程草稿",
        operation_description="获取指定流程的草稿版本",
        query_serializer=GetDraftTemplateSerializer,
        tags=["流程模板"],
    )

    @action(methods=["GET"], detail=True)
    @token_inject
    @params_valid(GetDraftTemplateSerializer)
    def get_draft_template(self, request, template_id, params):
        pre_template_signal.send(sender="get_draft_template", request_data=params)
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.get_draft_template(
            path_params={"template_id": template_id}, headers={API_TOKEN_HEADER_KEY: request.token}
        )
        post_template_signal.send(sender="get_draft_template", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="计算流程版本",
        operation_description="计算指定流程的版本号",
        request_body=CalculateVersionSerializer,
        tags=["流程模板"],
    )
    @action(methods=["POST"], detail=True)
    @token_inject
    @params_valid(CalculateVersionSerializer)
    def calculate_version(self, request, template_id, params):
        pre_template_signal.send(sender="calculate_version", request_data=params)
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.calculate_version(
            path_params={"template_id": template_id}, headers={API_TOKEN_HEADER_KEY: request.token}
        )
        post_template_signal.send(sender="calculate_version", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="发布流程",
        operation_description="发布指定流程版本",
        request_body=TemplateReleaseSerializer,
        tags=["流程模板"],
    )
    @action(methods=["POST"], detail=True)
    @token_inject
    @params_valid(TemplateReleaseSerializer)
    def release_template(self, request, template_id, params):
        pre_template_signal.send(sender="release_template", request_data=params)
        client = get_redirect_client(request)
        data = client.bkflow.front_release_template(
            path_params={"template_id": template_id}, headers={API_TOKEN_HEADER_KEY: request.token}, **params
        )
        post_template_signal.send(sender="release_template", response_data=data, request_data=params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="回滚流程",
        operation_description="回滚指定流程到指定版本",
        request_body=TemplateRollbackSerializer,
        tags=["流程模板"],
    )
    @action(methods=["POST"], detail=True)
    @token_inject
    @params_valid(TemplateRollbackSerializer)
    def rollback_template(self, request, template_id, params):
        pre_template_signal.send(sender="rollback_template", request_data=params)
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.rollback_template(
            path_params={"template_id": template_id}, headers={API_TOKEN_HEADER_KEY: request.token}, **params
        )
        post_template_signal.send(sender="rollback_template", response_data=data, request_data=params)
        return Response(data)


class InnerPluginViewSet(SimpleGenericViewSet):
    """内置插件视图集

    提供内置插件的查询功能
    """

    lookup_field = "code"

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取内置插件列表",
        operation_description="获取系统内置的所有插件列表，包括标准原子、子流程等",
        tags=["插件管理"],
    )
    @action(methods=["GET"], detail=False)
    @token_inject
    def plugins(self, request):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.list_inner_plugins(headers={API_TOKEN_HEADER_KEY: request.token})
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取内置插件详情",
        operation_description="获取指定内置插件的详细配置信息，包括输入输出参数定义",
        query_serializer=InnerPluginDetailSerializer,
        tags=["插件管理"],
    )
    @action(methods=["GET"], detail=True)
    @token_inject
    @params_valid(InnerPluginDetailSerializer)
    def plugin_detail(self, request, code, params):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.get_inner_plugin_detail(
            params, path_params={"code": code}, headers={API_TOKEN_HEADER_KEY: request.token}
        )
        return Response(data)


class PluginServiceViewSet(SimpleGenericViewSet):
    """第三方插件服务视图集

    提供第三方插件的管理功能
    """

    lookup_field = "plugin_code"

    @swagger_auto_schema(
        method="GET", operation_summary="获取插件标签分类", operation_description="获取第三方插件的标签分类信息，用于插件分组展示", tags=["插件管理"]
    )
    @action(methods=["GET"], detail=False)
    def tags(self, request):
        client = get_redirect_client_with_auth(request)
        response = client.bkflow.list_plugin_tags()
        return Response(response)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取第三方插件元数据",
        operation_description="获取指定第三方插件的元信息，包括插件版本、作者等基础信息",
        query_serializer=GetServicePluginSerializer,
        tags=["插件管理"],
    )
    @action(methods=["GET"], detail=False)
    @params_valid(GetServicePluginSerializer)
    def meta(self, request, params):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.get_plugin_meta(params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取第三方插件配置详情",
        operation_description="获取指定第三方插件的完整配置信息，包括表单定义、输出参数等",
        query_serializer=ServicePluginDetailSerializer,
        tags=["插件管理"],
    )
    @action(methods=["GET"], detail=False)
    @params_valid(ServicePluginDetailSerializer)
    def plugin_detail(self, request, params):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.get_service_plugin_detail(params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取第三方插件列表",
        operation_description="获取第三方插件列表",
        query_serializer=BKPluginSerializer,
        tags=["插件管理"],
    )
    @action(methods=["GET"], detail=False)
    @params_valid(BKPluginSerializer)
    def list_plugin(self, request, params):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.list_plugin(**params)
        return Response(data)

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取插件服务App详情",
        operation_description="获取插件服务App详情",
        query_serializer=PluginCodeQuerySerializer,
        tags=["插件管理"],
    )
    @action(methods=["GET"], detail=False)
    @params_valid(PluginCodeQuerySerializer)
    def get_plugin_app_detail(self, request, params):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.get_plugin_app_detail(**params)
        return Response(data)


class UniformApiViewSet(SimpleGenericViewSet):
    """统一 API 插件视图集

    提供统一 API 插件的查询功能
    """

    lookup_field = "space_id"

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取统一 API 插件列表",
        operation_description="获取指定空间下的统一 API 插件分类列表",
        query_serializer=UniFormAPiSerializer,
        tags=["插件管理"],
    )
    @action(methods=["GET"], detail=False)
    @token_inject
    @params_valid(UniFormAPiSerializer)
    def category_list(self, request, params):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.uniform_api(
            params,
            headers={API_TOKEN_HEADER_KEY: request.token},
        )
        return Response(data)


class SystemVariableViewSet(SimpleGenericViewSet):
    """系统变量视图集

    提供系统变量和自定义变量的管理功能
    """

    lookup_field = "variable_id"

    @swagger_auto_schema(
        method="GET", operation_summary="获取系统变量列表", operation_description="获取系统预定义的所有变量列表，如当前用户、当前时间等", tags=["流程变量"]
    )
    @action(methods=["GET"], detail=False)
    @token_inject
    def system_variables(self, request):
        client = get_redirect_client_with_auth(request)
        response = client.bkflow.system_variables(headers={API_TOKEN_HEADER_KEY: request.token})
        return Response(response)

    @swagger_auto_schema(
        method="GET", operation_summary="获取自定义变量列表", operation_description="获取系统中定义的所有自定义变量类型列表", tags=["流程变量"]
    )
    @action(methods=["GET"], detail=False)
    def variable_class_list(self, request):
        client = get_redirect_client_with_auth(request)
        response = client.bkflow.variable_class_list()
        return Response(response)

    @swagger_auto_schema(
        method="GET", operation_summary="获取自定义变量详情", operation_description="获取指定自定义变量的详细配置信息", tags=["流程变量"]
    )
    @action(methods=["GET"], detail=True)
    def variable_class_detail(self, request, variable_id):
        client = get_redirect_client_with_auth(request)
        response = client.bkflow.variable_class_detail(path_params={"variable_id": variable_id})
        return Response(response)

    @swagger_auto_schema(
        method="GET",
        operation_summary="检测变量 Key 是否合法",
        operation_description="检测变量 Key 的命名是否符合规范，是否已被使用",
        query_serializer=CheckVariableKeySerializer,
        tags=["流程变量"],
    )
    @action(methods=["GET"], detail=False)
    @params_valid(CheckVariableKeySerializer)
    def check_variable_key(self, request, params):
        client = get_redirect_client_with_auth(request)
        response = client.bkflow.check_variable_key(**params)
        return Response(response)

    @swagger_auto_schema(
        method="POST",
        operation_summary="获取常量预览结果",
        operation_description="预览流程常量的实际值，用于调试和验证变量引用",
        request_body=GetConstantPreviewResultSerializer,
        tags=["流程变量"],
    )
    @action(methods=["POST"], detail=False)
    @params_valid(GetConstantPreviewResultSerializer)
    def get_constant_preview_result(self, request, params):
        client = get_redirect_client_with_auth(request)
        response = client.bkflow.get_constant_preview_result(**params)
        return Response(response)


class DecisionTableViewSet(SimpleGenericViewSet):
    """决策表视图集

    提供决策表插件的管理功能
    """

    lookup_field = "template_id"

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取决策表插件列表",
        operation_description="获取用户创建的决策表插件列表，支持分页查询",
        query_serializer=DecisionTableSerializer,
        tags=["插件管理"],
    )
    @action(methods=["GET"], detail=False)
    @token_inject
    @params_valid(DecisionTableSerializer)
    def lists(self, request, params):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.list_decision(params, headers={API_TOKEN_HEADER_KEY: request.token})
        return Response(data)


class TemplateSnapshotViewSet(SimpleGenericViewSet):

    lookup_field = "snapshot_id"

    @swagger_auto_schema(
        method="GET",
        operation_summary="获取流程快照列表",
        operation_description="获取流程快照列表，支持分页查询",
        query_serializer=SnapshotSerializer,
        tags=["流程快照"],
    )
    @action(methods=["GET"], detail=False)
    @token_inject
    @params_valid(SnapshotSerializer)
    def list_snapshot(self, request, params):
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.list_snapshot(headers={API_TOKEN_HEADER_KEY: request.token}, **params)
        return Response(data)

    @swagger_auto_schema(
        method="POST",
        operation_summary="删除流程快照",
        operation_description="删除流程快照",
        query_serializer=SnapshotSerializer,
        tags=["流程快照"],
    )
    @action(methods=["POST"], detail=True)
    @token_inject
    @params_valid(SnapshotSerializer)
    def delete_snapshot(self, request, snapshot_id, params):
        pre_template_signal.send(sender="rollback_template", request_data=params)
        client = get_redirect_client_with_auth(request)
        data = client.bkflow.delete_snapshot(
            path_params={"snapshot_id": snapshot_id}, headers={API_TOKEN_HEADER_KEY: request.token}, **params
        )
        post_template_signal.send(sender="rollback_template", request_data=params)
        return Response(data)
