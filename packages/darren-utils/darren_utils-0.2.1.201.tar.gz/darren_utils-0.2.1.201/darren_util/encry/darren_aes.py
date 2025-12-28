# aes.py
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import os


class AESCipher:
    """
    AES加密解密类，支持多种模式和填充方式
    """

    def __init__(self, key: bytes, mode: str = 'CBC', padding_mode: str = 'PKCS7'):
        """
        初始化AES加密器

        Args:
            key (bytes): 密钥（16, 24, 或 32字节对应AES-128, AES-192, AES-256）
            mode (str): 加密模式 ('ECB', 'CBC', 'CFB', 'OFB')
            padding_mode (str): 填充模式 ('PKCS7', 'ISO7816', 'ANSIX923')
        """
        self.key = key
        self.mode = mode.upper()
        self.padding_mode = padding_mode.upper()
        self.backend = default_backend()

        # 验证密钥长度
        if len(key) not in [16, 24, 32]:
            raise ValueError("密钥长度必须为16, 24, 或 32字节")

    def _get_padding(self, block_size: int = 128):
        """获取填充器"""
        if self.padding_mode == 'PKCS7':
            return padding.PKCS7(block_size)
        elif self.padding_mode == 'ISO7816':
            return padding.ISO7816(block_size)
        elif self.padding_mode == 'ANSIX923':
            return padding.ANSIX923(block_size)
        else:
            raise ValueError(f"不支持的填充模式: {self.padding_mode}")

    def _pad_data(self, data: bytes) -> bytes:
        """数据填充"""
        if self.mode in ['ECB', 'CBC']:
            padder = self._get_padding().padder()
            return padder.update(data) + padder.finalize()
        return data

    def _unpad_data(self, data: bytes) -> bytes:
        """去除填充"""
        if self.mode in ['ECB', 'CBC']:
            unpadder = self._get_padding().unpadder()
            return unpadder.update(data) + unpadder.finalize()
        return data

    def _get_cipher(self, iv: bytes = None):
        """获取加密器"""
        algorithm = algorithms.AES(self.key)

        if self.mode == 'ECB':
            mode_obj = modes.ECB()
        elif self.mode == 'CBC':
            if iv is None:
                iv = os.urandom(16)
            mode_obj = modes.CBC(iv)
        elif self.mode == 'CFB':
            if iv is None:
                iv = os.urandom(16)
            mode_obj = modes.CFB(iv)
        elif self.mode == 'OFB':
            if iv is None:
                iv = os.urandom(16)
            mode_obj = modes.OFB(iv)
        else:
            raise ValueError(f"不支持的加密模式: {self.mode}")

        return Cipher(algorithm, mode_obj, backend=self.backend), iv

    def encrypt(self, plaintext: str, iv: bytes = None) -> bytes:
        """
        加密文本

        Args:
            plaintext (str): 明文
            iv (bytes): 初始化向量（ECB模式不需要）

        Returns:
            bytes: 密文
        """
        data = plaintext.encode('utf-8')
        data = self._pad_data(data)

        cipher, _ = self._get_cipher(iv)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()

        return ciphertext

    def decrypt(self, ciphertext: bytes, iv: bytes = None) -> str:
        """
        解密文本

        Args:
            ciphertext (bytes): 密文
            iv (bytes): 初始化向量（ECB模式不需要）

        Returns:
            str: 解密后的明文
        """
        cipher, _ = self._get_cipher(iv)
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        data = self._unpad_data(padded_data)

        return data.decode('utf-8')


# 便捷函数
def aes_encrypt_string(plaintext: str, key: str, mode: str = 'CBC',
                      padding_mode: str = 'PKCS7', iv: bytes = None) -> str:
    """
    AES加密字符串，返回base64编码的结果

    Args:
        plaintext (str): 明文
        key (str): 密钥字符串
        mode (str): 加密模式 ('ECB', 'CBC', 'CFB', 'OFB')
        padding_mode (str): 填充模式
        iv (bytes): 初始化向量（ECB模式不需要）

    Returns:
        str: base64编码的密文
    """
    key_bytes = key.encode('utf-8')
    # 确保密钥长度符合要求
    if len(key_bytes) < 16:
        key_bytes = key_bytes.ljust(16, b'\0')
    elif 16 < len(key_bytes) < 24:
        key_bytes = key_bytes.ljust(24, b'\0')
    elif 24 < len(key_bytes) < 32:
        key_bytes = key_bytes.ljust(32, b'\0')
    else:
        key_bytes = key_bytes[:32]

    cipher = AESCipher(key_bytes, mode, padding_mode)
    ciphertext = cipher.encrypt(plaintext, iv)  # 传入iv参数

    return base64.b64encode(ciphertext).decode('utf-8')


def aes_decrypt_string(ciphertext_b64: str, key: str, iv: bytes = None,
                      mode: str = 'CBC', padding_mode: str = 'PKCS7') -> str:
    """
    AES解密base64编码的字符串

    Args:
        ciphertext_b64 (str): base64编码的密文
        key (str): 密钥字符串
        iv (bytes): 初始化向量（ECB模式不需要）
        mode (str): 加密模式
        padding_mode (str): 填充模式

    Returns:
        str: 解密后的明文
    """
    key_bytes = key.encode('utf-8')
    # 确保密钥长度符合要求
    if len(key_bytes) < 16:
        key_bytes = key_bytes.ljust(16, b'\0')
    elif 16 < len(key_bytes) < 24:
        key_bytes = key_bytes.ljust(24, b'\0')
    elif 24 < len(key_bytes) < 32:
        key_bytes = key_bytes.ljust(32, b'\0')
    else:
        key_bytes = key_bytes[:32]

    ciphertext = base64.b64decode(ciphertext_b64)

    cipher = AESCipher(key_bytes, mode, padding_mode)
    return cipher.decrypt(ciphertext, iv)


if __name__ == '__main__':
    # 测试新的实现
    result = aes_encrypt_string("Hello World", "mysecretpassword", "ECB", "PKCS7", b"mysecretpassword")
    print(result)
    decrypted = aes_decrypt_string(result, "mysecretpassword", base64.b64encode(b"mysecretpassword").decode(), "ECB")
    print(decrypted)

    # 使用AES类
    cipher = AESCipher(b"16bytekey1234567", "CBC")
    encrypted = cipher.encrypt("Hello World", b"16bytekey1234567")
    print(base64.b64encode(encrypted).decode())
    decrypted = cipher.decrypt(encrypted, b"16bytekey1234567")
    print(decrypted)