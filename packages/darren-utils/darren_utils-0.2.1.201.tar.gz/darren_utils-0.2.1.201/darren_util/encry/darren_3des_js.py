from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
from cryptography.hazmat.backends import default_backend
import base64
import os


class TDESCipher_JS:
    """
    与JavaScript CryptoJS兼容的3DES加密解密类
    """

    def __init__(self, key: str, iv: str = None, mode: str = 'CBC'):
        """
        初始化3DES加密器（兼容JS CryptoJS）

        Args:
            key (str): 密钥字符串（会被处理为24字节）
            iv (str): IV字符串（会被截取为8字节）
            mode (str): 加密模式 ('ECB', 'CBC')，默认CBC以兼容JS
        """
        # 模拟JS CryptoJS的密钥处理方式
        key_bytes = key.encode('utf-8')
        # 确保密钥长度为24字节（3DES标准）
        if len(key_bytes) < 24:
            key_bytes = key_bytes.ljust(24, b'\0')
        else:
            key_bytes = key_bytes[:24]
        
        self.key = key_bytes
        self.mode = mode.upper()
        
        # IV处理
        if self.mode != 'ECB':
            if iv:
                iv_bytes = iv.encode('utf-8')
                if len(iv_bytes) < 8:
                    iv_bytes = iv_bytes.ljust(8, b'\0')
                else:
                    iv_bytes = iv_bytes[:8]
                self.iv = iv_bytes
            else:
                self.iv = os.urandom(8)
        else:
            self.iv = None
            
        self.backend = default_backend()

    def _get_cipher(self):
        """获取加密器"""
        algorithm = TripleDES(self.key)
        
        if self.mode == 'ECB':
            mode_obj = modes.ECB()
        elif self.mode == 'CBC':
            mode_obj = modes.CBC(self.iv)
        else:
            raise ValueError(f"不支持的加密模式: {self.mode}")
            
        return Cipher(algorithm, mode_obj, backend=self.backend)

    def encrypt(self, plaintext: str) -> bytes:
        """
        加密文本（模拟JS CryptoJS行为）

        Args:
            plaintext (str): 明文

        Returns:
            bytes: 密文
        """
        data = plaintext.encode('utf-8')
        
        # PKCS7填充（ECB和CBC模式都需要填充）
        if self.mode in ['ECB', 'CBC']:
            padder = padding.PKCS7(64).padder()
            padded_data = padder.update(data) + padder.finalize()
        else:
            padded_data = data

        # 获取加密器
        cipher = self._get_cipher()
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return ciphertext

    def decrypt(self, ciphertext: bytes) -> str:
        """
        解密文本（模拟JS CryptoJS行为）

        Args:
            ciphertext (bytes): 密文

        Returns:
            str: 解密后的明文
        """
        cipher = self._get_cipher()
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # 去除PKCS7填充（ECB和CBC模式都需要去填充）
        if self.mode in ['ECB', 'CBC']:
            unpadder = padding.PKCS7(64).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
        else:
            data = padded_data

        return data.decode('utf-8')


def tdes_encrypt_string_js(plaintext: str, key: str, mode: str = 'CBC',
                          padding_mode: str = 'PKCS7', iv: str = None) -> str:
    """
    与JavaScript CryptoJS兼容的3DES加密字符串，返回base64编码的结果

    Args:
        plaintext (str): 明文
        key (str): 密钥字符串
        mode (str): 加密模式 ('ECB', 'CBC')
        padding_mode (str): 填充模式（保留参数，但实际使用PKCS7）
        iv (str): IV字符串

    Returns:
        str: base64编码的密文
    """
    # 注意：为了与JS兼容，始终使用PKCS7填充
    cipher = TDESCipher_JS(key, iv, mode)
    ciphertext = cipher.encrypt(plaintext)
    return base64.b64encode(ciphertext).decode('utf-8')


def tdes_decrypt_string_js(ciphertext_b64: str, key: str, iv_b64: str = None,
                          mode: str = 'CBC', padding_mode: str = 'PKCS7') -> str:
    """
    与JavaScript CryptoJS兼容的3DES解密base64编码的字符串

    Args:
        ciphertext_b64 (str): base64编码的密文
        key (str): 密钥字符串
        iv_b64 (str): base64编码的IV（对于ECB模式不需要）
        mode (str): 加密模式 ('ECB', 'CBC')
        padding_mode (str): 填充模式（保留参数，但实际使用PKCS7）

    Returns:
        str: 解密后的明文
    """
    # 注意：为了与JS兼容，始终使用PKCS7填充
    cipher = TDESCipher_JS(key, iv_b64, mode)
    ciphertext = base64.b64decode(ciphertext_b64)
    return cipher.decrypt(ciphertext)


if __name__ == '__main__':
    # 测试与JS兼容的3DES加密
    key = "mypassword123456"
    iv = "mypaswd1mypaswd1"  # JS中使用了16字节IV，但我们只取前8字节
    
    plaintext = "Hello World"
    
    # CBC模式加密（默认，与JS兼容）
    result_cbc = tdes_encrypt_string_js(plaintext, key, 'CBC', 'PKCS7', iv)
    print("CBC模式加密结果:", result_cbc)
    decrypted_cbc = tdes_decrypt_string_js(result_cbc, key, iv, 'CBC')
    print("CBC模式解密结果:", decrypted_cbc)
    
    # ECB模式加密
    result_ecb = tdes_encrypt_string_js(plaintext, key, 'ECB', 'PKCS7', None)
    print("ECB模式加密结果:", result_ecb)
    decrypted_ecb = tdes_decrypt_string_js(result_ecb, key, None, 'ECB')
    print("ECB模式解密结果:", decrypted_ecb)