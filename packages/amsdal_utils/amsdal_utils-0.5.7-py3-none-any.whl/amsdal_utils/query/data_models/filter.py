from typing import Any

from pydantic import BaseModel

from amsdal_utils.query.enums import Lookup


class Filter(BaseModel):
    """
    Represents a filter for querying data.

    Attributes:
        field_name (str): The name of the field to filter.
        lookup (Lookup): The lookup operation to use for filtering. Defaults to Lookup.EQ.
        value (Any): The value to filter by.
    """

    field_name: str
    lookup: Lookup = Lookup.EQ
    value: Any

    @classmethod
    def build(cls, selector: str, value: Any) -> 'Filter':
        """
        Builds a Filter object from a selector and value.

        Args:
            selector (str): The selector string to parse.
            value (Any): The value to filter by.

        Returns:
            Filter: The constructed Filter object.
        """
        field_name, lookup = cls.parse_selector(selector)

        return cls(field_name=field_name, lookup=lookup, value=value)

    @classmethod
    def parse_selector(cls, selector: str) -> tuple[str, Lookup]:
        """
        Parses a selector string into a field name and lookup operation.

        Args:
            selector (str): The selector string to parse.

        Returns:
            tuple[str, Lookup]: A tuple containing the field name and the lookup operation.
        """
        if '__' not in selector:
            return selector, Lookup.EQ

        field_name, lookup = selector.rsplit('__', 1)

        try:
            return field_name, Lookup(lookup)
        except ValueError:
            return selector, Lookup.EQ

    @property
    def is_nested_selection(self) -> bool:
        """
        Checks if the field name indicates a nested selection.

        Returns:
            bool: True if the field name contains a nested selection, False otherwise.
        """
        return '__' in self.field_name

    def __str__(self) -> str:
        return f'Filter(field_name={self.field_name}, lookup={self.lookup.value}, value={self.value})'

    def __repr__(self) -> str:
        return self.__str__()
