from typing import Union

from caerp.consts.permissions import PERMISSIONS
from caerp.models.project.types import BusinessType, ProjectType


def base_project_type_allowed(
    request, data_type: Union[ProjectType, BusinessType]
) -> bool:
    res = False
    if not data_type.private:
        res = True
    elif data_type.name and request.has_permission(
        PERMISSIONS[f"context.add_{data_type.name}"]
    ):
        res = True
    return res
