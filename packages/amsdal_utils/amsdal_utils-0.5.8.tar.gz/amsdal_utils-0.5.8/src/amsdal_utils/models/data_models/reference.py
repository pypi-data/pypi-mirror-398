from abc import ABC
from abc import abstractmethod
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from amsdal_utils.models.data_models.address import Address
from amsdal_utils.models.enums import Versions
from amsdal_utils.query.mixin import QueryableMixin
from amsdal_utils.query.mixin import ReferenceableMixin
from amsdal_utils.query.utils import Q
from amsdal_utils.utils.singleton import Singleton


class ReferenceData(Address, validate_assignment=True):
    pass


class Reference(ReferenceableMixin, QueryableMixin, BaseModel, populate_by_name=True):
    """
    Represents a reference to an object/record.

    Attributes:
        ref (ReferenceData): The reference to the object/record.
    """

    ref: ReferenceData = Field(alias='$ref')

    @field_validator('ref', mode='before')
    @classmethod
    def set_address(cls, address: str | ReferenceData | Address | dict[str, str]) -> ReferenceData:
        """
        Validates and sets the address for the reference data.

        Args:
            address (str | Address | dict[str, str]): The address to set. It can be a string, an Address instance,
                or a dictionary.

        Returns:
            ReferenceData: The validated reference data.

        Raises:
            ValueError: If the input is not a valid dictionary or instance of ReferenceData.
            ValueError: If the class version is not provided or is set to Versions.ALL.
            ValueError: If the object version is set to Versions.ALL.
        """
        if isinstance(address, ReferenceData):
            return address

        if isinstance(address, Address):
            ref = ReferenceData.from_string(address.to_string())
        elif isinstance(address, str):
            ref = ReferenceData.from_string(address)
        else:
            try:
                ref = ReferenceData(**address)
            except TypeError as exc:
                msg = 'Input should be a valid dictionary or instance of ReferenceData'
                raise ValueError(msg) from exc

        if not ref.class_version:
            ref.class_version = Versions.LATEST

        if isinstance(ref.class_version, Versions) and ref.class_version == Versions.ALL:
            msg = 'Class version cannot be ALL.'
            raise ValueError(msg)

        if isinstance(ref.object_version, Versions) and ref.object_version == Versions.ALL:
            msg = 'Object version cannot be ALL.'
            raise ValueError(msg)

        if not ref.object_version:
            ref.object_version = Versions.LATEST

        if ref.object_version == Versions.LATEST:
            ref.class_version = Versions.LATEST

        if isinstance(ref.object_id, list) and len(ref.object_id) == 1:
            ref.object_id = ref.object_id[0]

        return ref

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """
        Dumps the model data to a dictionary.

        Args:
            **kwargs (Any): Additional keyword arguments to pass to the model dump.

        Returns:
            dict[str, Any]: A dictionary representation of the model data.
        """
        # we always use Reference with aliased prop $ref
        data = dict(kwargs.items())
        data['by_alias'] = False
        return super().model_dump(**data)

    def to_query(self, prefix: str = '') -> Q:
        """
        Converts the reference data to a query object.
        Args:
            prefix (str): The prefix to use for the query fields. Defaults to an empty string.
        Returns:
            Q: The query object representing the reference data.
        """
        return self.ref.to_query(prefix=f'{prefix}ref__')

    def __hash__(self) -> int:
        return hash(self.ref)

    async def aload(self, only: list[str] | None = None, using: str | None = None) -> Any:
        return await ReferenceLoaderManager().get_reference_loader()(self).aload_reference(only=only, using=using)

    def __await__(self) -> Any:
        return self.aload().__await__()

    def load(self, only: list[str] | None = None, using: str | None = None) -> Any:
        return ReferenceLoaderManager().get_reference_loader()(self).load_reference(only=only, using=using)

    def to_reference(self, *args: Any, **kwargs: Any) -> 'Reference':  # noqa: ARG002
        return self


class ReferenceLoaderBase(ABC):
    def __init__(self, reference: Reference) -> None:
        self._reference = reference

    @abstractmethod
    def load_reference(self, only: list[str] | None = None, using: str | None = None) -> Any:
        pass

    @abstractmethod
    async def aload_reference(self, only: list[str] | None = None, using: str | None = None) -> Any:
        pass


class ReferenceLoaderManager(metaclass=Singleton):
    _reference_loader: type[ReferenceLoaderBase]

    def set_reference_loader(self, reference_loader: type[ReferenceLoaderBase]) -> None:
        self._reference_loader = reference_loader

    def get_reference_loader(self) -> type[ReferenceLoaderBase]:
        return self._reference_loader
