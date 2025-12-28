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

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class ScopeSerializer(serializers.Serializer):
    """流程范围序列化器，用于指定流程的作用域"""

    scope_type = serializers.CharField(
        help_text=_("流程范围类型，如 project/organization/global 等"),
        max_length=128,
        required=False,
        allow_null=True,
        allow_blank=True,
    )
    scope_value = serializers.CharField(
        help_text=_("流程范围值，与 scope_type 配合使用，指定具体的范围 ID"),
        max_length=128,
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class TemplateSerializer(ScopeSerializer):
    """流程模板序列化器，用于定义流程模板的基本信息"""

    name = serializers.CharField(help_text=_("流程模板名称，唯一标识流程"), max_length=128, required=True)
    notify_config = serializers.JSONField(help_text=_("通知配置，JSON格式，包含通知方式、通知人等信息"), required=False)
    desc = serializers.CharField(
        help_text=_("流程描述，说明流程的用途和功能"), max_length=256, required=False, allow_blank=True, allow_null=True
    )
    source = serializers.CharField(
        help_text=_("流程来源，标识流程的创建方式或来源系统"), max_length=32, required=False, allow_null=True, allow_blank=True
    )
    version = serializers.CharField(
        help_text=_("流程版本号，用于版本管理"), max_length=32, required=False, allow_blank=True, allow_null=True
    )
    extra_info = serializers.JSONField(help_text=_("额外扩展信息，JSON格式，用于存储自定义字段"), required=False)

    def validate(self, attrs):
        if "desc" in attrs and (attrs["desc"] is None or attrs["desc"] == ""):
            del attrs["desc"]
        return attrs


class CreateTemplateSerializer(TemplateSerializer):
    """创建流程模板序列化器"""

    source_template_id = serializers.IntegerField(help_text=_("源模板ID，从已有模板复制时使用"), required=False, allow_null=True)
    pipeline_tree = serializers.JSONField(help_text=_("流程树，JSON格式，包含流程节点、连线等完整信息"), required=False)
    operator = serializers.CharField(help_text=_("操作人，记录创建或更新流程的用户"), max_length=32, required=False, allow_blank=True)
    triggers = serializers.ListField(required=False, help_text=_("触发器配置列表，用于设置流程的自动触发条件"), allow_empty=True)


class CreateTaskSerializer(ScopeSerializer):
    """创建流程任务序列化器"""

    template_id = serializers.IntegerField(help_text=_("流程模板ID，指定要实例化的流程模板"), required=True)
    name = serializers.CharField(help_text=_("任务名称，用于标识任务实例"), max_length=128, required=False, allow_blank=True)
    creator = serializers.CharField(help_text=_("任务创建者，记录创建任务的用户"), max_length=32, required=True)
    description = serializers.CharField(help_text=_("任务描述，说明任务的目的和背景"), required=True, allow_blank=True)
    constants = serializers.JSONField(help_text=_("任务启动参数，JSON格式，包含流程执行所需的变量值"), required=False, default=dict)


class UpdateTemplateSerializer(TemplateSerializer):
    """更新流程模板序列化器"""

    operator = serializers.CharField(help_text=_("操作人，记录更新流程的用户"), max_length=32, required=False, allow_blank=True)
    pipeline_tree = serializers.JSONField(help_text=_("流程树信息，包含更新后的完整流程结构"), required=True)
    triggers = serializers.ListField(required=True, help_text=_("触发器配置列表，更新流程的触发条件"), allow_empty=True)


class CopyTemplateSerializer(ScopeSerializer):
    """复制流程模板序列化器"""

    name = serializers.CharField(help_text=_("新模板名称，用于标识复制后的流程"), max_length=128, required=False, allow_blank=True)
    desc = serializers.CharField(help_text=_("新模板描述，说明新模板的目的和背景"), required=False, allow_blank=True)


class GetServicePluginSerializer(serializers.Serializer):
    """获取第三方插件元数据序列化器"""

    plugin_code = serializers.CharField(required=True, help_text=_("插件编码，唯一标识第三方插件"))


class InnerPluginDetailSerializer(serializers.Serializer):
    """获取内置插件详情序列化器"""

    version = serializers.CharField(required=False, help_text=_("插件版本号，不指定则返回最新版本"), allow_blank=True)


class DecisionTableSerializer(serializers.Serializer):
    """获取用户决策表插件列表序列化器"""

    limit = serializers.IntegerField(
        required=False, help_text=_("分页大小，每页返回的数据量"), default=20, min_value=1, max_value=200
    )
    offset = serializers.IntegerField(required=False, help_text=_("分页偏移量，用于翻页"), default=0, min_value=0)
    template_id = serializers.IntegerField(required=True, help_text=_("流程模板ID，查询指定流程下的决策表"))


class UniFormAPiSerializer(serializers.Serializer):
    """获取统一 API 插件列表序列化器"""

    template_id = serializers.IntegerField(required=True, help_text=_("流程模板ID，查询指定流程下的统一API插件"))


class ServicePluginDetailSerializer(serializers.Serializer):
    """获取第三方插件配置详情序列化器"""

    plugin_code = serializers.CharField(required=False, help_text=_("插件编码，唯一标识插件"), allow_blank=True)
    plugin_version = serializers.CharField(required=False, help_text=_("插件版本号，不指定则返回最新版本"), allow_blank=True)


class AnalysisConstantsRefSerializer(serializers.Serializer):
    """变量引用统计分析序列化器"""

    activities = serializers.JSONField(required=True, help_text=_("活动节点信息，JSON格式，包含流程中的所有活动节点"))
    constants = serializers.JSONField(required=True, help_text=_("常量信息，JSON格式，包含流程中定义的所有变量"))
    gateways = serializers.JSONField(required=True, help_text=_("网关信息，JSON格式，包含流程中的所有分支网关"))


class TemplateDetailQuerySerializer(ScopeSerializer):
    """流程模板详情查询序列化器"""

    with_mock_data = serializers.BooleanField(help_text=_("是否包含 Mock 数据，用于调试和测试"), required=False, default=False)


class TemplateListSerializer(ScopeSerializer):
    """流程模板列表查询序列化器"""

    limit = serializers.IntegerField(required=False, help_text=_("每页数量，最大200条"), default=20, min_value=1, max_value=200)
    offset = serializers.IntegerField(required=False, help_text=_("分页偏移量，用于翻页查询"), default=0, min_value=0)
    name = serializers.CharField(required=False, help_text=_("流程名称，支持模糊匹配"), allow_blank=True)
    creator = serializers.CharField(required=False, help_text=_("创建者用户名，精确匹配"), allow_blank=True)
    updated_by = serializers.CharField(required=False, help_text=_("最后更新人用户名，精确匹配"), allow_blank=True)
    create_at_start = serializers.CharField(
        required=False, help_text=_("创建起始时间，格式: YYYY-MM-DD HH:MM:SS，如 2023-08-25 07:49:45"), allow_blank=True
    )
    create_at_end = serializers.CharField(
        required=False, help_text=_("创建结束时间，格式: YYYY-MM-DD HH:MM:SS，如 2023-08-25 07:49:46"), allow_blank=True
    )
    order_by = serializers.CharField(required=False, help_text=_("排序字段，默认按创建时间排序，如: -created 表示倒序"), allow_blank=True)


class TaskSerializer(ScopeSerializer):
    """流程任务序列化器"""

    task_id = serializers.IntegerField(help_text=_("任务实例ID，唯一标识一个流程任务"), required=True)


class OperateTaskSerializer(TaskSerializer):
    """执行任务操作序列化器"""

    action = serializers.CharField(
        help_text=_("操作类型: start(启动), pause(暂停), resume(继续), revoke(撤销), retry(重试)等"), default="start", required=False
    )


class BatchTaskStatesSerializer(ScopeSerializer):
    """批量查询任务状态序列化器"""

    task_ids = serializers.ListField(
        help_text=_("任务ID列表，批量查询多个任务的状态"),
        required=True,
        child=serializers.IntegerField(required=True, help_text=_("任务实例ID")),
    )


class CheckVariableKeySerializer(serializers.Serializer):
    """检查变量 Key 合法性序列化器"""

    key = serializers.CharField(help_text=_("变量 Key，检查命名是否符合规范（字母开头，支持字母数字下划线）"), required=True)


class GetConstantPreviewResultSerializer(serializers.Serializer):
    """获取常量预览结果序列化器"""

    constants = serializers.JSONField(help_text=_("常量信息，JSON格式，包含需要预览的变量定义"), required=False, default=dict)
    extra_data = serializers.JSONField(help_text=_("预览上下文数据，JSON格式，提供额外的执行环境信息"), required=False, default=dict)


class TaskListSerializer(TemplateListSerializer):
    """流程任务列表查询序列化器"""

    id = serializers.IntegerField(help_text=_("任务实例ID，唯一标识一个流程任务"), required=False)
    executor = serializers.CharField(help_text=_("执行者用户名，精确匹配"), required=False)
    template_id = serializers.IntegerField(help_text=_("流程模板ID，查询指定流程下的任务"), required=False)


class DeleteTemplateSerializer(ScopeSerializer):
    """删除流程模板序列化器"""

    pass


class GetDraftTemplateSerializer(ScopeSerializer):
    """获取草稿流程模板序列化器"""

    pass


class CalculateVersionSerializer(ScopeSerializer):
    """计算版本序列化器"""

    pass


class TemplateReleaseSerializer(ScopeSerializer):
    """模板发布序列化器"""

    version = serializers.CharField(help_text=_("版本号"), required=True)
    desc = serializers.CharField(help_text=_("描述"), required=False, allow_blank=True)


class TemplateRollbackSerializer(ScopeSerializer):
    """模板回滚序列化器"""

    version = serializers.CharField(help_text=_("版本号"), required=True)


class SnapshotSerializer(ScopeSerializer):
    """快照序列化器"""

    template_id = serializers.IntegerField(help_text=_("模板ID"), required=True)


class PreviewTaskTreeSerializer(ScopeSerializer):
    """预览任务树序列化器"""

    appoint_node_ids = serializers.ListSerializer(
        child=serializers.CharField(help_text=_("节点ID")), help_text=_("包含的节点ID列表"), default=[]
    )
    is_all_nodes = serializers.BooleanField(required=False, default=False, help_text=_("preview是否需要过滤节点"))
    version = serializers.CharField(help_text=_("版本号"), required=False)
    is_draft = serializers.BooleanField(help_text=_("是否为草稿"), required=False, default=False)


class BKPluginSerializer(serializers.Serializer):
    """BKPlugin序列化器"""

    code = serializers.CharField(help_text=_("插件编码"), required=False)
    name = serializers.CharField(help_text=_("插件名称"), required=False)
    tag = serializers.IntegerField(help_text=_("插件分类id"), required=False)
    manager = serializers.CharField(help_text=_("管理员"), required=False)
    search_term = serializers.CharField(help_text=_("搜索关键字"), required=False, allow_blank=True)
    limit = serializers.IntegerField(required=False, help_text=_("每页数量，最大200条"), default=20, min_value=1, max_value=200)
    offset = serializers.IntegerField(required=False, help_text=_("分页偏移量，用于翻页查询"), default=0, min_value=0)


class PluginCodeQuerySerializer(serializers.Serializer):
    plugin_code = serializers.CharField(help_text="插件服务编码")
