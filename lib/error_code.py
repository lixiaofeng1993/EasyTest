#!/user/bin/env python
# coding=utf-8
'''
# 创 建 人: 李先生
# 文 件 名: error_code.py
# 说   明: 
# 创建时间: 2019/7/10 21:43
'''


class ErrorCode:
    """
    处理接口请求返回中的异常情况
    """
    interface_error = '系统异常！请前往【用例管理】页面，检查接口参数是否正确！'

    index_error = 'list索引错误！提取参数设置长度超出，请前往【用例管理】页面修改！'

    validators_error = '接口未设置检查点，请前往【用例管理】页面添加！'

    case_not_exit_error = '正在执行的用例不存在！请前往【用例管理】页面核实！'

    env_not_exit_error = '用例运行环境不存在！请前往【测试环境】页面核实！'

    interface_not_exit_error = '执行接口不存在！请前往【接口管理】页面核实！'

    user_not_logged_in_error = '用户未登录！请重新登录后再进行相关操作！'

    requests_error = '接口请求异常，检查请求接口代码是否正确！'

    mock_fail = '模拟接口返回值进行断言，实际未请求！'

    empty_error = '字段不能为空！'

    fields_too_long_error = '输入字段过长！'

    not_enough_error = '输入字段长度不够！'

    different_error = '两次输入的密码不一致！'

    format_error = 'email格式错误！'

    already_exists_error = '注册用户已经存在！'

    AES_key_length_error = 'app_key长度必须是16、24或者32位！请前往【测试环境】页面修改密钥！'

    random_params_error = '参数化设置错误，不符合关键字设置规则！请前往【用例管理】页面检查相关参数化配置！'

    analytical_return_value_error = '解析返回值错误！请前往【用例管理】页面检查相关参数配置！'

    eval_error = 'eval()错误，请前往【用例管理】页面核实相关参数配置！'

    sql_query_error = 'sql查询返回数据错误，请确保sql查询有返回值且是正确的！'

    extract_value_path_error = '提取参数值路径错误，请核实并写入正确的路径！'
