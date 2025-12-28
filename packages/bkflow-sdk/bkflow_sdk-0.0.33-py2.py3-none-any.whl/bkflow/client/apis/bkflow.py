"""
TencentBlueKing is pleased to support the open source community by making
蓝鲸流程引擎服务 (BlueKing Flow Engine Service) available.
Copyright (C) 2024 THL A29 Limited,
a Tencent company. All rights reserved.
Licensed under the MIT License (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied. See the License for the
specific language governing permissions and limitations under the License.

We undertake not to change the open source license (MIT license) applicable

to the current version of the project delivered to anyone in the future.
"""

from bkflow.config.default import bkflow_sdk_settings

from ..base import RequestAPI


class CollectionsBKFlow:
    def __init__(self, client):
        self.client = client
        self.host = bkflow_sdk_settings.BKFLOW_SDK_APIGW_HOST
        self.apply_token = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/space/{space_id}/apply_token/",
            description="申请访问token",
        )
        self.admin_create_template = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/sdk/template/admin/create_default_template/{space_id}/",
            description="Admin创建流程",
        )
        self.create_template = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/space/{space_id}/create_template/",
            description="后台创建流程",
        )
        self.copy_template = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/sdk/template/admin/template_copy/",
            description="创建流程",
        )
        self.list_templates = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/space/{space_id}/get_template_list/",
            description="获取模板列表",
        )
        self.fetch_template = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/template/{template_id}/",
            description="获取流程详情",
            token_required=True,
        )
        self.update_template = RequestAPI(
            client=self.client,
            method="PUT",
            host=self.host,
            path="/{stage}/sdk/template/{template_id}/",
            description="更新模板",
            token_required=True,
        )
        self.delete_template = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/space/{space_id}/delete_template/{template_id}/",
            description="删除模板",
        )
        self.system_variables = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/template/variable/system_variable/",
            description="获取系统变量",
            token_required=True,
        )
        self.get_space_related_configs = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/template/{template_id}/get_space_related_configs/",
            description="获取空间相关配置",
            token_required=True,
        )
        self.list_inner_plugins = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/plugin/",
            description="获取插件",
            token_required=True,
        )
        self.get_inner_plugin_detail = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/plugin/{code}/",
            description="获取插件详情",
            token_required=True,
        )
        self.list_plugin_tags = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/plugin_service/tags/",
            description="获取第三方插件Tags",
        )
        self.list_plugin = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/bk_plugin/",
            description="获取第三方插件",
        )
        self.get_plugin_meta = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/plugin_service/meta/",
            description="获取第三方插件元信息",
        )
        self.get_plugin_app_detail = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/plugin_service/app_detail/",
            description="获取插件服务App详情",
        )
        self.get_service_plugin_detail = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/plugin_service/detail/",
            description="获取第三方插件详情",
        )
        self.analysis_constants_ref = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/sdk/template/analysis_constants_ref/",
            description="变量引用统计",
            token_required=True,
        )
        self.list_decision = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/decision_table/user/",
            description="获取用户决策表插件列表",
            token_required=True,
        )
        self.uniform_api = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/plugin_query/uniform_api/category_list/{space_id}/",
            description="获取uniform_api插件列表",
            token_required=True,
        )
        self.create_task = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/space/{space_id}/create_task/",
            description="创建任务",
        )
        self.front_operate_task = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/sdk/task/operate_task/{task_id}/{action}/",
            description="操作任务",
            token_required=True,
        )
        self.operation_record = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/template/{template_id}/get_template_operation_record/",
            description="操作记录",
            token_required=True,
        )
        self.variable_class_list = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/template/variable/",
            description="自定义变量列表",
        )
        self.variable_class_detail = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/template/variable/{variable_id}/",
            description="自定义变量详情",
        )
        self.check_variable_key = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/template/variable/check_variable_key/",
            description="检查变量key是否规范合法",
        )
        self.get_constant_preview_result = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/sdk/template/variable/get_constant_preview_result/",
            description="流程常量预览结果",
        )
        self.get_task_mock_data = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/task/get_task_mock_data/{task_id}/",
            description="获取任务的mock数据",
            token_required=True,
        )
        self.get_task_list = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/space/{space_id}/get_task_list/",
            description="获取任务列表",
        )
        self.get_task_states = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/space/{space_id}/task/{task_id}/get_task_states/",
            description="获取任务状态",
        )
        self.get_task_detail = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/space/{space_id}/task/{task_id}/get_task_detail/",
            description="获取任务详情",
        )
        self.get_tasks_states = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/space/{space_id}/get_tasks_states/",
            description="批量获取任务状态",
        )
        self.get_template_detail = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/space/{space_id}/template/{template_id}/get_template_detail/",
            description="获取模板详情",
        )
        self.operate_task = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/space/{space_id}/task/{task_id}/operate_task/{operation}/",
            description="操作任务",
        )
        self.get_draft_template = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/template/{template_id}/get_draft_template/",
            description="获取草稿模板",
            token_required=True,
        )
        self.calculate_version = RequestAPI(
            client=self.client,
            method="GET",
            host=self.host,
            path="/{stage}/sdk/template/{template_id}/calculate_version/",
            description="计算版本号",
            token_required=True,
        )
        self.release_template = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/space/{space_id}/template/{template_id}/release_template/",
            description="免登录发布模板",
        )
        self.front_release_template = RequestAPI(
            client=self.client,
            method="POST",
            host=self.host,
            path="/{stage}/sdk/template/{template_id}/release_template/",
            description="发布模板",
            token_required=True,
        )
        self.rollback_template = (
            RequestAPI(
                client=self.client,
                method="POST",
                host=self.host,
                path="/{stage}/sdk/template/{template_id}/rollback_template/",
                description="回滚模板",
                token_required=True,
            ),
        )
        self.preview_task_tree = (
            RequestAPI(
                client=self.client,
                method="POST",
                host=self.host,
                path="/{stage}/sdk/template/{template_id}/preview_task_tree/",
                description="预览任务树",
                token_required=True,
            ),
        )
        self.list_snapshot = (
            RequestAPI(
                client=self.client,
                method="GET",
                host=self.host,
                path="/{stage}/sdk/template/snapshot/list_snapshot/",
                description="获取模板快照列表",
                token_required=True,
            ),
        )
        self.delete_snapshot = (
            RequestAPI(
                client=self.client,
                method="POST",
                host=self.host,
                path="/{stage}/sdk/template/snapshot/{snapshot_id}/delete_snapshot/",
                description="删除模板快照",
                token_required=True,
            ),
        )
