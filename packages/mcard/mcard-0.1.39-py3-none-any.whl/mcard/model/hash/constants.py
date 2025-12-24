"""Constants related to hash algorithms and operations."""
from mcard.model.hash.enums import HashAlgorithm

# Hash Algorithm Hierarchy - Maps each algorithm to the set of stronger algorithms
HASH_ALGORITHM_HIERARCHY = {
    HashAlgorithm.MD5: {HashAlgorithm.SHA1, HashAlgorithm.SHA224, HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512},
    HashAlgorithm.SHA1: {HashAlgorithm.SHA224, HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512},
    HashAlgorithm.SHA224: {HashAlgorithm.SHA256, HashAlgorithm.SHA384, HashAlgorithm.SHA512},
    HashAlgorithm.SHA256: {HashAlgorithm.SHA384, HashAlgorithm.SHA512},
    HashAlgorithm.SHA384: {HashAlgorithm.SHA512},
    HashAlgorithm.SHA512: set(),
}

# Known MD5 collision pairs for testing
KNOWN_MD5_COLLISION_PAIRS = [
    (
        bytes.fromhex("4dc968ff0ee35c209572d4777b721587d36fa7b21bdc56b74a3dc0783e7b9518afbfa200a8284bf36e8e4b55b35f427593d849676da0d1555d8360fb5f07fea2"),
        bytes.fromhex("4dc968ff0ee35c209572d4777b721587d36fa7b21bdc56b74a3dc0783e7b9518afbfa202a8284bf36e8e4b55b35f427593d849676da0d1d55d8360fb5f07fea2")
    )
]
