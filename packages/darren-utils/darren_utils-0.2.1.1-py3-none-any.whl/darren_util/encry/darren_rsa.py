"""
RSA加密算法实现封装
基于cryptography库
"""

import base64
from typing import Union, Optional
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives import serialization, hashes


class RSACipher:
    """
    RSA加密/解密和签名/验证封装类
    """

    def __init__(self, private_key=None, public_key=None):
        """
        使用可选密钥初始化RSA密码器
        
        :param private_key: PEM格式的私钥（可选）
        :param public_key: PEM格式的公钥（可选）
        """
        self.private_key = private_key
        self.public_key = public_key
        
        # Parse keys if provided
        self.private_key_obj: Optional[RSAPrivateKey] = None
        self.public_key_obj: Optional[RSAPublicKey] = None
        
        if private_key:
            if isinstance(private_key, str):
                private_key = private_key.encode('utf-8')
            key_obj = serialization.load_pem_private_key(
                private_key,
                password=None
            )
            if isinstance(key_obj, RSAPrivateKey):
                self.private_key_obj = key_obj
            else:
                raise ValueError("Provided key is not an RSA private key")
            
        if public_key:
            if isinstance(public_key, str):
                public_key = public_key.encode('utf-8')
            key_obj = serialization.load_pem_public_key(public_key)
            if isinstance(key_obj, RSAPublicKey):
                self.public_key_obj = key_obj
            else:
                raise ValueError("Provided key is not an RSA public key")

    @staticmethod
    def generate_keypair(key_size=2048):
        """
        生成新的RSA密钥对
        
        :param key_size: 密钥大小（比特），默认2048位
        :return: PEM格式的(私钥, 公钥)元组
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        
        # Get private key in PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Get public key in PEM format
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem.decode('utf-8'), public_pem.decode('utf-8')

    def encrypt(self, plaintext: str, public_key=None, padding_scheme='OAEP') -> str:
        """
        使用RSA算法加密明文
        
        :param plaintext: 要加密的文本
        :param public_key: PEM格式的公钥（可选，如果未提供则使用实例密钥）
        :param padding_scheme: 填充方案 ('OAEP', 'PKCS1', 'NONE')
        :return: Base64编码的加密密文
        """
        if not public_key and not self.public_key_obj:
            raise ValueError("Public key is required for encryption")
        
        if public_key:
            if isinstance(public_key, str):
                public_key = public_key.encode('utf-8')
            public_key_obj = serialization.load_pem_public_key(public_key)
            if not isinstance(public_key_obj, RSAPublicKey):
                raise ValueError("Provided key is not an RSA public key")
        else:
            public_key_obj = self.public_key_obj
            
        # Encrypt the plaintext
        if public_key_obj is None:
            raise ValueError("No valid public key available for encryption")
            
        # Prepare plaintext based on padding scheme
        plaintext_bytes = plaintext.encode('utf-8')
        
        # Apply padding scheme
        if padding_scheme == 'OAEP':
            pad = padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        elif padding_scheme == 'PKCS1':
            pad = padding.PKCS1v15()
        elif padding_scheme == 'NONE':
            # For no padding, manually implement raw RSA
            # This is not recommended for security reasons
            key_size = public_key_obj.key_size // 8
            # 检查明文长度是否合适
            if len(plaintext_bytes) > key_size - 11:
                raise ValueError("Plaintext too long for RSA encryption without padding")
            message_int = int.from_bytes(plaintext_bytes, 'big')
            encrypted_int = pow(message_int, public_key_obj.public_numbers().e, public_key_obj.public_numbers().n)
            return base64.b64encode(encrypted_int.to_bytes(key_size, 'big')).decode('utf-8')
        else:
            raise ValueError("Unsupported padding scheme. Use 'OAEP', 'PKCS1', or 'NONE'")
            
        ciphertext = public_key_obj.encrypt(plaintext_bytes, pad)
        
        # Return base64 encoded ciphertext
        return base64.b64encode(ciphertext).decode('utf-8')

    def decrypt_with_public_key(self, ciphertext: str, public_key=None, padding_scheme='OAEP') -> str:
        """
        使用RSA公钥解密密文（用于特殊情况，如服务器用私钥加密后返回给客户端）

        :param ciphertext: Base64编码的密文
        :param public_key: PEM格式的公钥（可选，如果未提供则使用实例密钥）
        :param padding_scheme: 填充方案 ('OAEP', 'PKCS1')
        :return: 解密后的明文
        """
        if not public_key and not self.public_key_obj:
            raise ValueError("Public key is required for decryption with public key")

        if public_key:
            if isinstance(public_key, str):
                public_key = public_key.encode('utf-8')
            public_key_obj = serialization.load_pem_public_key(public_key)
            if not isinstance(public_key_obj, RSAPublicKey):
                raise ValueError("Provided key is not an RSA public key")
        else:
            public_key_obj = self.public_key_obj

        # Decode base64 ciphertext
        ciphertext_bytes = base64.b64decode(ciphertext)

        # Decrypt the ciphertext
        if public_key_obj is None:
            raise ValueError("No valid public key available for decryption")

        # 注意：这里我们使用公钥进行"解密"操作，这在技术上是反向操作
        # 实际上这是使用公钥的指数和模数进行幂运算
        ciphertext_int = int.from_bytes(ciphertext_bytes, 'big')
        # 使用公钥的e指数进行解密操作
        decrypted_int = pow(ciphertext_int, public_key_obj.public_numbers().e, public_key_obj.public_numbers().n)

        # 转换回字节
        key_size = public_key_obj.key_size // 8
        decrypted_bytes = decrypted_int.to_bytes(key_size, 'big')

        # 移除填充（根据具体填充方案）
        if padding_scheme == 'PKCS1':
            # PKCS1 v1.5 解填充 - 更宽松的处理方式
            # 查找第一个 0x00 字节的位置
            zero_index = decrypted_bytes.find(0x00)
            if zero_index != -1:
                # 通常在 PKCS1 v1.5 中，数据以 0x00 0x02 开头，然后是随机填充，再以 0x00 分隔符结尾
                # 找到最后一个 0x00 分隔符
                last_zero_index = decrypted_bytes.rfind(0x00)
                if last_zero_index != -1 and last_zero_index < len(decrypted_bytes) - 1:
                    decrypted_bytes = decrypted_bytes[last_zero_index + 1:]
                else:
                    # 如果找不到合适的分隔符，就简单移除开头的零字节
                    decrypted_bytes = decrypted_bytes.lstrip(b'\x00')
            else:
                # 简单处理：移除开头的零字节
                decrypted_bytes = decrypted_bytes.lstrip(b'\x00')
        elif padding_scheme == 'OAEP':
            # OAEP 解填充比较复杂，这里简化处理
            decrypted_bytes = decrypted_bytes.lstrip(b'\x00')

        return decrypted_bytes.decode('utf-8', errors='ignore')

    def decrypt(self, ciphertext: str, private_key=None, padding_scheme='OAEP') -> str:
        """
        使用RSA算法解密密文
        
        :param ciphertext: Base64编码的密文
        :param private_key: PEM格式的私钥（可选，如果未提供则使用实例密钥）
        :param padding_scheme: 填充方案 ('OAEP', 'PKCS1')
        :return: 解密后的明文
        """
        if not private_key and not self.private_key_obj:
            raise ValueError("Private key is required for decryption")
            
        if private_key:
            if isinstance(private_key, str):
                private_key = private_key.encode('utf-8')
            private_key_obj = serialization.load_pem_private_key(
                private_key,
                password=None
            )
            if not isinstance(private_key_obj, RSAPrivateKey):
                raise ValueError("Provided key is not an RSA private key")
        else:
            private_key_obj = self.private_key_obj
            
        # Decode base64 ciphertext
        ciphertext_bytes = base64.b64decode(ciphertext)
            
        # Decrypt the ciphertext
        if private_key_obj is None:
            raise ValueError("No valid private key available for decryption")
            
        # Apply padding scheme
        if padding_scheme == 'OAEP':
            pad = padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        elif padding_scheme == 'PKCS1':
            pad = padding.PKCS1v15()
        elif padding_scheme == 'NONE':
            # For no padding, manually implement raw RSA decryption
            # This is not recommended for security reasons
            key_size = private_key_obj.key_size // 8
            ciphertext_int = int.from_bytes(ciphertext_bytes, 'big')
            decrypted_int = pow(ciphertext_int, private_key_obj.private_numbers().d, private_key_obj.private_numbers().public_numbers.n)
            plaintext_bytes = decrypted_int.to_bytes(key_size, 'big')
            # Remove leading zeros
            plaintext_bytes = plaintext_bytes.lstrip(b'\x00')
            return plaintext_bytes.decode('utf-8')
        else:
            raise ValueError("Unsupported padding scheme. Use 'OAEP', 'PKCS1', or 'NONE'")
            
        plaintext = private_key_obj.decrypt(ciphertext_bytes, pad)
        
        return plaintext.decode('utf-8')

    def sign(self, data: str, private_key=None, padding_scheme='PSS') -> str:
        """
        使用RSA算法对数据进行签名
        
        :param data: 要签名的数据
        :param private_key: PEM格式的私钥（可选，如果未提供则使用实例密钥）
        :param padding_scheme: 填充方案 ('PSS', 'PKCS1')
        :return: Base64编码的签名
        """
        if not private_key and not self.private_key_obj:
            raise ValueError("Private key is required for signing")
            
        if private_key:
            if isinstance(private_key, str):
                private_key = private_key.encode('utf-8')
            private_key_obj = serialization.load_pem_private_key(
                private_key,
                password=None
            )
            if not isinstance(private_key_obj, RSAPrivateKey):
                raise ValueError("Provided key is not an RSA private key")
        else:
            private_key_obj = self.private_key_obj
            
        # Sign the data
        if private_key_obj is None:
            raise ValueError("No valid private key available for signing")
            
        data_bytes = data.encode('utf-8')
        
        # Apply padding scheme
        if padding_scheme == 'PSS':
            pad = padding.PSS(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            )
            algorithm = hashes.SHA256()
        elif padding_scheme == 'PKCS1':
            pad = padding.PKCS1v15()
            algorithm = hashes.SHA256()
        else:
            raise ValueError("Unsupported padding scheme. Use 'PSS' or 'PKCS1'")
            
        signature = private_key_obj.sign(data_bytes, pad, algorithm)
        
        # Return base64 encoded signature
        return base64.b64encode(signature).decode('utf-8')

    def verify(self, data: str, signature: str, public_key=None, padding_scheme='PSS') -> bool:
        """
        使用RSA算法验证签名
        
        :param data: 原始数据
        :param signature: Base64编码的签名
        :param public_key: PEM格式的公钥（可选，如果未提供则使用实例密钥）
        :param padding_scheme: 填充方案 ('PSS', 'PKCS1')
        :return: 如果验证成功返回True，否则返回False
        """
        if not public_key and not self.public_key_obj:
            raise ValueError("Public key is required for verification")
            
        if public_key:
            if isinstance(public_key, str):
                public_key = public_key.encode('utf-8')
            public_key_obj = serialization.load_pem_public_key(public_key)
            if not isinstance(public_key_obj, RSAPublicKey):
                raise ValueError("Provided key is not an RSA public key")
        else:
            public_key_obj = self.public_key_obj
            
        # Decode base64 signature
        signature_bytes = base64.b64decode(signature)
            
        # Verify the signature
        if public_key_obj is None:
            raise ValueError("No valid public key available for verification")
            
        # Apply padding scheme
        if padding_scheme == 'PSS':
            pad = padding.PSS(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            )
            algorithm = hashes.SHA256()
        elif padding_scheme == 'PKCS1':
            pad = padding.PKCS1v15()
            algorithm = hashes.SHA256()
        else:
            raise ValueError("Unsupported padding scheme. Use 'PSS' or 'PKCS1'")
            
        try:
            public_key_obj.verify(signature_bytes, data.encode('utf-8'), pad, algorithm)
            return True
        except Exception:
            return False


# 便捷函数
def rsa_generate_keypair(key_size=1024):
    """
    生成新的RSA密钥对
    
    :param key_size: 密钥大小（比特），默认1024位
    :return: PEM格式的(私钥, 公钥)元组
    """
    return RSACipher.generate_keypair(key_size)


def rsa_encrypt_string(plaintext: str, public_key: str, padding_scheme='OAEP') -> str:
    """
    使用RSA加密字符串
    
    :param plaintext: 要加密的文本
    :param public_key: PEM格式的公钥
    :param padding_scheme: 填充方案 ('OAEP', 'PKCS1', 'NONE')
    :return: Base64编码的加密密文
    """
    cipher = RSACipher(public_key=public_key)
    return cipher.encrypt(plaintext, padding_scheme=padding_scheme)





def rsa_decrypt_with_public_key(ciphertext: str, public_key: str, padding_scheme='OAEP') -> str:
    """
    使用RSA公钥解密字符串

    :param ciphertext: Base64编码的密文
    :param public_key: PEM格式的公钥
    :param padding_scheme: 填充方案 ('OAEP', 'PKCS1')
    :return: 解密后的明文
    """
    cipher = RSACipher(public_key=public_key)
    return cipher.decrypt_with_public_key(ciphertext, padding_scheme=padding_scheme)


def rsa_decrypt_string(ciphertext: str, private_key: str, padding_scheme='OAEP') -> str:
    """
    使用RSA解密字符串
    
    :param ciphertext: Base64编码的密文
    :param private_key: PEM格式的私钥
    :param padding_scheme: 填充方案 ('OAEP', 'PKCS1', 'NONE')
    :return: 解密后的明文
    """
    cipher = RSACipher(private_key=private_key)
    return cipher.decrypt(ciphertext, padding_scheme=padding_scheme)


def rsa_sign(data: str, private_key: str, padding_scheme='PSS') -> str:
    """
    使用RSA算法对数据进行签名
    
    :param data: 要签名的数据
    :param private_key: PEM格式的私钥
    :param padding_scheme: 填充方案 ('PSS', 'PKCS1')
    :return: Base64编码的签名
    """
    cipher = RSACipher(private_key=private_key)
    return cipher.sign(data, padding_scheme=padding_scheme)


def rsa_verify(data: str, signature: str, public_key: str, padding_scheme='PSS') -> bool:
    """
    使用RSA算法验证签名
    
    :param data: 原始数据
    :param signature: Base64编码的签名
    :param public_key: PEM格式的公钥
    :param padding_scheme: 填充方案 ('PSS', 'PKCS1')
    :return: 如果验证成功返回True，否则返回False
    """
    cipher = RSACipher(public_key=public_key)
    return cipher.verify(data, signature, padding_scheme=padding_scheme)

if __name__ == '__main__':
    # Generate a new RSA key pair
    private_key, public_key = rsa_generate_keypair()
    print(f"Private key:\n{private_key}")
    print(f"Public key:\n{public_key}")

    plaintext = "hello"
    
    # Test with OAEP padding (default)
    print("\n--- Testing with OAEP padding ---")
    ciphertext = rsa_encrypt_string(plaintext, public_key, padding_scheme='OAEP')
    print(f"Ciphertext (OAEP): {ciphertext}")
    decrypted_text = rsa_decrypt_string(ciphertext, private_key, padding_scheme='OAEP')
    print(f"Decrypted (OAEP): {decrypted_text}")
    
    # Test with PKCS1 padding
    print("\n--- Testing with PKCS1 padding ---")
    ciphertext = rsa_encrypt_string(plaintext, public_key, padding_scheme='PKCS1')
    print(f"Ciphertext (PKCS1): {ciphertext}")
    decrypted_text = rsa_decrypt_string(ciphertext, private_key, padding_scheme='PKCS1')
    print(f"Decrypted (PKCS1): {decrypted_text}")

    # Test with PKCS1 padding
    print("\n--- Testing with NONE padding ---")
    ciphertext = rsa_encrypt_string(plaintext, public_key, padding_scheme='NONE')
    print(f"Ciphertext (NONE): {ciphertext}")
    decrypted_text = rsa_decrypt_string(ciphertext, private_key, padding_scheme='NONE')
    print(f"Decrypted (NONE): {decrypted_text}")

    # Sign a string
    signature = rsa_sign(plaintext, private_key, padding_scheme='PSS')
    print(f"Signature: {signature}")
    
    # Verify the signature
    is_valid = rsa_verify(plaintext, signature, public_key, padding_scheme='PSS')
    print(f"Signature valid: {is_valid}")