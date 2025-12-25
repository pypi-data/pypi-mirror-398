from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

from amsdal_utils.errors import AmsdalInitiationError
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.utils.singleton import Singleton

if TYPE_CHECKING:
    from amsdal_utils.models.data_models.metadata import Metadata


class MetadataInfoQueryBase(ABC):
    @classmethod
    @abstractmethod
    def get_reference_to(cls, metadata: 'Metadata') -> list['Reference']:
        """
        Get the list of References that the given metadata is referencing to.

        Args:
            metadata (Metadata): The metadata.

        Returns:
            list[Reference]: The list of References that the given metadata is referencing to.
        """

    @classmethod
    @abstractmethod
    def get_referenced_by(cls, metadata: 'Metadata') -> list['Reference']:
        """
        Get the list of References that have reference to the given metadata.

        Args:
            metadata (Metadata): The metadata.

        Returns:
            list[Reference]: The list of References that have reference to the given metadata.
        """


class MetadataInfoManager(metaclass=Singleton):
    def __init__(self) -> None:
        self._metadata_info_query: type[MetadataInfoQueryBase] | None = None

    def register_metadata_info_query(self, metadata_info_query: type[MetadataInfoQueryBase]) -> None:
        """
        Registers a metadata info query class.

        Args:
            metadata_info_query (type[MetadataInfoQueryBase]): The metadata info query class.

        Returns:
            None
        """
        self._metadata_info_query = metadata_info_query

    def get_metadata_info_query(self) -> type[MetadataInfoQueryBase]:
        """
        Gets the registered metadata info query class.

        Returns:
            type[MetadataInfoQueryBase]: The registered metadata info query class.

        Raises:
            AmsdalInitiationError: If no metadata info query class is registered.
        """
        if self._metadata_info_query is None:
            msg = 'MetadataInfoQuery is not registered.'
            raise AmsdalInitiationError(msg)

        return self._metadata_info_query

    def get_reference_to(self, metadata: 'Metadata') -> list['Reference']:
        """
        Gets the list of References that the given metadata is referencing to.

        Args:
            metadata (Metadata): The metadata.

        Returns:
            list[Reference]: The list of References that the given metadata is referencing to.
        """
        return self.get_metadata_info_query().get_reference_to(metadata)

    def get_referenced_by(self, metadata: 'Metadata') -> list['Reference']:
        """
        Gets the list of References that have reference to the given metadata.

        Args:
            metadata (Metadata): The metadata.

        Returns:
            list[Reference]: The list of References that have reference to the given metadata.
        """
        return self.get_metadata_info_query().get_referenced_by(metadata)
