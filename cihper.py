import random
import base64
import binascii
from Crypto.Cipher import AES


def aes_encrypt(text, sec_key):
    '''AES对称加密，加密通信内容
    @text 明文
    @sec_key 对称加密秘钥
    '''
    pad = 16 - len(text) % 16
    text = text + pad * chr(pad)
    encryptor = AES.new(sec_key, 2, b'0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext)
    return ciphertext.decode()


def create_sec_key(size=16):
    '''生成随机的对称加密秘钥'''
    return ''.join(random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', size)).encode()


# rsa公钥指数 65537
rsa_e = int('010001', 16)
# rsa模数
rsa_n = int('00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7', 16)


def rsa_encrypt(text):
    '''RSA非对称加密 加密AES秘钥'''
    text = text[::-1]
    rs = int(binascii.b2a_hex(text), 16)**rsa_e % rsa_n
    return format(rs, 'x').zfill(256)


def encry_post_data(data):
    params = aes_encrypt(str(data), b'0CoJUm6Qyw8W8jud')  # 第一次使用固定的aes key加密一次
    sec_key = create_sec_key()
    params = aes_encrypt(params, sec_key)  # 第二次再使用随机的aes key再加密一次
    enc_sec_key = rsa_encrypt(sec_key)  # 最后使用rsa加密 第二次随机生成的aes key
    data = {'params': params, 'encSecKey': enc_sec_key}
    return data
