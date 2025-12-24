"""Hash algorithm enums."""
from enum import Enum

class HashAlgorithm(Enum):
    """Supported hash algorithms."""
    MD5 = "md5"
    SHA1 = "sha1"
    SHA224 = "sha224"
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"
    CUSTOM = "custom"

    # Default hash algorithm
    DEFAULT = SHA256

    @classmethod
    def from_string(cls, value: str) -> 'HashAlgorithm':
        """Convert a string to a HashAlgorithm enum.
        
        Args:
            value: String value to convert
            
        Returns:
            HashAlgorithm: The corresponding enum value
            
        Raises:
            ValueError: If the string is not a valid hash algorithm
        """
        try:
            return cls(value.lower())
        except ValueError:
            raise ValueError(f"'{value}' is not a valid hash algorithm")

    @classmethod
    def get_default(cls) -> 'HashAlgorithm':
        """Get the default hash algorithm from environment or fallback to SHA1."""
        from mcard.config.settings import settings
        env_algo = settings.hashing.algorithm
        if env_algo is None:
            return cls.DEFAULT
        try:
            return cls.from_string(env_algo)
        except ValueError:
            raise ValueError(f"Invalid hash algorithm in environment: {env_algo}")
