import time
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import PrivateAttr

from amsdal_utils.classes.metadata_manager import MetadataInfoManager
from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.enums import Versions
from amsdal_utils.utils.lazy_object import LazyInstanceObject


class Metadata(BaseModel):
    _reference_to: LazyInstanceObject['Metadata', list[Reference]] = PrivateAttr(
        LazyInstanceObject(lambda metadata: MetadataInfoManager().get_reference_to(metadata))
    )
    _referenced_by: LazyInstanceObject['Metadata', list[Reference]] = PrivateAttr(
        LazyInstanceObject(lambda metadata: MetadataInfoManager().get_referenced_by(metadata))
    )
    _next_version: str | None = PrivateAttr(None)

    object_id: Any
    object_version: str | Versions
    class_schema_reference: Reference
    class_meta_schema_reference: Reference | None = None
    transaction: Reference | None = None
    is_deleted: bool = False
    prior_version: str | None = None
    created_at: int = Field(default_factory=lambda: round(time.time() * 1000))
    updated_at: int = Field(default_factory=lambda: round(time.time() * 1000))

    def __init__(self, /, **data: Any) -> None:
        _next_version = data.pop('_next_version', None)
        super().__init__(**data)
        self._next_version = _next_version

    @property
    def next_version(self) -> str | None:
        return self._next_version

    @property
    def address(self) -> Address:
        from amsdal_utils.config.manager import AmsdalConfigManager  # noqa: PLC0415

        _class_name = self.class_schema_reference.ref.object_id

        return Address(
            resource=AmsdalConfigManager().get_connection_name_by_model_name(_class_name),  # type: ignore[arg-type]
            class_name=_class_name,  # type: ignore[arg-type]
            class_version=self.class_schema_reference.ref.object_version,
            object_id=self.object_id,
            object_version=self.object_version,
        )

    @property
    def is_latest(self) -> bool:
        """
        Flag to indicate if the object/record is the latest version.

        Returns:
            bool: True if the object/record is the latest version, False otherwise.
        """
        return self.next_version is None

    @property
    def reference_to(self) -> list[Reference]:
        """
        The list of references to other objects/records.

        Returns:
            list[Reference]: The list of references to other objects/records.
        """
        return self._reference_to.value(self)

    @property
    def referenced_by(self) -> list[Reference]:
        """
        The list of references from other objects/records.

        Returns:
            list[Reference]: The list of references from other objects/records.
        """
        return self._referenced_by.value(self)
