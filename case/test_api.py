import json
import ddt
from common.logger import Log
from common import base_api
import unittest
import requests

test_data = [{'case_name': '性能测试用例', 'if_id': 64, 'if_name': '模拟授权', 'method': 'post', 'url': 'https://course.rest.xxbmm.com/ops', 'data_type': 'json', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjA2NDczODQyODgsImV4cGlyZVRpbWUiOjE1NjE5NDMzODQyODgsImlkZW50aWZ5IjoyMTE0OH0.LcOGPyr5UKA0WG7ExZWkdGCrXWa7Pirl3LfR1cf4CvA', 'Accept': 'application/json;charset=UTF-8'}, 'body': {'gender': '1', 'headimg': 'https://coursecdn.xxbmm.com/xxbmm-course-image/2019/05/17/17/ab2ef098-be16-4955-a144-a452815f5418.jpg', 'nickname': '道在光明', 'openid': 'ocIIn4141-6H2uTABfyz5XlTDBGU', 'source': 'APPLET', 'unionid': 'oPmunjjIzQtjk2aBI4pfkVLcA9tE'}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {}}, {'case_name': '性能测试用例', 'if_id': 18, 'if_name': '宝宝列表', 'method': 'get', 'url': 'https://course.rest.xxbmm.com/babys', 'data_type': 'data', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjA2NDczODQyODgsImV4cGlyZVRpbWUiOjE1NjE5NDMzODQyODgsImlkZW50aWZ5IjoyMTE0OH0.LcOGPyr5UKA0WG7ExZWkdGCrXWa7Pirl3LfR1cf4CvA', 'Accept': 'application/json;charset=UTF-8'}, 'body': {}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {'id': ''}}]
log = Log()  # 初始化log


@ddt.ddt
class Test_api(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.s = requests.session()

	@ddt.data(*test_data)
	def test_api(self, data):
		"""{0}"""
		res = base_api.send_requests(self.s, data)  # 调用send_requests方法,请求接口,返回结果
		checkpoint = data["checkpoint"]  # 检查点 checkpoint
		res_text = res["text"]  # 返回结果
		text = json.loads(res_text)
		for inspect in checkpoint:
			self.assertTrue(inspect["expect"] in str(text[inspect["check"]]).lower(), "检查点验证失败！")  # 断言


if __name__ == '__main__':
	unittest.main()