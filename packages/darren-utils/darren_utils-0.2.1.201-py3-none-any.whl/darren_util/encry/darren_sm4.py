"""
SM4 encryption algorithm implementation wrapper
Based on the gmssl library
"""

import binascii
from gmssl import sm4


class SM4Cipher:
    """
    SM4 encryption/decryption wrapper class
    """

    def __init__(self, key: str, mode: str = 'ECB'):
        """
        Initialize SM4 cipher
        
        :param key: Encryption key (16 bytes)
        :param mode: Encryption mode ('ECB' or 'CBC')
        """
        self.key = key.encode('utf-8') if isinstance(key, str) else key
        self.mode = mode.upper()
        if self.mode not in ['ECB', 'CBC']:
            raise ValueError("Mode must be 'ECB' or 'CBC'")
        self.sm4_crypto = sm4.CryptSM4()

    def encrypt(self, plaintext: str, iv=None) -> str:
        """
        Encrypt plaintext using SM4 algorithm
        
        :param plaintext: Text to encrypt
        :param iv: Initialization vector (required for CBC mode)
        :return: Encrypted ciphertext in hexadecimal format
        """
        data = plaintext.encode('utf-8')
        
        if self.mode == 'ECB':
            self.sm4_crypto.set_key(self.key, sm4.SM4_ENCRYPT)
            encrypted = self.sm4_crypto.crypt_ecb(data)
        elif self.mode == 'CBC':
            if not iv:
                raise ValueError("IV is required for CBC mode")
            iv_bytes = iv.encode('utf-8') if isinstance(iv, str) else iv
            self.sm4_crypto.set_key(self.key, sm4.SM4_ENCRYPT)
            encrypted = self.sm4_crypto.crypt_cbc(iv_bytes, data)
            
        return binascii.b2a_hex(encrypted).decode('utf-8')

    def decrypt(self, ciphertext: str, iv=None) -> str:
        """
        Decrypt ciphertext using SM4 algorithm
        
        :param ciphertext: Ciphertext in hexadecimal format
        :param iv: Initialization vector (required for CBC mode)
        :return: Decrypted plaintext
        """
        data = binascii.a2b_hex(ciphertext)
        
        if self.mode == 'ECB':
            self.sm4_crypto.set_key(self.key, sm4.SM4_DECRYPT)
            decrypted = self.sm4_crypto.crypt_ecb(data)
        elif self.mode == 'CBC':
            if not iv:
                raise ValueError("IV is required for CBC mode")
            iv_bytes = iv.encode('utf-8') if isinstance(iv, str) else iv
            self.sm4_crypto.set_key(self.key, sm4.SM4_DECRYPT)
            decrypted = self.sm4_crypto.crypt_cbc(iv_bytes, data)
            
        return decrypted.decode('utf-8')


def sm4_encrypt_string(plaintext: str, key: str, mode: str = 'ECB', iv=None) -> str:
    """
    Encrypt string using SM4 algorithm
    
    :param plaintext: Text to encrypt
    :param key: Encryption key (16 bytes)
    :param mode: Encryption mode ('ECB' or 'CBC')
    :param iv: Initialization vector (required for CBC mode)
    :return: Encrypted ciphertext in hexadecimal format
    """
    cipher = SM4Cipher(key, mode)
    return cipher.encrypt(plaintext, iv)


def sm4_decrypt_string(ciphertext: str, key: str, mode: str = 'ECB', iv=None) -> str:
    """
    Decrypt string using SM4 algorithm
    
    :param ciphertext: Ciphertext in hexadecimal format
    :param key: Encryption key (16 bytes)
    :param mode: Encryption mode ('ECB' or 'CBC')
    :param iv: Initialization vector (required for CBC mode)
    :return: Decrypted plaintext
    """
    cipher = SM4Cipher(key, mode)
    return cipher.decrypt(ciphertext, iv)


if __name__ == '__main__':
    # 测试SM4 ECB模式
    print("=== SM4 ECB模式测试 ===")
    key = "BC60B8B9E4FFEFFA219E5AD77F11F9E2"  # 16字节密钥
    key = binascii.unhexlify(key)
    plaintext = 'hello'

    # ECB模式加密/解密
    encrypted_ecb = sm4_encrypt_string(plaintext, key, 'ECB')
    print(f"原文: {plaintext}")
    print(f"ECB加密结果: {encrypted_ecb}")

    decrypted_ecb = sm4_decrypt_string(encrypted_ecb, key, 'ECB')
    print(f"ECB解密结果: {decrypted_ecb}")
    print(f"ECB模式测试{'通过' if plaintext == decrypted_ecb else '失败'}")

    # 测试SM4 CBC模式
    print("\n=== SM4 CBC模式测试 ===")
    iv = "fedcba0987654321"  # 16字节IV

    # CBC模式加密/解密
    encrypted_cbc = sm4_encrypt_string(plaintext, key, 'CBC', iv)
    print(f"原文: {plaintext}")
    print(f"CBC加密结果: {encrypted_cbc}")

    decrypted_cbc = sm4_decrypt_string(encrypted_cbc, key, 'CBC', iv)
    print(f"CBC解密结果: {decrypted_cbc}")
    print(f"CBC模式测试{'通过' if plaintext == decrypted_cbc else '失败'}")

    # 测试类的使用方式
    print("\n=== SM4Cipher类使用测试 ===")
    cipher = SM4Cipher(key, 'ECB')
    encrypted = cipher.encrypt(plaintext)
    decrypted = cipher.decrypt(encrypted)
    print(f"类方式加密: {encrypted}")
    print(f"类方式解密: {decrypted}")
    print(f"类方式测试{'通过' if plaintext == decrypted else '失败'}")