"""Generate randomness without using the random module directly."""

from typing import TYPE_CHECKING

from lazy_bear import LazyLoader

if TYPE_CHECKING:
    import os
    import secrets
else:
    os = LazyLoader("os")
    secrets = LazyLoader("secrets")


def rnd_bits(k: int = 32) -> int:
    """Another way to get random bits."""
    return int.from_bytes(os.urandom(k), "big") % 2**k


def secrets_bits(k: int = 32) -> int:
    """Generate a random seed based on an object's id."""
    return secrets.randbits(k)
