from typing import Any
from typing import Union

from pydantic import BaseModel
from pydantic import Field

from amsdal_utils.models.data_models.address import Address


class TableSchema(BaseModel):
    """
    Represents the schema of a table.

    Attributes:
        address (Address): The address of the table.
        columns (list[TableColumnSchema]): The columns of the table.
        indexed (list[TableIndexSchema]): The indexed columns of the table. Defaults to an empty list.
        unique_columns (list[list[str]]): The unique columns of the table. Defaults to an empty list.
    """

    address: Address
    columns: list['TableColumnSchema']
    indexed: list['TableIndexSchema'] = Field(default_factory=list)
    unique_columns: list[list[str]] = Field(default_factory=list)

    def __hash__(self) -> int:
        return hash(self.address.to_string())


class JsonSchemaModel(BaseModel): ...


class NestedSchemaModel(BaseModel):
    """
    Represents a nested schema model.

    Attributes:
        properties (dict[str, Union[NestedSchemaModel, ArraySchemaModel, DictSchemaModel, type[JsonSchemaModel],
         type]]):
            The properties of the nested schema model.
    """

    properties: dict[
        str, Union['NestedSchemaModel', 'ArraySchemaModel', 'DictSchemaModel', type[JsonSchemaModel], type]
    ]


class ArraySchemaModel(BaseModel):
    """
    Represents an array schema model.

    Attributes:
        item_type (Union[ArraySchemaModel, NestedSchemaModel, DictSchemaModel, type[JsonSchemaModel], type]):
            The type of items in the array schema model.
    """

    item_type: Union['ArraySchemaModel', 'NestedSchemaModel', 'DictSchemaModel', type[JsonSchemaModel], type]


class DictSchemaModel(BaseModel):
    """
    Represents a dictionary schema model.

    Attributes:
        key_type (type): The type of keys in the dictionary schema model.
        value_type (Union[DictSchemaModel, NestedSchemaModel, ArraySchemaModel, type[JsonSchemaModel], type]):
            The type of values in the dictionary schema model.
    """

    key_type: type
    value_type: Union['DictSchemaModel', 'NestedSchemaModel', 'ArraySchemaModel', type[JsonSchemaModel], type]


class TableColumnSchema(BaseModel):
    """
    Represents a column schema in a table.

    Attributes:
        name (str): The name of the column.
        field_id (str): The field ID of the column.
        type (type | NestedSchemaModel | ArraySchemaModel | DictSchemaModel | type[JsonSchemaModel]):
            The type of the column.
        default (Any): The default value of the column.
        nullable (bool): Indicates if the column is nullable. Defaults to True.
        is_deleted (bool): Indicates if the column is deleted. Defaults to False.
    """

    name: str
    field_id: str
    type: type | NestedSchemaModel | ArraySchemaModel | DictSchemaModel | type[JsonSchemaModel]
    default: Any
    nullable: bool = True
    is_deleted: bool = False


class TableIndexSchema(BaseModel):
    """
    Represents an index schema for a table.

    Attributes:
        column_name (str): The name of the column that is indexed.
        index_type (str): The type of the index. Defaults to an empty string.
    """

    column_name: str
    index_type: str = ''
