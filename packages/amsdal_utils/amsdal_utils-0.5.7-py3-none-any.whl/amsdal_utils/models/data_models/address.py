import base64
import json
from collections.abc import Callable
from datetime import date
from datetime import datetime
from datetime import time
from decimal import Decimal
from typing import Any
from typing import Self
from typing import TypeAlias

from pydantic import BaseModel
from pydantic import field_validator

from amsdal_utils.models.enums import Versions
from amsdal_utils.query.utils import Q

AddressType: TypeAlias = 'Address'
ObjectIDType: TypeAlias = Any | tuple[Any, ...]

RESOURCE_DELIMITER = '#'
ADDRESS_PARTS_DELIMITER = ':'


class JSONExtendedEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle additional types."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (Decimal, datetime, date, time, bytes)):
            return {
                '__type__': type(obj).__name__,
                'value': base64.b64encode(obj).decode('utf-8') if isinstance(obj, bytes) else str(obj),
            }
        return super().default(obj)


class AddressEncoder:
    @staticmethod
    def encode(object_id: Any) -> str:
        """Encode object ID to base64 JSON string."""
        return base64.b64encode(json.dumps(object_id, cls=JSONExtendedEncoder).encode('utf-8')).decode('utf-8')

    @classmethod
    def decode(cls, encoded_id: str) -> Any:
        """Decode base64 JSON string to original object."""
        if not encoded_id:
            return ''

        try:
            decoded_binary = base64.b64decode(encoded_id.encode('utf-8'))
            return json.loads(decoded_binary, object_hook=cls._object_hook)
        except Exception:
            # fallback for the old address format
            return encoded_id

    @staticmethod
    def _object_hook(dct: dict[str, Any]) -> Any:
        if '__type__' in dct:
            type_name = dct['__type__']
            value = dct['value']

            type_mapping: dict[str, Callable[[str], Any]] = {
                'Decimal': Decimal,
                'datetime': datetime.fromisoformat,
                'date': date.fromisoformat,
                'time': time.fromisoformat,
                'bytes': lambda x: base64.b64decode(x.encode('utf-8')),
            }

            return type_mapping.get(type_name, str)(value)
        return dct


class Address(BaseModel):
    """
    Represents a resource address with flexible identification.

    Attributes:
        resource (str): The resource/connection name.
        class_name (str): The class name.
        class_version (Versions | str): The class specific version or LATEST/ALL.
        object_id (ObjectIDType): The object id. Can be either a single value or list of values in case of compound PK
        object_version (Versions | str): The object specific version or LATEST/ALL.
    """

    resource: str
    class_name: str
    class_version: Versions | str
    object_id: ObjectIDType
    object_version: Versions | str

    @classmethod
    def from_string(cls, address: str) -> Self:
        """
        Creates an Address instance from a string representation.

        Args:
            cls (type[AddressType]): The class type.
            address (str): The string representation of the address.

        Returns:
            AddressType: The Address instance created from the string.

        Raises:
            ValueError: If the resource name is not specified in the address.
        """
        if RESOURCE_DELIMITER not in address:
            msg = f'Resource name is not specified for this address: "{address}".'
            raise ValueError(msg)

        resource, components = address.split(RESOURCE_DELIMITER, 1)
        components_dict = dict(enumerate(components.split(ADDRESS_PARTS_DELIMITER)))
        object_id = components_dict.get(2, '')

        return cls(
            resource=resource,
            class_name=components_dict.get(0, ''),
            class_version=components_dict.get(1, ''),
            object_id=AddressEncoder.decode(object_id),
            object_version=components_dict.get(3, ''),
        )

    def to_string(self) -> str:
        """
        Convert Address instance to string representation.

        Returns:
            String representation of the address
        """

        encoded_object_id = AddressEncoder.encode(self.object_id)

        parts = [str(self.class_name), str(self.class_version), encoded_object_id, str(self.object_version)]

        return f'{self.resource}{RESOURCE_DELIMITER}{ADDRESS_PARTS_DELIMITER.join(parts)}'

    @field_validator('class_version', 'object_version', mode='before')
    @classmethod
    def validate_version(cls, version: str | Versions) -> str | Versions:
        """
        Validate and convert version to Versions enum if possible.

        Args:
            version: Version to validate

        Returns:
            Validated version
        """
        if isinstance(version, str):
            try:
                return Versions(version)
            except ValueError:
                pass
        return version

    @property
    def is_complete(self) -> bool:
        """
        Check if the address is fully specified.

        Returns:
            Whether all address components are specified
        """
        return all(
            element and not isinstance(element, Versions)
            for element in [
                self.class_name,
                self.class_version,
                self.object_id,
                self.object_version,
            ]
        )

    @property
    def is_full(self) -> bool:
        """
        Deprecated, use is_complete instead.
        """
        return self.is_complete

    def to_query(self, prefix: str = '') -> Q:
        """
        Converts the Address instance to a query.
        Args:
            prefix (str, optional): The prefix for the query fields. Defaults to ''.
        Returns:
            Q: The query object.
        """
        object_id_q = Q(**{f'{prefix}object_id': self.object_id})

        if self.object_version == Versions.LATEST:
            object_id_q &= Q(**{f'{prefix}object_version': 'LATEST'}) | Q(**{f'{prefix}object_version': ''})
        elif self.object_version != Versions.ALL:
            object_id_q &= Q(**{f'{prefix}object_version': self.object_version})
        return object_id_q

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return self.to_string()

    def __hash__(self) -> int:
        return hash(self.to_string())

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Address) and self.to_string() == other.to_string()
