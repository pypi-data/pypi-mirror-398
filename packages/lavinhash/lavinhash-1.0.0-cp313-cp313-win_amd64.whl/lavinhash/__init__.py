"""LavinHash: High-performance fuzzy hashing library.

Implements the Dual-Layer Adaptive Hashing (DLAH) algorithm for
detecting file and content similarity with extreme efficiency.
"""

from .lavinhash import generate_hash, compare_hashes, compare_data

__all__ = ["generate_hash", "compare_hashes", "compare_data"]
__version__ = "1.0.0"
