#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: error_code.py
# 说   明: 
# 创建时间: 2019/7/10 21:43
'''


class ErrorCode:
    interface_error = '系统异常，检查接口参数是否正确！'

    index_error = 'list索引错误，提取参数设置长度超出！'

    validators_error = '未设置检查点！'

    case_not_exit_error = '执行用例不存在！'

    interface_not_exit_error = '执行接口不存在！'

    user_not_logged_in_error = '用户未登录！！！'

    requests_error = '接口请求异常，检查请求接口代码是否正确！'
