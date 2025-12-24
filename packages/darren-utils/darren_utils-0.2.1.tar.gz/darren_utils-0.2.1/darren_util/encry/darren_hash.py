import hashlib
import zlib


def hash_md5_string(text):
    """
    MD5加密，返回32位小写十六进制字符串

    Args:
        text (str): 要加密的文本

    Returns:
        str: 32位小写MD5值

    Example:
        >>> hash_md5_string("hello")
        '5d41402abc4b2a76b9719d911017c592'
    """
    md5_hash = hashlib.md5()
    md5_hash.update(text.encode('utf-8'))
    return md5_hash.hexdigest()


def hash_md5_bytes(text: str) -> bytes:
    """
    MD5加密，返回字节格式

    Args:
        text (str): 要加密的文本

    Returns:
        bytes: MD5字节值
    """
    md5_hash = hashlib.md5()
    md5_hash.update(text.encode('utf-8'))
    return md5_hash.digest()


def hash_sha1_string(text: str) -> str:
    """
    SHA1加密，返回40位小写十六进制字符串

    Args:
        text (str): 要加密的文本

    Returns:
        str: 40位小写SHA1值
    """
    sha1_hash = hashlib.sha1()
    sha1_hash.update(text.encode('utf-8'))
    return sha1_hash.hexdigest()


def hash_sha256_string(text: str) -> str:
    """
    SHA256加密，返回64位小写十六进制字符串

    Args:
        text (str): 要加密的文本

    Returns:
        str: 64位小写SHA256值
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(text.encode('utf-8'))
    return sha256_hash.hexdigest()


def hash_sha512_string(text: str) -> str:
    """
    SHA512加密，返回128位小写十六进制字符串

    Args:
        text (str): 要加密的文本

    Returns:
        str: 128位小写SHA512值
    """
    sha512_hash = hashlib.sha512()
    sha512_hash.update(text.encode('utf-8'))
    return sha512_hash.hexdigest()


def hash_sha1_bytes(text: str) -> bytes:
    """
    SHA1加密，返回字节格式

    Args:
        text (str): 要加密的文本

    Returns:
        bytes: SHA1字节值
    """
    sha1_hash = hashlib.sha1()
    sha1_hash.update(text.encode('utf-8'))
    return sha1_hash.digest()


def hash_sha256_bytes(text: str) -> bytes:
    """
    SHA256加密，返回字节格式

    Args:
        text (str): 要加密的文本

    Returns:
        bytes: SHA256字节值
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(text.encode('utf-8'))
    return sha256_hash.digest()


def hash_sha512_bytes(text: str) -> bytes:
    """
    SHA512加密，返回字节格式

    Args:
        text (str): 要加密的文本

    Returns:
        bytes: SHA512字节值
    """
    sha512_hash = hashlib.sha512()
    sha512_hash.update(text.encode('utf-8'))
    return sha512_hash.digest()


def hash_crc32_string(text: str) -> str:
    """
    CRC32校验，返回8位小写十六进制字符串

    Args:
        text (str): 要计算CRC32的文本

    Returns:
        str: 8位小写CRC32值
    """
    crc32_value = zlib.crc32(text.encode('utf-8')) & 0xffffffff
    return format(crc32_value, '08x')


def hash_crc32_int(text: str) -> int:
    """
    CRC32校验，返回整数值

    Args:
        text (str): 要计算CRC32的文本

    Returns:
        int: CRC32整数值
    """
    return zlib.crc32(text.encode('utf-8')) & 0xffffffff
if __name__ == '__main__':
    crc32_hex = hash_crc32_string("1")  # '3610a686'
    crc32_int = hash_crc32_int("hello")  # 906962566
    print(crc32_hex, crc32_int)
