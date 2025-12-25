from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any

from amsdal_utils.query.utils import Q

if TYPE_CHECKING:
    from amsdal_utils.models.data_models.reference import Reference


class QueryableMixin(ABC):
    @abstractmethod
    def to_query(self, *args: Any, **kwargs: Any) -> Q: ...


class ReferenceableMixin(ABC):
    @abstractmethod
    def to_reference(self, *args: Any, **kwargs: Any) -> 'Reference': ...
