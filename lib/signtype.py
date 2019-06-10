import hashlib
import time
from Crypto.Cipher import AES
import base64


# 用户签名+时间戳   md5加密
def user_sign_api(data, private_key):
    api_key = private_key
    # 当前时间
    now_time = time.time()
    client_time = str(now_time).split('.')[0]
    # sign
    md5 = hashlib.md5()
    sign_str = client_time + api_key
    sign_bytes_utf8 = sign_str.encode('utf-8')
    md5.update(sign_bytes_utf8)
    sign_md5 = md5.hexdigest()
    if isinstance(data, dict):
        data['time'] = client_time
        data['sign'] = sign_md5
    return data


def encryptBase64(src):
    return base64.urlsafe_b64encode(src)  # 对AES加密字符串进行二次加密


def encryptAES(data, private_key):
    BS = 16
    pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)  # 通过 lambda 函数来对字符串进行补足，使其长度变成 16、24、32位
    app_key = private_key  # 接口参数
    iv = b'1172311105789011'
    cryptor = AES.new(app_key, AES.MODE_CBC, iv)  # AES.new()--参数需要为二进制数据
    # encrypt() --- 参数需要为二进制数据
    ciphertext = cryptor.encrypt(
        pad(data.decode('utf-8')).encode('utf-8'))  # encrypt()方法要求被加密的字符串长度必须是16、24或者32位。否则：ValueError
    return encryptBase64(ciphertext)
