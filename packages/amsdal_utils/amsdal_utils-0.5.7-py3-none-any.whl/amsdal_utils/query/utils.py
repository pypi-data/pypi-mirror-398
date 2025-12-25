from enum import Enum
from typing import Any
from typing import Union

from amsdal_utils.query.data_models.filter import Filter


class ConnectorEnum(str, Enum):
    """
    Enumeration for logical connectors used in queries.

    Attributes:
        AND (str): Logical AND connector.
        OR (str): Logical OR connector.
    """

    AND = 'AND'
    OR = 'OR'


class Q:
    """
    Q objects allow you to build complex queries.

    Example usage:

        ```python
        Q(age__gt=15) & Q(name__icontains='e') & Q(name='John', age=18)
        Q(Q(age__gt=15) & Q(name__icontains='e')) | Q(name='John', age=18)
        ```
    """

    def __init__(self, *args: Union['Q', Filter], **kwargs: Any) -> None:
        self.connector: ConnectorEnum = kwargs.pop('connector', ConnectorEnum.AND)
        self.negated = kwargs.pop('negated', False)
        self.children: list[Q | Filter] = [
            *args,
            *[Filter.build(selector=selector, value=value) for selector, value in sorted(kwargs.items())],
        ]

    def __and__(self, other: 'Q') -> 'Q':
        return self._combine(other, ConnectorEnum.AND)

    def __or__(self, other: 'Q') -> 'Q':
        return self._combine(other, ConnectorEnum.OR)

    def __invert__(self) -> 'Q':
        q_obj = self.__copy__()
        q_obj._negate()

        return q_obj

    def __copy__(self) -> 'Q':
        return self.__class__(*self.children, connector=self.connector, negated=self.negated)

    def _combine(self, other: 'Q', connector: ConnectorEnum) -> 'Q':
        if not isinstance(other, Q):
            raise TypeError(other)

        obj = self.__class__(connector=connector)
        obj.children = [self, other]

        return obj

    def _negate(self) -> None:
        self.negated = not self.negated

    def __repr__(self) -> str:
        return f'<Q: {self.children}, c={self.connector.value}, n={self.negated}>'

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Q):
            return False

        return (
            self.children == __value.children
            and self.connector == __value.connector
            and self.negated == __value.negated
        )

    def __hash__(self) -> int:
        return hash((self.connector, self.negated, tuple(self.children)))
