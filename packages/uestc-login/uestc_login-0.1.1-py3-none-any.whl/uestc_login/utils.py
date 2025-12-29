# utils.py

import random
import base64
from Crypto.Cipher import AES

# 定义 AES 加密中生成随机字符串所用的字符集
AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"
]


def get_random_user_agent():
    """
    返回一个随机的 User-Agent 字符串
    :return: User-Agent 字符串
    """
    return random.choice(USER_AGENTS)


def _get_random_string(length):
    """
    生成指定长度的随机字符串
    :param length: 字符串长度
    :return: 随机字符串
    """
    return ''.join(random.choice(AES_CHARS) for _ in range(length))


def encrypt_password(password, salt):
    """
    根据前端加密逻辑对密码进行 AES 加密
    :param password: 原始密码
    :param salt: 加密盐值 (pwdEncryptSalt)
    :return: Base64 编码的加密后密码
    """
    key = salt.encode('utf-8')
    iv = _get_random_string(16).encode('utf-8')
    plaintext = (_get_random_string(64) + password).encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # PKCS7 填充
    block_size = AES.block_size
    padding_length = block_size - len(plaintext) % block_size
    padded_plaintext = plaintext + bytes([padding_length]) * padding_length

    encrypted_bytes = cipher.encrypt(padded_plaintext)
    return base64.b64encode(encrypted_bytes).decode('utf-8')