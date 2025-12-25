from datetime import date
from datetime import datetime
from enum import Enum
from typing import Any
from typing import Union


class MetaClasses(str, Enum):
    """
    Enumeration for meta classes.

    This enum defines the different types of meta classes used in the application.
    These meta classes categorize objects by their roles within the system.

    Attributes:
        TYPE (str): Represents the 'TypeMeta' class.
        CLASS_OBJECT (str): Represents the 'ClassObject' class.
    """

    TYPE = 'TypeMeta'
    CLASS_OBJECT = 'ClassObject'


class BaseClasses(str, Enum):
    """
    Enumeration for base classes.

    This enum defines the different types of base classes used in the application.
    These base classes categorize objects by their fundamental roles within the system.

    Attributes:
        OBJECT (str): Represents the 'Object' class.
        CLASS_OBJECT (str): Represents the 'ClassObject' class.
        CLASS_OBJECT_META (str): Represents the 'ClassObjectMeta' class.
    """

    OBJECT = 'Object'
    CLASS_OBJECT = 'ClassObject'
    CLASS_OBJECT_META = 'ClassObjectMeta'


class CoreTypes(str, Enum):
    """
    Enumeration of core data types.

    This enum class defines the core data types used in the schema definitions.

    Attributes:
        INTEGER (str): Represents an integer type.
        NUMBER (str): Represents a numeric type.
        STRING (str): Represents a string type.
        BOOLEAN (str): Represents a boolean type.
        DICTIONARY (str): Represents a dictionary type.
        ARRAY (str): Represents an array type.
        ANYTHING (str): Represents any type.
        BINARY (str): Represents a binary type.
        OBJECT (str): Represents an object type.
        DATETIME (str): Represents a datetime type.
        DATE (str): Represents a date type.
    """

    INTEGER = 'integer'
    NUMBER = 'number'
    STRING = 'string'
    BOOLEAN = 'boolean'
    DICTIONARY = 'dictionary'
    ARRAY = 'array'
    ANYTHING = 'anything'
    BINARY = 'binary'
    OBJECT = 'object'
    DATETIME = 'datetime'
    DATE = 'date'

    @classmethod
    def from_python_type(cls, python_type: Any) -> 'CoreTypes':
        """
        Converts a Python type to a CoreTypes enum value.

        Args:
            python_type (Any): The Python type to convert.

        Returns:
            CoreTypes: The CoreTypes enum value that corresponds to the given Python type.
        """
        if python_type is int:
            return cls.INTEGER
        if python_type is float:
            return cls.NUMBER
        if python_type is str:
            return cls.STRING
        if python_type is bool:
            return cls.BOOLEAN
        if python_type is dict:
            return cls.DICTIONARY
        if python_type is list:
            return cls.ARRAY
        if python_type is bytes:
            return cls.BINARY
        if python_type is datetime:
            return cls.DATETIME
        if python_type is date:
            return cls.DATE
        return cls.ANYTHING

    @classmethod
    def to_python_type(cls, internal_type: Union['CoreTypes', str]) -> type | Any:
        """
        Converts a CoreTypes enum value to a Python type.

        Args:
            internal_type (str | CoreTypes): The CoreTypes enum value to convert.

        Returns:
            type: The Python type that corresponds to the given CoreTypes enum value.
        """
        if not isinstance(internal_type, CoreTypes):
            internal_type = CoreTypes(internal_type)

        if internal_type == cls.INTEGER:
            return int
        if internal_type == cls.NUMBER:
            return float
        if internal_type == cls.STRING:
            return str
        if internal_type == cls.BOOLEAN:
            return bool
        if internal_type == cls.DICTIONARY:
            return dict
        if internal_type == cls.ARRAY:
            return list
        if internal_type == cls.BINARY:
            return bytes
        if internal_type == cls.DATETIME:
            return datetime
        if internal_type == cls.DATE:
            return date
        return Any
