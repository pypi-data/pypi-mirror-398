from typing import Any

from amsdal_utils.config.manager import AmsdalConfigManager
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.data_models.reference import ReferenceData
from amsdal_utils.models.enums import Versions


def build_reference(
    class_name: str,
    object_id: Any,
    class_version: str | Versions = Versions.LATEST,
    object_version: str | Versions = Versions.LATEST,
    resource: str | None = None,
) -> Reference:
    """
    Builds a reference object.

    Args:
        class_name (str): The name of the class.
        object_id (Any): The ID of the object.
        class_version (str | Versions, optional): The version of the class. Defaults to Versions.LATEST.
        object_version (str | Versions, optional): The version of the object. Defaults to Versions.LATEST.
        resource (str | None, optional): The resource name. Defaults to None.

    Returns:
        Reference: The constructed reference object.
    """
    connection_name = resource or AmsdalConfigManager().get_connection_name_by_model_name(class_name)

    if isinstance(object_id, list) and len(object_id) == 1:
        object_id = object_id[0]

    return Reference(
        ref=ReferenceData(
            resource=connection_name,
            class_name=class_name,
            class_version=class_version,
            object_id=object_id,
            object_version=object_version,
        ),
    )
