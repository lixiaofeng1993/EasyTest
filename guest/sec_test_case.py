import unittest, hashlib
import requests, time
from Crypto.Cipher import AES
import base64
from binascii import b2a_hex, a2b_hex
import json


#
# class GetEventListTest(unittest.TestCase):
#     """查询发布会信息（带用户认证）"""
#
#     def test_get_event_list(self):
#         """查询成功"""
#         auth_user = ('lixiaofeng', 'fengzi802300')
#         r = requests.get('http://localhost:8000/api/sec_get_event_list/', auth=auth_user, params={'eid': 1})
#         result = r.json()
#         self.assertEqual(result['status'], 200)
#         self.assertEqual(result['message'], 'success')


class AddEventTest(unittest.TestCase):
    def setUp(self):
        self.url = 'http://localhost:8000/api/sec_add_event/'
        # apikey
        self.api_key = '&Guest-Bugmaster'
        # 当前时间
        now_time = time.time()
        self.client_time = str(now_time).split('.')[0]
        # sign
        md5 = hashlib.md5()
        sign_str = self.client_time + self.api_key
        sign_bytes_utf8 = sign_str.encode('utf-8')
        md5.update(sign_bytes_utf8)
        self.sign_md5 = md5.hexdigest()

    def test_add_event_success(self):
        """添加成功"""
        payload = {"eid": 8, "name": "一加8手机发布会", "limit": 2000, "status": "0", "address": "深圳宝体会展中心",
                   "start_time": "2018-09-15 22:40:00", 'time': self.client_time, 'sign': self.sign_md5}
        r = requests.post(self.url, data=payload)
        result = r.json()
        self.assertEqual(result['status'], 200)
        self.assertEqual(result['message'], 'add event success')


# class AESTest(unittest.TestCase):
#     def setUp(self):
#         BS = 16
#         self.pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)  # 通过 lambda 函数来对字符串进行补足，使其长度变成 16、24、32位
#
#         self.base_url = 'http://localhost:8000/api/sec_get_guest_list/'
#         self.app_key = 'W7v4D60fds2Cmk2U'  # 接口参数
#
#     def encryptBase64(self, src):
#         return base64.urlsafe_b64encode(src)  # 对AES加密字符串进行二次加密
#
#     def encryptAES(self, src, key):
#         """生成AES密文"""
#         iv = b'1172311105789011'
#         cryptor = AES.new(key, AES.MODE_CBC, iv)  # AES.new()--参数需要为二进制数据
#         # encrypt() --- 参数需要为二进制数据
#         ciphertext = cryptor.encrypt(
#             self.pad(src.decode('utf-8')).encode('utf-8'))  # encrypt()方法要求被加密的字符串长度必须是16、24或者32位。否则：ValueError
#         return self.encryptBase64(ciphertext)
#
#     def test_aes_interface(self):
#         """接口 aes 测试"""
#         payload = {'name': '187'}
#         # 加密
#         encodeed = self.encryptAES(json.dumps(payload).encode('utf-8'), self.app_key.encode('utf-8')).decode('utf-8')
#         print(encodeed)
#         r = requests.get(self.base_url, params={'data': encodeed})
#         result = r.json()
#         print(result)
#         self.assertEqual(result['status'], 200)
#         self.assertEqual(result['message'], 'success')


if __name__ == '__main__':
    unittest.main()
