from abc import abstractmethod

from pydantic import BaseModel

from amsdal_utils.models.data_models.metadata import Metadata
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.query.mixin import QueryableMixin
from amsdal_utils.query.mixin import ReferenceableMixin
from amsdal_utils.query.utils import Q


class ModelBase(ReferenceableMixin, QueryableMixin, BaseModel):  # pragma: no cover
    @abstractmethod
    def get_metadata(self) -> Metadata:
        """
        Retrieves the metadata for the model.

        Returns:
            Metadata: The metadata associated with the model.
        """
        ...

    @abstractmethod
    def build_reference(self, *, is_frozen: bool = False) -> Reference:
        """
        Builds a reference object from the model.
        If the flag is_frozen is set to True, the reference object will be pinned to specific versions

        Args:
            is_frozen (bool): Whether to pin the reference to specific versions. Defaults to False.
        """
        ...

    def to_query(self, prefix: str = '', *, force_frozen: bool = False) -> Q:
        """
        Converts the model metadata to a query object.

        Args:
            prefix (str): The prefix to use for the query. Defaults to an empty string.
            force_frozen (bool): Whether to force the query to be frozen. Defaults to False.

        Returns:
            Q: The query object.
        """
        reference = self.build_reference(is_frozen=force_frozen)

        return reference.to_query(prefix=prefix)

    def to_reference(self) -> Reference:
        return self.build_reference()
