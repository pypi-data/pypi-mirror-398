"""
SM2 encryption algorithm implementation wrapper
Based on the gmssl library
"""

import binascii
from gmssl import sm2


class SM2Cipher:
    """
    SM2 encryption/decryption and signing/verification wrapper class
    """

    def __init__(self, private_key=None, public_key=None):
        """
        Initialize SM2 cipher with optional keys
        
        :param private_key: Private key in hexadecimal format (optional)
        :param public_key: Public key in hexadecimal format (optional)
        """
        self.private_key = private_key
        self.public_key = public_key
        self.sm2_crypto = sm2.CryptSM2(
            private_key=self.private_key, 
            public_key=self.public_key
        ) if private_key or public_key else None

    def generate_keypair(self):
        """
        Generate a new SM2 key pair
        
        :return: tuple of (private_key, public_key)
        """
        private_key = sm2.CryptSM2.generate_private_key()
        public_key = private_key.public_key
        return private_key, public_key

    def encrypt(self, plaintext: str, public_key=None) -> str:
        """
        Encrypt plaintext using SM2 algorithm
        
        :param plaintext: Text to encrypt
        :param public_key: Public key in hexadecimal format (optional, uses instance key if not provided)
        :return: Encrypted ciphertext in hexadecimal format
        """
        if not public_key and not self.public_key:
            raise ValueError("Public key is required for encryption")
        
        if public_key:
            crypto = sm2.CryptSM2(public_key=public_key)
        else:
            crypto = self.sm2_crypto
            
        encrypted = crypto.encrypt(plaintext.encode('utf-8'))
        return binascii.b2a_hex(encrypted).decode('utf-8')

    def decrypt(self, ciphertext: str, private_key=None) -> str:
        """
        Decrypt ciphertext using SM2 algorithm
        
        :param ciphertext: Ciphertext in hexadecimal format
        :param private_key: Private key in hexadecimal format (optional, uses instance key if not provided)
        :return: Decrypted plaintext
        """
        if not private_key and not self.private_key:
            raise ValueError("Private key is required for decryption")
            
        if private_key:
            crypto = sm2.CryptSM2(private_key=private_key)
        else:
            crypto = self.sm2_crypto
            
        decrypted = crypto.decrypt(binascii.a2b_hex(ciphertext))
        return decrypted.decode('utf-8')

    def sign(self, data: str, private_key=None) -> str:
        """
        Sign data using SM2 algorithm
        
        :param data: Data to sign
        :param private_key: Private key in hexadecimal format (optional, uses instance key if not provided)
        :return: Signature in hexadecimal format
        """
        if not private_key and not self.private_key:
            raise ValueError("Private key is required for signing")
            
        if private_key:
            crypto = sm2.CryptSM2(private_key=private_key)
        else:
            crypto = self.sm2_crypto
            
        signature = crypto.sign(data.encode('utf-8'))
        return signature

    def verify(self, data: str, signature: str, public_key=None) -> bool:
        """
        Verify signature using SM2 algorithm
        
        :param data: Original data
        :param signature: Signature in hexadecimal format
        :param public_key: Public key in hexadecimal format (optional, uses instance key if not provided)
        :return: True if verification succeeds, False otherwise
        """
        if not public_key and not self.public_key:
            raise ValueError("Public key is required for verification")
            
        if public_key:
            crypto = sm2.CryptSM2(public_key=public_key)
        else:
            crypto = self.sm2_crypto
            
        return crypto.verify(signature, data.encode('utf-8'))


def sm2_generate_keypair():
    """
    Generate a new SM2 key pair
    
    :return: tuple of (private_key, public_key)
    """
    private_key = sm2.CryptSM2.generate_private_key()
    public_key = private_key.public_key
    return private_key, public_key


def sm2_encrypt_string(plaintext: str, public_key: str) -> str:
    """
    Encrypt string using SM2 algorithm
    
    :param plaintext: Text to encrypt
    :param public_key: Public key in hexadecimal format
    :return: Encrypted ciphertext in hexadecimal format
    """
    crypto = sm2.CryptSM2(public_key=public_key)
    encrypted = crypto.encrypt(plaintext.encode('utf-8'))
    return binascii.b2a_hex(encrypted).decode('utf-8')


def sm2_decrypt_string(ciphertext: str, private_key: str) -> str:
    """
    Decrypt string using SM2 algorithm
    
    :param ciphertext: Ciphertext in hexadecimal format
    :param private_key: Private key in hexadecimal format
    :return: Decrypted plaintext
    """
    crypto = sm2.CryptSM2(private_key=private_key)
    decrypted = crypto.decrypt(binascii.a2b_hex(ciphertext))
    return decrypted.decode('utf-8')


def sm2_sign(data: str, private_key: str) -> str:
    """
    Sign data using SM2 algorithm
    
    :param data: Data to sign
    :param private_key: Private key in hexadecimal format
    :return: Signature in hexadecimal format
    """
    crypto = sm2.CryptSM2(private_key=private_key)
    signature = crypto.sign(data.encode('utf-8'))
    return signature


def sm2_verify(data: str, signature: str, public_key: str) -> bool:
    """
    Verify signature using SM2 algorithm
    
    :param data: Original data
    :param signature: Signature in hexadecimal format
    :param public_key: Public key in hexadecimal format
    :return: True if verification succeeds, False otherwise
    """
    crypto = sm2.CryptSM2(public_key=public_key)
    return crypto.verify(signature, data.encode('utf-8'))