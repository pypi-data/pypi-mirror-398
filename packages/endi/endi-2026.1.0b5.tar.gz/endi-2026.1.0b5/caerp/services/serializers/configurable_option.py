from caerp.consts.permissions import PERMISSIONS
from caerp.services.serializers.base import BaseSerializer
from caerp.services.task.mentions import company_task_mention_is_used


class ConfigurableOptionSerializer(BaseSerializer):
    pass


class CompanyTaskMentionSerializer(ConfigurableOptionSerializer):
    acl = {
        "__all__": (
            PERMISSIONS["context.edit_company_task_mention"],
            PERMISSIONS["context.edit_company"],
        ),
        "company": (
            PERMISSIONS["context.edit_company_task_mention"],
            PERMISSIONS["context.edit_company"],
        ),
    }
    exclude_from_children = ("company_task_mentions",)

    def get_is_used(self, request, item, field_name):
        return company_task_mention_is_used(request, item.id)
