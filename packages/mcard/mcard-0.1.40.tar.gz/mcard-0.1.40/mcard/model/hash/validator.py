import hashlib
from typing import Union
import logging
from mcard.model.hash.enums import HashAlgorithm

logger = logging.getLogger(__name__)


class HashValidator:
    """Validates and computes hash values for content."""
    def __init__(self, content: Union[str, bytes], hash_algorithm: Union[str, HashAlgorithm] = HashAlgorithm.DEFAULT):
        self.content = content
        self.hash_algorithm = hash_algorithm
        self.hash_value = self.compute_hash(content, hash_algorithm)

    @staticmethod
    def compute_hash(content: Union[str, bytes], hash_algorithm: Union[str, HashAlgorithm] = HashAlgorithm.DEFAULT) -> str:
        """Compute hash for given content using specified hash function"""
        content_to_hash = content if isinstance(content, bytes) else content.encode()

        # Convert string input to HashAlgorithm if needed
        if isinstance(hash_algorithm, str):
            try:
                hash_algorithm = HashAlgorithm(hash_algorithm.lower())
            except ValueError:
                raise ValueError(f"'{hash_algorithm}' is not a valid HashAlgorithm")

        hash_functions = {
            HashAlgorithm.MD5: hashlib.md5,
            HashAlgorithm.SHA1: hashlib.sha1,
            HashAlgorithm.SHA224: hashlib.sha224,
            HashAlgorithm.SHA256: hashlib.sha256,
            HashAlgorithm.SHA384: hashlib.sha384,
            HashAlgorithm.SHA512: hashlib.sha512
        }

        if hash_algorithm == HashAlgorithm.CUSTOM:
            raise ValueError("Custom hash function must be provided when using CUSTOM algorithm")

        if hash_algorithm not in hash_functions:
            raise ValueError(f"'{hash_algorithm}' is not a valid HashAlgorithm")

        return hash_functions[hash_algorithm](content_to_hash).hexdigest()

    def validate(self, expected_hash: str = None):
        """Validate that the stored hash matches the expected hash"""
        if expected_hash is not None:
            self.hash_value = expected_hash
        calculated_hash = self.compute_hash(self.content, self.hash_algorithm)
        logger.debug(f"Validating hash: expected '{self.hash_value}', calculated '{calculated_hash}'")
        logger.debug(f"Hash calculation details: content='{self.content}', hash_function='{self.hash_algorithm}'")
        if calculated_hash != self.hash_value:
            raise ValueError(f"Hash mismatch: expected '{self.hash_value}', got '{calculated_hash}'")

    def __str__(self):
        return self.hash_value
