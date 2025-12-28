from src.hexcalculator.hex import HexValues
from src.hexcalculator.hex import Hex


class HexConverter:
    """
    This class takes a list of hex values in string and returns the base 16 integer
    representation of the combined hex value.
    """

    @staticmethod
    def join_hex_list(hex_list: list[str]) -> str:
        """
        Takes a list of hex values in string format and joins them into a single hex value.

        :param hex_list: List of hex values to combine
        :return: a single hex value
        """
        for value in hex_list:
            result = Hex.is_hex_string(value)  # Validate each hex string
            if not result:
                raise ValueError(f"Invalid hex value: {value}. Expected a valid hex character."
                                 f" Valid characters are: {HexValues.HEX_VALUES.value}")

        combined_hex = "".join(hex_list)
        return f"{HexValues.BASE.value}{combined_hex}"

    def convert_to_int(self, hex_str: str) -> int:
        """
        Converts a list of hex values into a base 16 integer.

        :param hex_str: String representation of hex values to convert
        :return: Integer representation of the combined hex value
        """
        hex_list = list(hex_str)
        combined_hex = self.join_hex_list(hex_list)
        return int(combined_hex, 16)

