"""
darren_utils package initialization.
"""
from darren_util.encry.darren_3des import TDESCipher, tdes_encrypt_string, tdes_decrypt_string
from darren_util.encry.darren_3des_js import TDESCipher_JS, tdes_encrypt_string_js, tdes_decrypt_string_js
from darren_util.encry.darren_aes import AESCipher, aes_encrypt_string, aes_decrypt_string
from darren_util.encry.darren_des import DESCipher, des_encrypt_string, des_decrypt_string
from darren_util.encry.darren_hash import hash_md5_string, hash_md5_bytes, hash_sha1_string, hash_sha256_string, \
    hash_sha512_string, \
    hash_sha1_bytes, hash_sha256_bytes, hash_sha512_bytes, hash_crc32_int
from darren_util.encry.darren_hmac import hmac_md5, hmac_sha1, hmac_sha256, hmac_sha512, hmac_sha3_256, hmac_sha3_512
from darren_util.encry.darren_rc4 import hash_crc32_string, rc4_encrypt_string, rc4_decrypt_string, RC4
from darren_util.encry.darren_rsa import RSACipher, rsa_generate_keypair, rsa_encrypt_string, rsa_decrypt_string, \
    rsa_sign, rsa_verify, rsa_decrypt_with_public_key
from darren_util.encry.darren_sm2 import SM2Cipher, sm2_generate_keypair, sm2_encrypt_string, sm2_decrypt_string, \
    sm2_sign, sm2_verify
from darren_util.encry.darren_sm3 import hash_sm3_string, hash_sm3_bytes
from darren_util.encry.darren_sm4 import SM4Cipher, sm4_encrypt_string, sm4_decrypt_string
from darren_util.encry.js_rsa import JSRSA, js_rsa_generate_keypair, js_rsa_public_encrypt, js_rsa_private_decrypt, \
    js_rsa_private_encrypt
from .darren_devices import *
from .darren_file import *
from .darren_http import *
from .darren_http_class import DarrenHttp
from .darren_string import *
from .darren_time import *
# Import modules to make them easily accessible
from .darren_utils import *
from .fn_net_work import FNNetWork
__all__ = [
    'DarrenHttp',
    'darren_utils',
    'darren_http',
    'save_log',
    'json_parse_safe',
    'string_random_string',
    'string_get_between',
    'string_get_left',
    'string_get_right',
    'cookie_dict_to_string',
    'cookie_string_to_dict',
    'cookie_merge',
    'cookie_to_dict',
    'time_get_timestamp',
    'time_random_timestamp',
    'time_format',
    'darren_http', 'darren_http_proxy',
    # MD5相关方法
    'hash_md5_string',
    'hash_md5_bytes',
    # SHA系列方法
    'hash_sha1_string',
    'hash_sha256_string',
    'hash_sha512_string',
    'hash_sha1_bytes',
    'hash_sha256_bytes',
    'hash_sha512_bytes',
    # SM2系列方法
    'SM2Cipher',
    'sm2_generate_keypair',
    'sm2_encrypt_string',
    'sm2_decrypt_string',
    'sm2_sign',
    'sm2_verify',
    # SM3系列方法
    'hash_sm3_string',
    'hash_sm3_bytes',
    # SM4系列方法
    'SM4Cipher',
    'sm4_encrypt_string',
    'sm4_decrypt_string',
    # CRC32相关方法
    'hash_crc32_string',
    'hash_crc32_int',
    # RC4相关方法
    'rc4_encrypt_string',
    'rc4_decrypt_string',
    'RC4',
    # HMAC系列方法
    'hmac_md5',
    'hmac_sha1',
    'hmac_sha256',
    'hmac_sha512',
    'hmac_sha3_256',
    'hmac_sha3_512',
    # AES系列方法
    'AESCipher',
    'aes_encrypt_string',
    'aes_decrypt_string',
    # DES系列方法
    'DESCipher',
    'des_encrypt_string',
    'des_decrypt_string',
    # 3DES系列方法
    'TDESCipher',
    'tdes_encrypt_string',
    'tdes_decrypt_string',
    # JavaScript兼容3DES系列方法
    'TDESCipher_JS',
    'tdes_encrypt_string_js',
    'tdes_decrypt_string_js',
    # RSA系列方法
    'RSACipher',
    'rsa_generate_keypair',
    'rsa_encrypt_string',
    'rsa_decrypt_string',
    'rsa_decrypt_with_public_key',
    'rsa_sign',
    'rsa_verify',
    # JavaScript兼容RSA系列方法
    'JSRSA',
    'js_rsa_generate_keypair',
    'js_rsa_public_encrypt',
    'js_rsa_private_decrypt',
    'js_rsa_private_encrypt',
    # 文件操作系列方法
    'file_exists',
    'dir_exists',
    'file_is_use',
    'file_open',
    'file_execute',
    'file_locate',
    'file_copy',
    'file_rename',
    'file_enumerate',
    'file_size',
    'file_get_extension',
    'file_get_directory',
    'file_get_info',
    'file_get_name',
    'file_delete',
    'get_public_ip',  # 添加这行
    'url_get_domain',  # 添加这行
    'get_jsonp',  # 添加这行
    'GetHardwareInformation',
    'get_devices_id',
    #飞鸟网络验证
    'FNNetWork'
]


