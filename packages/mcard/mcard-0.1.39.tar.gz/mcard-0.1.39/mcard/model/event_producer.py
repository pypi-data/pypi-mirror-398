from typing import Union
import json

from mcard.model.card import MCard
from mcard.config.config_constants import TYPE, HASH, FIRST_G_TIME, CONTENT_SIZE, COLLISION_TIME, UPGRADED_FUNCTION, UPGRADED_HASH, DUPLICATE_TIME, DUPLICATE_EVENT_TYPE, COLLISION_EVENT_TYPE
from mcard.model.hash.enums import HashAlgorithm
from mcard.model.hash.constants import HASH_ALGORITHM_HIERARCHY
from mcard.model.g_time import GTime
from mcard.model.hash.validator import HashValidator


def next_hash_function(current_hash_function: Union[str, HashAlgorithm]) -> str:
    """Get the next hash function in the hierarchy.

    Args:
        current_hash_function: Current hash function name or enum

    Returns:
        str: Name of the next hash function to use
    """
    # Convert enum to string if needed
    if isinstance(current_hash_function, HashAlgorithm):
        current_hash_function = current_hash_function.value
    elif isinstance(current_hash_function, str):
        current_hash_function = current_hash_function.lower()

    # Convert to HashAlgorithm enum
    try:
        current_algo = HashAlgorithm(current_hash_function)
    except ValueError:
        return HashAlgorithm.SHA1.value

    # Get stronger algorithms for current algorithm
    stronger_algos = HASH_ALGORITHM_HIERARCHY.get(current_algo, set())

    # Return the first stronger algorithm, or SHA1 if none exist
    for algo in [HashAlgorithm.SHA1, HashAlgorithm.SHA256, HashAlgorithm.SHA512]:
        if algo in stronger_algos:
            return algo.value

    return HashAlgorithm.SHA1.value


def compute_content_size(card: MCard) -> int:
    """Compute the size of a card's content.

    Args:
        card: The card to compute size for

    Returns:
        int: Size of content in bytes
    """
    return len(card.content)


def generate_collision_event(card: MCard) -> str:
    """Generate a collision event for the given card."""
    next_algo = next_hash_function(GTime.get_hash_function(card.g_time))
    collision_event = {
        TYPE: COLLISION_EVENT_TYPE,
        HASH: str(card.hash),
        FIRST_G_TIME: str(card.g_time),
        COLLISION_TIME: str(card.g_time),
        CONTENT_SIZE: len(card.content),
        UPGRADED_FUNCTION: next_algo,
        UPGRADED_HASH: HashValidator.compute_hash(card.content, next_algo)
    }
    return json.dumps(collision_event)


def generate_duplication_event(card: MCard) -> str:
    """Generate a duplication event for the given card."""
    duplication_event = {
        TYPE: DUPLICATE_EVENT_TYPE,
        HASH: str(card.hash),
        DUPLICATE_TIME: str(card.g_time)
    }
    return json.dumps(duplication_event)
