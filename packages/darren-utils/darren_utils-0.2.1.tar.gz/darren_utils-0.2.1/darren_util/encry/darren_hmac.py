import hmac
import hashlib


def hmac_md5(text: str, key: str) -> str:
    """
    HMAC-MD5加密，返回32位小写十六进制字符串

    Args:
        text (str): 要加密的文本
        key (str): 密钥

    Returns:
        str: 32位小写HMAC-MD5值
    """
    return hmac.new(key.encode('utf-8'), text.encode('utf-8'), hashlib.md5).hexdigest()


def hmac_sha1(text: str, key: str) -> str:
    """
    HMAC-SHA1加密，返回40位小写十六进制字符串

    Args:
        text (str): 要加密的文本
        key (str): 密钥

    Returns:
        str: 40位小写HMAC-SHA1值
    """
    return hmac.new(key.encode('utf-8'), text.encode('utf-8'), hashlib.sha1).hexdigest()


def hmac_sha256(text: str, key: str) -> str:
    """
    HMAC-SHA256加密，返回64位小写十六进制字符串

    Args:
        text (str): 要加密的文本
        key (str): 密钥

    Returns:
        str: 64位小写HMAC-SHA256值
    """
    return hmac.new(key.encode('utf-8'), text.encode('utf-8'), hashlib.sha256).hexdigest()


def hmac_sha512(text: str, key: str) -> str:
    """
    HMAC-SHA512加密，返回128位小写十六进制字符串

    Args:
        text (str): 要加密的文本
        key (str): 密钥

    Returns:
        str: 128位小写HMAC-SHA512值
    """
    return hmac.new(key.encode('utf-8'), text.encode('utf-8'), hashlib.sha512).hexdigest()


def hmac_sha3_256(text: str, key: str) -> str:
    """
    HMAC-SHA3-256加密，返回64位小写十六进制字符串

    Args:
        text (str): 要加密的文本
        key (str): 密钥

    Returns:
        str: 64位小写HMAC-SHA3-256值
    """
    return hmac.new(key.encode('utf-8'), text.encode('utf-8'), hashlib.sha3_256).hexdigest()


def hmac_sha3_512(text: str, key: str) -> str:
    """
    HMAC-SHA3-512加密，返回128位小写十六进制字符串

    Args:
        text (str): 要加密的文本
        key (str): 密钥

    Returns:
        str: 128位小写HMAC-SHA3-512值
    """
    return hmac.new(key.encode('utf-8'), text.encode('utf-8'), hashlib.sha3_512).hexdigest()
if __name__ == '__main__':
    # HMAC-MD5
    signature = hmac_md5("data", "secret_key")
    print(signature)

    # HMAC-SHA256
    signature = hmac_sha256("data", "secret_key")
    print(signature)