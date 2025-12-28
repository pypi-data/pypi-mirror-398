from enum import Enum
from typing import Union


class HexValues(Enum):
    BASE = "0x"
    HEX_VALUES = ['A', 'B', 'C', 'D', 'E', 'F']


class Hex:

    @staticmethod
    def is_hex_string(value: str) -> bool:
        """
        Takes in a string and checks to see if it is a valid hex string.

        :param value: The value to check.
        :return: True if the value is a valid hex value, False otherwise.
        """
        if not isinstance(value, str):
            raise ValueError(f"Expected an str or int, got {type(value)}")

        if value.upper() not in [item for item in HexValues.HEX_VALUES.value]:
            return False
        else:
            return True


if __name__ == "__main__":
    # Example usage
    hex_value = "a"
    print(Hex.is_hex_string(hex_value))  # Should print True
