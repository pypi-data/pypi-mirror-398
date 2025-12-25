from typing import Annotated
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import ValidationInfo
from pydantic import model_validator

from amsdal_utils.models.data_models.core import CLASS_OPENAPI_PARAMETERS_MAPPER
from amsdal_utils.models.data_models.core import DictSchema
from amsdal_utils.models.data_models.core import OptionItemData
from amsdal_utils.models.data_models.core import TypeData
from amsdal_utils.models.data_models.core import get_definition
from amsdal_utils.models.data_models.core import process_any_of
from amsdal_utils.models.data_models.enums import MetaClasses


class PropertyData(TypeData, extra='allow'):
    """
    Schema for property data.

    This class represents the schema for property data, which extends the TypeData class
    and includes additional attributes such as title, options, read-only status, field name,
    field ID, and deletion status.

    Attributes:
        title (str | None): The title of the property.
        options (list[OptionItemData] | None): A list of option item data.
        read_only (bool): Indicates if the property is read-only.
        field_name (str | None): The name of the field.
        field_id (str | None): The ID of the field.
        is_deleted (bool): Indicates if the property is deleted.
    """

    title: str | None = None
    read_only: bool = False
    field_name: str | None = None
    field_id: str | None = None
    is_deleted: bool = False
    discriminator: str | None = None

    @classmethod
    def _format_openapi_parameters(cls, data: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        if '$ref' in data:
            if not info.context:
                msg = 'Context is required to resolve $ref'
                raise ValueError(msg)

            _def = get_definition(info.context, data['$ref'])
            _def['type'] = _def['title']
            data.pop('$ref')
            data.update(_def)

        if 'additionalProperties' in data and isinstance(data['additionalProperties'], dict):
            _add_props = data.pop('additionalProperties')

            if 'anyOf' in _add_props:
                _add_props = process_any_of(_add_props, info)

            items = DictSchema(
                key=TypeData(type='string'),
                value=TypeData(**cls._format_openapi_parameters(_add_props, info)),
            )

            if 'items' not in data:
                data['items'] = items

            if data['type'] == 'object':
                data['type'] = 'dictionary'

        return {CLASS_OPENAPI_PARAMETERS_MAPPER.get(k, k): v for k, v in data.items()}

    @model_validator(mode='before')
    @classmethod
    def format_openapi_parameters(cls, data: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        return cls._format_openapi_parameters(data, info)

    @model_validator(mode='after')
    def validate_options(self) -> 'PropertyData':
        if isinstance(getattr(self, 'enum', None), list) and not self.options:
            _options = []

            x_enum_names: list[str] | None = None
            if hasattr(self, 'x_enum_names'):
                x_enum_names = self.x_enum_names

            for i, item in enumerate(self.enum):  # type: ignore[attr-defined]
                if hasattr(item, '__len__') and not isinstance(item, str):
                    if len(item) > 1:
                        _options.append(OptionItemData(key=str(item[1]), value=item[0]))
                    else:
                        _options.append(OptionItemData(key=str(item[0]), value=item[0]))

                else:
                    _options.append(OptionItemData(key=str(item), value=item))

                if x_enum_names and len(x_enum_names) > i:
                    _options[i].key = x_enum_names[i]

            self.options = _options

        return self


class StorageMetadata(BaseModel, extra='allow'):
    table_name: str | None = Field(default=None, title='Table name')
    db_fields: dict[str, list[str]] | None = Field(default=None, title='Database property to fields mapping')
    primary_key: list[str] | None = Field(default=None, title='Primary key fields')
    indexed: list[list[str]] | None = Field(default=None, title='Indexed')
    unique: list[list[str]] | None = Field(default=None, title='Unique Fields')


class ObjectSchema(BaseModel, extra='allow'):
    r"""
    Schema for an object.

    This class represents the schema for an object, including attributes such as title, type,
    required properties, default value, properties, options, meta class, and custom code.

    Attributes:
        title (Annotated\[str, Field\]): The title of the object, with a minimum length of 1 and a maximum length of 255
        type (str): The type of the object, default is 'object'.
        required (Annotated\[list\[str\], Field\]): A list of required property names.
        default (Any): The default value for the object.
        properties (dict\[str, PropertyData\] | None): A dictionary of property data.
        options (list\[OptionItemData\] | None): A list of option item data.
        meta_class (str): The meta class of the object, default is the value of MetaClasses.CLASS_OBJECT.
        custom_code (str | None): Custom code associated with the object.
        storage_metadata (StorageMetadata | None): Storage metadata associated with the object.
    """

    title: Annotated[str, Field(..., min_length=1, max_length=255)]
    type: str = 'object'
    required: Annotated[list[str], Field(default_factory=list)]
    default: Any = None
    properties: dict[str, PropertyData] | None = None
    options: list[OptionItemData] | None = None
    meta_class: str = MetaClasses.CLASS_OBJECT.value
    custom_code: str | None = None
    storage_metadata: StorageMetadata | None = None

    @model_validator(mode='before')
    @classmethod
    def validated_required(cls, data: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:  # noqa: ARG003
        if 'required' in data and isinstance(data['required'], list):
            _required = data['required']

            if 'properties' in data:
                for _name, _prop in data['properties'].items():
                    if (
                        'anyOf' in _prop
                        and isinstance(_prop['anyOf'], list)
                        and any(any_of == {'type': 'null'} for any_of in _prop['anyOf'])
                        and _name in _required
                    ):
                        _required.remove(_name)

            data['required'] = _required

        return data

    def __hash__(self) -> int:
        return hash(f'{self.title}::{self.type}')
