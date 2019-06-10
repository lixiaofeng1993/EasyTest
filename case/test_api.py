import json
import ddt
from common.logger import Log
from common import base_api
import unittest
import requests

test_data = [{'case_name': '性能测试用例', 'if_id': 64, 'if_name': '模拟授权', 'method': 'post', 'url': 'https://course.rest.xxbmm.com/ops', 'data_type': 'json', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjAwNTAwMjExNDMsImV4cGlyZVRpbWUiOjE1NjEzNDYwMjExNDMsImlkZW50aWZ5IjoyMDkxN30.Lo9kDuCEbRwsHF2fd9JruO4v-ZdO7-U3AUhrJIHwUIQ', 'Accept': 'application/json;charset=UTF-8'}, 'body': {'gender': '1', 'headimg': 'https://coursecdn.xxbmm.com/xxbmm-course-image/2019/05/17/17/ab2ef098-be16-4955-a144-a452815f5418.jpg', 'nickname': '道在光明', 'openid': 'ocIIn4141-6H2uTABfyz5XlTDBGU', 'source': 'APPLET', 'unionid': 'oPmunjjIzQtjk2aBI4pfkVLcA9tE'}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {}}, {'case_name': '性能测试用例', 'if_id': 18, 'if_name': '宝宝列表', 'method': 'get', 'url': 'https://course.rest.xxbmm.com/babys', 'data_type': 'data', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjAwNTAwMjExNDMsImV4cGlyZVRpbWUiOjE1NjEzNDYwMjExNDMsImlkZW50aWZ5IjoyMDkxN30.Lo9kDuCEbRwsHF2fd9JruO4v-ZdO7-U3AUhrJIHwUIQ', 'Accept': 'application/json;charset=UTF-8'}, 'body': {}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {'id': ''}}, {'case_name': '性能测试用例', 'if_id': 30, 'if_name': '当前宝宝免费课程', 'method': 'get', 'url': 'https://course.rest.xxbmm.com/course/futureFreeCourse/{babyId}', 'data_type': 'data', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjAwNTAwMjExNDMsImV4cGlyZVRpbWUiOjE1NjEzNDYwMjExNDMsImlkZW50aWZ5IjoyMDkxN30.Lo9kDuCEbRwsHF2fd9JruO4v-ZdO7-U3AUhrJIHwUIQ', 'Accept': 'application/json;charset=UTF-8'}, 'body': {'babyId': '$id'}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {}}, {'case_name': '性能测试用例', 'if_id': 31, 'if_name': '当前宝宝已经领取的免费课程', 'method': 'get', 'url': 'https://course.rest.xxbmm.com/course/groupByFreeGroupIdOf/{babyId}', 'data_type': 'data', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjAwNTAwMjExNDMsImV4cGlyZVRpbWUiOjE1NjEzNDYwMjExNDMsImlkZW50aWZ5IjoyMDkxN30.Lo9kDuCEbRwsHF2fd9JruO4v-ZdO7-U3AUhrJIHwUIQ', 'Accept': 'application/json;charset=UTF-8'}, 'body': {'babyId': '$id'}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {}}, {'case_name': '性能测试用例', 'if_id': 32, 'if_name': '当前宝宝课程分组列表', 'method': 'get', 'url': 'https://course.rest.xxbmm.com/course/groupByGroupIdOf/{babyId}', 'data_type': 'data', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjAwNTAwMjExNDMsImV4cGlyZVRpbWUiOjE1NjEzNDYwMjExNDMsImlkZW50aWZ5IjoyMDkxN30.Lo9kDuCEbRwsHF2fd9JruO4v-ZdO7-U3AUhrJIHwUIQ', 'Accept': 'application/json;charset=UTF-8'}, 'body': {'babyId': '$id'}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {}}, {'case_name': '性能测试用例', 'if_id': 33, 'if_name': '主页无宝宝时展示核心课信息', 'method': 'get', 'url': 'https://course.rest.xxbmm.com/course/index', 'data_type': 'data', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjAwNTAwMjExNDMsImV4cGlyZVRpbWUiOjE1NjEzNDYwMjExNDMsImlkZW50aWZ5IjoyMDkxN30.Lo9kDuCEbRwsHF2fd9JruO4v-ZdO7-U3AUhrJIHwUIQ', 'Accept': 'application/json;charset=UTF-8'}, 'body': {}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {}}, {'case_name': '性能测试用例', 'if_id': 34, 'if_name': '用户是否有查看课程详情权限', 'method': 'get', 'url': 'https://course.rest.xxbmm.com/course/read/{id}', 'data_type': 'data', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjAwNTAwMjExNDMsImV4cGlyZVRpbWUiOjE1NjEzNDYwMjExNDMsImlkZW50aWZ5IjoyMDkxN30.Lo9kDuCEbRwsHF2fd9JruO4v-ZdO7-U3AUhrJIHwUIQ', 'Accept': 'application/json;charset=UTF-8'}, 'body': {'id': '$id'}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {}}, {'case_name': '性能测试用例', 'if_id': 16, 'if_name': '打卡图片/视频上传', 'method': 'post', 'url': 'https://course.rest.xxbmm.com/baby_sign/upload', 'data_type': 'file', 'headers': {'token': 'eyJhbGciOiJIUzI1NiJ9.eyJzdGFydFRpbWUiOjE1NjAwNTAwMjExNDMsImV4cGlyZVRpbWUiOjE1NjEzNDYwMjExNDMsImlkZW50aWZ5IjoyMDkxN30.Lo9kDuCEbRwsHF2fd9JruO4v-ZdO7-U3AUhrJIHwUIQ', 'Accept': 'application/json;charset=UTF-8'}, 'body': {'file': ''}, 'checkpoint': [{'check': 'msg', 'comparator': 'eq', 'expect': '成功'}], 'extract': {}}]
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