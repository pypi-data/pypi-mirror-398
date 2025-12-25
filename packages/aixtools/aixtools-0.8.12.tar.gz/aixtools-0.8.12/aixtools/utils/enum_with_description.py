"""
Enhanced Enum implementation that supports descriptions for enum values.
"""

from enum import Enum


class EnumWithDescription(str, Enum):
    """
    An enum with string values and descriptions.
    Each enum value has a string representation and a description.

    Example:
        class MyEnum(EnumWithDescription):
            VALUE1 = "value1", "This is a description for VALUE1"
            VALUE2 = "value2", "This is a description for VALUE2"
            VALUE3 = "value3", "This is a description for VALUE3"

        print(MyEnum.describe())
        # Output:
        # VALUE1: This is a description for VALUE1
        # VALUE2: This is a description for VALUE2
        # VALUE3: This is a description for VALUE3
    """

    @classmethod
    def describe(cls) -> str:
        """
        Get the description of a decision's enum values
        """
        return "\n".join([f"{field.name}: {field.__doc__}" for field in cls])

    def __new__(cls, value, doc):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.__doc__ = doc
        return obj
