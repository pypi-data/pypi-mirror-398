from datetime import datetime
import time
from typing import Union

from mcard.model.hash.enums import HashAlgorithm

class GTime:
    @staticmethod
    def stamp_now(hash_function: Union[str, HashAlgorithm]) -> str:
        """Get current timestamp in ISO format with hash function and region code."""
        if hash_function is None:
            raise ValueError("hash_function cannot be None")

        # Convert string to HashAlgorithm if needed
        if isinstance(hash_function, str):
            try:
                hash_function = HashAlgorithm(hash_function.lower())
            except ValueError:
                raise ValueError(f"Invalid hash function: {hash_function}")

        region_code = 'UTC'
        return f"{hash_function.value}|{datetime.utcnow().isoformat()}Z|{region_code}"

    @staticmethod
    def get_hash_function(string_value: str) -> HashAlgorithm:
        """Get the hash function from the formatted string."""
        hash_function_str = string_value.split('|')[0].lower()  # Get the part before the first '|'

        try:
            return HashAlgorithm(hash_function_str)
        except ValueError:
            raise ValueError(f"Invalid hash function: {hash_function_str}")

    @staticmethod
    def get_timestamp(string_value: str) -> str:
        """Get the timestamp from the formatted string."""
        return string_value.split('|')[1]

    @staticmethod
    def get_region_code(string_value: str) -> str:
        """Get the region code from the formatted string."""
        return string_value.split('|')[2]

    @staticmethod
    def is_valid_hash_function(hash_function: Union[str, HashAlgorithm]) -> bool:
        """Check if the provided hash function is valid."""
        if isinstance(hash_function, HashAlgorithm):
            return True

        if isinstance(hash_function, str):
            try:
                HashAlgorithm(hash_function.lower())
                return True
            except ValueError:
                return False

        return False

    @staticmethod
    def is_valid_region_code(region_code: str) -> bool:
        """Check if the provided region code is valid."""
        return bool(region_code and region_code.isupper())

    @staticmethod
    def is_iso_format(timestamp: str) -> bool:
        """Check if the provided timestamp is in ISO format."""
        try:
            # Handle Z suffix for UTC (common in JS/ISO8601 but not supported by older python fromisoformat)
            if timestamp.endswith('Z'):
                timestamp = timestamp[:-1] + '+00:00'
            datetime.fromisoformat(timestamp)
            return True
        except ValueError:
            return False
