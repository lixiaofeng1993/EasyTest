import json
import ddt
from common.logger import Log
from common import base_api
import unittest
import requests

test_data = []
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