from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
from cryptography.hazmat.backends import default_backend
import base64
import os


class TDESCipher:
    """
    3DES加密解密类，支持多种模式和填充方式
    """

    def __init__(self, key: bytes, mode: str = 'CBC', padding_mode: str = 'PKCS7'):
        """
        初始化3DES加密器

        Args:
            key (bytes): 密钥（16字节对应2-key 3DES，24字节对应3-key 3DES）
            mode (str): 加密模式 ('ECB', 'CBC', 'CFB', 'OFB')
            padding_mode (str): 填充模式 ('PKCS7', 'ISO7816', 'ANSIX923')
        """
        # 3DES密钥必须是16字节(2-key)或24字节(3-key)
        if len(key) not in [16, 24]:
            # 如果不是16或24字节，尝试调整长度
            if len(key) < 16:
                key = key.ljust(16, b'\0')
            elif 16 < len(key) < 24:
                key = key.ljust(24, b'\0')
            elif len(key) > 24:
                key = key[:24]
            
            # 确保最终长度是16或24字节
            if len(key) not in [16, 24]:
                key = key[:16] if len(key) >= 16 else key.ljust(16, b'\0')
        
        self.key = key
        self.mode = mode.upper()
        self.padding_mode = padding_mode.upper()
        self.backend = default_backend()

    def _get_padding(self, block_size: int = 64):
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
        algorithm = TripleDES(self.key)  # 使用3DES算法

        if self.mode == 'ECB':
            mode_obj = modes.ECB()
        elif self.mode == 'CBC':
            if iv is None:
                iv = os.urandom(8)  # 3DES的IV是8字节
            mode_obj = modes.CBC(iv)
        elif self.mode == 'CFB':
            if iv is None:
                iv = os.urandom(8)
            mode_obj = modes.CFB(iv)
        elif self.mode == 'OFB':
            if iv is None:
                iv = os.urandom(8)
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
def tdes_encrypt_string(plaintext: str, key: str, mode: str = 'CBC',
                       padding_mode: str = 'PKCS7', iv: bytes = None) -> str:
    """
    3DES加密字符串，返回base64编码的结果

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
    # 确保密钥长度为16或24字节
    if len(key_bytes) < 16:
        key_bytes = key_bytes.ljust(16, b'\0')
    elif 16 < len(key_bytes) < 24:
        key_bytes = key_bytes.ljust(24, b'\0')
    elif len(key_bytes) > 24:
        key_bytes = key_bytes[:24]

    cipher = TDESCipher(key_bytes, mode, padding_mode)
    ciphertext = cipher.encrypt(plaintext, iv)

    return base64.b64encode(ciphertext).decode('utf-8')


def tdes_decrypt_string(ciphertext_b64: str, key: str, iv_b64: str = None,
                       mode: str = 'CBC', padding_mode: str = 'PKCS7') -> str:
    """
    3DES解密base64编码的字符串

    Args:
        ciphertext_b64 (str): base64编码的密文
        key (str): 密钥字符串
        iv_b64 (str): base64编码的IV
        mode (str): 加密模式
        padding_mode (str): 填充模式

    Returns:
        str: 解密后的明文
    """
    key_bytes = key.encode('utf-8')
    # 确保密钥长度为16或24字节
    if len(key_bytes) < 16:
        key_bytes = key_bytes.ljust(16, b'\0')
    elif 16 < len(key_bytes) < 24:
        key_bytes = key_bytes.ljust(24, b'\0')
    elif len(key_bytes) > 24:
        key_bytes = key_bytes[:24]

    ciphertext = base64.b64decode(ciphertext_b64)
    iv = base64.b64decode(iv_b64) if iv_b64 else None

    cipher = TDESCipher(key_bytes, mode, padding_mode)
    return cipher.decrypt(ciphertext, iv)


if __name__ == '__main__':
    # 测试3DES加密
    result = tdes_encrypt_string("Hello World", "mypassword123456", "CBC", "PKCS7", b"mypaswd1mypaswd1")
    print("加密结果:", result)
    decrypted = tdes_decrypt_string(result, "mypassword123456", base64.b64encode(b"mypaswd1mypaswd1").decode(), "CBC")
    print("解密结果:", decrypted)