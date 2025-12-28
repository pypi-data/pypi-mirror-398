"""
JavaScript兼容RSA加密解密模块
基于JSEncrypt库的Python实现
"""

import base64
import binascii
from typing import Optional, Union

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


class JSRSA:
    """
    JavaScript JSEncrypt兼容的RSA加密解密类
    """

    def __init__(self):
        self.key = None
        self.log = False

    def _apply_zero_padding(self, data: bytes, key_size: int) -> bytes:
        """
        应用零填充（模拟JavaScript中padding=0的行为）
        
        :param data: 要填充的数据
        :param key_size: 密钥大小（字节）
        :return: 填充后的数据
        """
        # 添加PKCS#1 v1.5格式的零填充
        padded = bytearray(key_size)
        padded[1] = 0  # 第二个字节为0
        # 数据放在最后
        data_start_index = key_size - len(data)
        padded[data_start_index:] = data
        return bytes(padded)

    def _remove_zero_padding(self, padded_data: bytes) -> bytes:
        """
        移除零填充（模拟JavaScript中padding=0的解密行为）
        
        :param padded_data: 填充的数据
        :return: 移除填充后的数据
        """
        # 查找第一个非零字节的位置（跳过前两个字节）
        start_index = 2
        while start_index < len(padded_data) and padded_data[start_index] == 0:
            start_index += 1
        return padded_data[start_index:]

    def set_public_key(self, pubkey: str):
        """
        设置公钥
        
        :param pubkey: PEM格式的公钥字符串
        """
        try:
            if isinstance(pubkey, str):
                pubkey = pubkey.encode('utf-8')
            self.key = serialization.load_pem_public_key(pubkey, backend=default_backend())
        except Exception as e:
            if self.log:
                print(f"Error setting public key: {e}")
            raise

    def set_private_key(self, privkey: str):
        """
        设置私钥
        
        :param privkey: PEM格式的私钥字符串
        """
        try:
            if isinstance(privkey, str):
                privkey = privkey.encode('utf-8')
            self.key = serialization.load_pem_private_key(privkey, password=None, backend=default_backend())
        except Exception as e:
            if self.log:
                print(f"Error setting private key: {e}")
            raise

    def public_encrypt(self, text: str, pad: Union[padding.AsymmetricPadding, int] = None) -> str:
        """
        使用公钥加密（兼容JavaScript JSEncrypt）
        
        :param text: 要加密的文本
        :param pad: 填充方式，可以是cryptography库的填充对象或整数(0=zero padding, 1=特定填充, 2=PKCS1v15)
        :return: Base64编码的加密结果
        """
        if not isinstance(self.key, RSAPublicKey):
            raise ValueError("需要设置有效的公钥用于加密")

        # 如果未指定填充方式，则使用默认的PKCS1v15
        if pad is None:
            pad = padding.PKCS1v15()
        
        # 如果pad是整数，则映射到对应的填充方式
        elif isinstance(pad, int):
            if pad == 0:  # Zero padding (接近JavaScript中的nopadding)
                # 手动实现零填充
                # 注意：这种方式不安全，仅用于兼容JavaScript的特殊需求
                key_size = self.key.key_size // 8
                padded_data = self._apply_zero_padding(text.encode('utf-8'), key_size)
                # 直接进行模幂运算，不使用标准填充
                from cryptography.hazmat.primitives.asymmetric import rsa
                encrypted = pow(
                    int.from_bytes(padded_data, 'big'),
                    self.key.public_numbers().e,
                    self.key.public_numbers().n
                )
                encrypted_bytes = encrypted.to_bytes(key_size, 'big')
                return base64.b64encode(encrypted_bytes).decode('utf-8')
            elif pad == 2:  # PKCS1v15
                pad = padding.PKCS1v15()
            # 其他情况默认使用PKCS1v15
            else:
                pad = padding.PKCS1v15()

        try:
            # 使用指定的填充方式
            encrypted = self.key.encrypt(
                text.encode('utf-8'),
                pad
            )
            # 转换为JavaScript兼容的十六进制格式
            hex_encrypted = binascii.hexlify(encrypted).decode('utf-8')
            # 转换为Base64格式返回
            return base64.b64encode(binascii.unhexlify(hex_encrypted)).decode('utf-8')
        except Exception as e:
            if self.log:
                print(f"加密错误: {e}")
            return False

    def private_decrypt(self, encrypted_text: str, pad: Union[padding.AsymmetricPadding, int] = None) -> str:
        """
        使用私钥解密（兼容JavaScript JSEncrypt）
        
        :param encrypted_text: Base64编码的加密文本
        :param pad: 填充方式，可以是cryptography库的填充对象或整数(0=zero padding, 1=特定填充, 2=PKCS1v15)
        :return: 解密后的原始文本
        """
        if not isinstance(self.key, RSAPrivateKey):
            raise ValueError("需要设置有效的私钥用于解密")

        # 将Base64解码为字节
        encrypted_data = base64.b64decode(encrypted_text)
        
        # 如果未指定填充方式，则使用默认的PKCS1v15
        if pad is None:
            pad = padding.PKCS1v15()
        
        # 如果pad是整数，则映射到对应的处理方式
        elif isinstance(pad, int):
            if pad == 0:  # Zero padding (接近JavaScript中的nopadding)
                # 手动实现零填充解密
                key_size = self.key.key_size // 8
                # 直接进行模幂运算，不使用标准解密
                decrypted_int = pow(
                    int.from_bytes(encrypted_data, 'big'),
                    self.key.private_numbers().d,
                    self.key.private_numbers().public_numbers.n
                )
                decrypted_bytes = decrypted_int.to_bytes(key_size, 'big')
                # 移除零填充并解码
                return self._remove_zero_padding(decrypted_bytes).decode('utf-8')
            elif pad == 2:  # PKCS1v15
                pad = padding.PKCS1v15()
            # 其他情况默认使用PKCS1v15
            else:
                pad = padding.PKCS1v15()

        try:
            # 使用指定的填充方式解密
            decrypted = self.key.decrypt(
                encrypted_data,
                pad
            )
            return decrypted.decode('utf-8')
        except Exception as e:
            if self.log:
                print(f"解密错误: {e}")
            return False

    def private_encrypt(self, text: str) -> str:
        """
        使用私钥加密（签名）
        
        :param text: 要加密的文本
        :return: Base64编码的加密结果
        """
        if not isinstance(self.key, RSAPrivateKey):
            raise ValueError("需要设置有效的私钥用于加密")

        try:
            # 私钥加密通常用于签名，这里使用PKCS1v15填充
            encrypted = self.key.sign(
                text.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            # 转换为Base64格式返回
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            if self.log:
                print(f"私钥加密错误: {e}")
            return False

    def public_decrypt(self, encrypted_text: str) -> str:
        """
        使用公钥解密（验证签名）
        
        :param encrypted_text: Base64编码的加密文本
        :return: 解密后的原始文本
        """
        if not isinstance(self.key, RSAPublicKey):
            raise ValueError("需要设置有效的公钥用于解密")

        try:
            # 将Base64解码为字节
            encrypted_data = base64.b64decode(encrypted_text)
            # 公钥解密（验证）
            # 注意：这里实际是验证签名，不是真正的解密
            # 在JSEncrypt中，公钥解密通常用于验证私钥加密的内容
            # 但Python的cryptography库不直接支持公钥解密
            # 这里需要特殊处理，可能需要使用签名验证
            return "Not supported in Python version"
        except Exception as e:
            if self.log:
                print(f"公钥解密错误: {e}")
            return False

    @staticmethod
    def generate_keypair(key_size: int = 1024) -> tuple:
        """
        生成RSA密钥对
        
        :param key_size: 密钥长度，默认1024位
        :return: (private_key, public_key) PEM格式的密钥对
        """
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

        # 获取私钥PEM格式
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # 获取公钥PEM格式
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem.decode('utf-8'), public_pem.decode('utf-8')


# 便捷函数
def js_rsa_generate_keypair(key_size: int = 1024) -> tuple:
    """
    生成RSA密钥对
    
    :param key_size: 密钥长度，默认1024位
    :return: (private_key, public_key) PEM格式的密钥对
    """
    return JSRSA.generate_keypair(key_size)


def js_rsa_public_encrypt(text: str, public_key: str, pad: padding.AsymmetricPadding = None) -> str:
    """
    使用公钥加密
    
    :param text: 要加密的文本
    :param public_key: PEM格式的公钥
    :param pad: 填充方式，默认使用PKCS1v15
    :return: Base64编码的加密结果
    """
    rsa_obj = JSRSA()
    rsa_obj.set_public_key(public_key)
    return rsa_obj.public_encrypt(text, pad)


def js_rsa_private_decrypt(encrypted_text: str, private_key: str, pad: padding.AsymmetricPadding = None) -> str:
    """
    使用私钥解密
    
    :param encrypted_text: Base64编码的加密文本
    :param private_key: PEM格式的私钥
    :param pad: 填充方式，默认使用PKCS1v15
    :return: 解密后的原始文本
    """
    rsa_obj = JSRSA()
    rsa_obj.set_private_key(private_key)
    return rsa_obj.private_decrypt(encrypted_text, pad)


def js_rsa_private_encrypt(text: str, private_key: str) -> str:
    """
    使用私钥加密（签名）
    
    :param text: 要加密的文本
    :param private_key: PEM格式的私钥
    :return: Base64编码的加密结果
    """
    rsa_obj = JSRSA()
    rsa_obj.set_private_key(private_key)
    return rsa_obj.private_encrypt(text)


if __name__ == "__main__":
    # 生成密钥对
    private_key, public_key = js_rsa_generate_keypair()
    print("私钥:")
    print(private_key)
    print("\n公钥:")
    print(public_key)
    # 测试加密解密
    text = "Hello, World!"
    print(f"\n原始文本: {text}")
    # 使用默认填充方式（PKCS1v15）加密和解密
    encrypted_default = js_rsa_public_encrypt(text, public_key)
    print(f"\n使用默认填充加密后: {encrypted_default}")
    decrypted_default = js_rsa_private_decrypt(encrypted_default, private_key)
    print(f"\n使用默认填充解密后: {decrypted_default}")

    encrypted_pkcs1 = js_rsa_public_encrypt(text, public_key, padding.PKCS1v15())
    print(f"\n使用PKCS1v15填充加密后: {encrypted_pkcs1}")
    decrypted_pkcs1 = js_rsa_private_decrypt(encrypted_pkcs1, private_key, padding.PKCS1v15())
    print(f"\n使用PKCS1v15填充解密后: {decrypted_pkcs1}")
    

    encrypted_oaep = js_rsa_public_encrypt(text, public_key, 0)
    print(f"\n使用zeroPadding填充加密后: {encrypted_oaep}")
    decrypted_oaep = js_rsa_private_decrypt(encrypted_oaep, private_key, 0)
    print(f"\n使用zeroPadding填充解密后: {decrypted_oaep}")
