"""
nrhgen - Generate cryptographic hashes (MD5, SHA1, SHA256)
"""

__version__ = "0.1.0"

from .hasher import hash_text, hash_file, SUPPORTED_ALGOS

__all__ = ["hash_text", "hash_file", "SUPPORTED_ALGOS"]

