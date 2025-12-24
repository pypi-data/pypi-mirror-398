"""
SM3 hash algorithm implementation wrapper
Based on the gmssl library
"""

from gmssl import sm3


def hash_sm3_string(data: str) -> str:
    """
    Calculate SM3 hash of a string
    
    :param data: Input string
    :return: SM3 hash in hexadecimal format
    """
    return sm3.sm3_hash(data.encode('utf-8'))


def hash_sm3_bytes(data: bytes) -> str:
    """
    Calculate SM3 hash of bytes
    
    :param data: Input bytes
    :return: SM3 hash in hexadecimal format
    """
    return sm3.sm3_hash(data)