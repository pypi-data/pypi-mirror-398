from typing import Any
from typing import Union

from pydantic import BaseModel
from pydantic import ValidationInfo
from pydantic import model_validator
from pydantic.json_schema import GenerateJsonSchema
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import PydanticCustomError


class AmsdalGenerateJsonSchema(GenerateJsonSchema):
    def enum_schema(self, schema) -> JsonSchemaValue:  # type: ignore[no-untyped-def]
        result = super().enum_schema(schema)
        result['x_enum_names'] = [member.name for member in schema['members']]
        return result


def get_definition(defs: dict[str, Any], ref: str) -> Any:
    for _ref in ref.split('/')[1:]:
        try:
            defs = defs[_ref]
        except KeyError:
            defs = defs[_ref.lower()]

    return defs


CLASS_OPENAPI_PARAMETERS_MAPPER = {
    'minLength': 'min_length',
    'maxLength': 'max_length',
    'exclusiveMinimum': 'exclusive_minimum',
    'exclusiveMaximum': 'exclusive_maximum',
    'multipleOf': 'multiple_of',
}


class OptionItemData(BaseModel):
    key: str
    value: Any


class DictSchema(BaseModel):
    """
    Schema for a dictionary type.

    This class represents the schema for a dictionary type, where the keys and values
    are defined by the `TypeData` class.

    Attributes:
        key (TypeData): The schema for the dictionary keys.
        value (TypeData): The schema for the dictionary values.
    """

    key: 'TypeData'
    value: 'TypeData'


class LegacyDictSchema(BaseModel):
    """
    Schema for a legacy dictionary type.

    This class represents the schema for a legacy dictionary type, where the key and value types
    are defined as strings.

    Attributes:
        key_type (str): The type of the dictionary keys.
        value_type (str): The type of the dictionary values.
    """

    key_type: str
    value_type: str


def process_one_of(data: dict[str, Any]) -> dict[str, Any]:
    one_of = [
        ao
        for ao in data.pop('oneOf')
        if ao not in [{'type': 'null'}, {'$ref': '#/$defs/Reference'}, {'$ref': '#/$defs/LegacyModel'}]
    ]

    for _one_of_item in one_of:
        if not _one_of_item or '$ref' not in _one_of_item:
            msg = f'Multiple oneOf should contain $ref. Currently: {one_of}'
            raise ValueError(msg)

    _types = [_one_of_item['$ref'].rsplit('/', 1)[-1] for _one_of_item in one_of]
    data['type'] = '|'.join(_types)

    return data


def process_any_of(data: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
    from amsdal_utils.schemas.schema import PropertyData  # noqa: PLC0415

    _any_of = data.pop('anyOf')
    if _any_of in [[{'$ref': '#/$defs/Reference'}], [{'$ref': '#/$defs/Reference'}, {'type': 'null'}]]:
        data['type'] = 'object'
        return data

    any_of = [
        ao
        for ao in _any_of
        if ao not in [{'type': 'null'}, {'$ref': '#/$defs/Reference'}, {'$ref': '#/$defs/LegacyModel'}]
    ]

    if len(any_of) != 1:
        for _any_of_item in any_of:
            if not _any_of_item or '$ref' not in _any_of_item:
                msg = f'Multiple anyOf should contain $ref. Currently: {any_of}'
                raise ValueError(msg)
        _types = [_any_of_item['$ref'].rsplit('/', 1)[-1] for _any_of_item in any_of]

        data['type'] = '|'.join(_types)

    _any_of_element = any_of[0]

    if _any_of_element == {}:
        data['type'] = 'object'
    elif '$ref' in _any_of_element:
        if not info.context:
            msg = 'Context is required to resolve $ref'
            raise ValueError(msg)

        definition = get_definition(info.context, _any_of_element['$ref']).copy()
        if definition['type'] == 'object':
            definition['type'] = definition['title']

        definition.update(data)
        data = definition

    elif 'additionalProperties' in _any_of_element and isinstance(_any_of_element['additionalProperties'], dict):
        _add_props = _any_of_element.pop('additionalProperties')

        if 'anyOf' in _add_props:
            _add_props = process_any_of(_add_props, info)

        _type = _add_props.get('type', 'object')

        if 'items' not in data:
            data['items'] = DictSchema(
                key=TypeData(type='string'),
                value=TypeData(**PropertyData._format_openapi_parameters(_add_props, info)),
            )

        if _any_of_element['type'] == 'object':
            data['type'] = 'dictionary'

    else:
        data['type'] = _any_of_element['type']

        if 'format' in _any_of_element:
            data['format'] = _any_of_element['format']

        if 'items' in any_of[0]:
            data['items'] = any_of[0]['items']

            if '$ref' in data['items']:
                if not info.context:
                    msg = 'Context is required to resolve $ref'
                    raise ValueError(msg)

                definition = get_definition(info.context, data['items']['$ref']).copy()
                definition['type'] = definition['title']

                data['items'] = definition

    return data


class TypeData(BaseModel, extra='allow'):
    """
    Schema for type data.

    This class represents the schema for type data, which includes the type, items,
    and default value.

    Attributes:
        type (str): The type of the data.
        items (Union[TypeData, DictSchema, LegacyDictSchema] | None): The items contained within the type data,
            which can be another TypeData, DictSchema, or LegacyDictSchema instance.
        default (Any): The default value for the type data.
    """

    type: str
    items: Union['TypeData', DictSchema, LegacyDictSchema] | None = None
    default: Any = None
    options: list[OptionItemData] | None = None

    @model_validator(mode='before')
    @classmethod
    def check_any_of(cls, data: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        if '$ref' in data:
            if not info.context:
                msg = 'Context is required to resolve $ref'
                raise ValueError(msg)

            _def = get_definition(info.context, data['$ref'])
            _def['type'] = _def['title']
            data.pop('$ref')
            data.update(_def)

        if not isinstance(data, dict):
            err_type = 'invalid_data'
            raise PydanticCustomError(err_type, 'Data must be a dictionary')

        if 'type' in data and 'anyOf' in data:
            err_type = 'invalid_data'
            raise PydanticCustomError(err_type, 'Data cannot have both "type" and "anyOf" keys')

        if 'anyOf' in data:
            data = process_any_of(data, info)

        if 'oneOf' in data:
            data = process_one_of(data)

        if 'discriminator' in data and isinstance(data['discriminator'], dict):
            try:
                data['discriminator'] = data['discriminator']['propertyName']
            except:
                raise

        if 'type' not in data:
            data['type'] = 'object'

        return data

    @model_validator(mode='after')
    def validate_final_types(self) -> 'TypeData':
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

        if hasattr(self, 'format'):
            if self.type == 'string':
                if self.format == 'date-time':
                    self.type = 'datetime'

                if self.format == 'date':
                    self.type = 'date'

                if self.format in ['binary', 'byte']:
                    self.type = 'binary'
                    delattr(self, 'format')

        if self.type == 'object' and self.items is None:
            self.type = 'anything'

        if self.type != 'object':
            for model_props in ['properties', 'required']:
                if hasattr(self, model_props):
                    delattr(self, model_props)

        return self
