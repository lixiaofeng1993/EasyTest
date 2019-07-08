# !/user/bin/env python
# coding=utf-8
import json
import ddt, logging
# from common.logger import Log
from common import base_api
from common.processingJson import get_json
import requests, os, unittest

demo_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/common' + '/config' + '/demo.json'
# demo_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '\common' + '\config' + '\demo.json'

test_data = get_json(demo_path)
# log = Log()  # 初始化log
log = logging.getLogger('log')  # 初始化log
log.info('--------------------------------test_data: {}'.format(test_data))


@ddt.ddt
class Test_api(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # cls.s = requests.session()
        pass

    @ddt.data(*test_data)
    def test_api(self, data):
        """{0}"""

        log.info('2222222222222222222222222: {}'.format(data))

        # res = base_api.send_requests(self.s, data)  # 调用send_requests方法,请求接口,返回结果
        # checkpoint = data["checkpoint"]  # 检查点 checkpoint
        # res_text = res["text"]  # 返回结果
        # text = json.loads(res_text)
        # for inspect in checkpoint:
        # 	self.assertTrue(inspect["expect"] in str(text[inspect["check"]]).lower(), "检查点验证失败！")  # 断言


if __name__ == '__main__':
    unittest.main()
