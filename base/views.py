import os
from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.conf import settings
from django.http import StreamingHttpResponse
from base.models import Project, Sign, Environment, Interface, Case, Plan, Report
from django.contrib.auth.models import User  # django自带user
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Q  # 与或非 查询
from lib.execute import Test_execute, get_user  # 执行接口
from djcelery.models import PeriodicTask, CrontabSchedule, IntervalSchedule
from datetime import timedelta, datetime
from lib.swagger import AnalysisJson
import time
import json
import logging
# from base.page_cache import page_cache  # redis缓存
from lib.public import get_new_report_html, DrawPie, is_number, paginator
import run_this

log = logging.getLogger('log')  # 初始化log
report_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/templates' + '/report'
# report_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '\\templates' + '\\report'
logs_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/' + 'logs'  # 拼接删除目录完整路径
# logs_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '\\' + 'logs'  # 拼接删除目录完整路径
start_time = ''  # 执行测试计划开始时间
totalTime = ''  # 执行测试计划运行时间
now_time = ''  # 饼图命名区分
class_name = ''  # 执行测试类


# 项目首页
# @login_required
# @page_cache(5)
def project_index(request):
    user_id = request.session.get('user_id', '')  # 从session中获取user_id
    if get_user(user_id):
        # prj_list = Project.objects.filter(user_id=user_id)  # 按照user_id查询项目
        prj_list = Project.objects.all()  # 按照user_id查询项目
        # project_list = []
        # for prj in prj_list:
        #     project_list.append(str(prj.prj_id))
        page = request.GET.get('page')
        contacts = paginator(prj_list, page)
        # request.session['project_list'] = project_list  # 保存项目id
        return render(request, "base/project/index.html", {"prj_list": prj_list, 'contacts': contacts})
    else:
        request.session['login_from'] = '/base/project/'
        return render(request, 'user/login_action.html')


# 增加项目
# @login_required
def project_add(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/project/'
        return render(request, 'user/login_action.html')
    else:
        sign_list = Sign.objects.all()  # 所有签名
        if request.method == 'POST':
            prj_name = request.POST['prj_name'].strip()
            if prj_name == '':  # 判断输入框
                return render(request, 'base/project/add.html', {'error': '项目名称不能为空！', "sign_list": sign_list})

            else:
                # name_same = Project.objects.filter(user_id=user_id).filter(prj_name=prj_name)
                name_same = Project.objects.filter(prj_name=prj_name)
                if name_same:
                    return render(request, 'base/project/add.html',
                                  {'error': '项目: {}，已存在！'.format(prj_name), "sign_list": sign_list})
                else:
                    description = request.POST['description']
                    sign_id = request.POST['sign']
                    sign = Sign.objects.get(sign_id=sign_id)
                    user = User.objects.get(id=user_id)
                    prj = Project(prj_name=prj_name, description=description, sign=sign, user=user)
                    prj.save()
                    log.info('add project   {}  success. project info: {} // {} '.format(prj_name, description, sign))
                    return HttpResponseRedirect("/base/project/")
        return render(request, "base/project/add.html", {"sign_list": sign_list})


# 项目编辑
# @login_required
def project_update(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/project/'
        return render(request, 'user/login_action.html')
    else:
        sign_list = Sign.objects.all()
        if request.method == 'POST':
            prj_id = request.POST['prj_id']
            prj_name = request.POST['prj_name'].strip()
            if prj_name == '':
                prj = Project.objects.get(prj_id=prj_id)
                return render(request, 'base/project/update.html',
                              {'error': '项目名称不能为空！', "prj": prj, "sign_list": sign_list})
            else:
                # name_exit = Project.objects.filter(user_id=user_id).filter(prj_name=prj_name).exclude(
                #     prj_id=prj_id)
                name_exit = Project.objects.filter(prj_name=prj_name).exclude(prj_id=prj_id)
                if name_exit:
                    prj = Project.objects.get(prj_id=prj_id)
                    return render(request, 'base/project/update.html',
                                  {'error': '项目: {}，已存在！'.format(prj_name), "prj": prj, "sign_list": sign_list})
                else:
                    description = request.POST['description']
                    sign_id = request.POST['sign_id']
                    sign = Sign.objects.get(sign_id=sign_id)
                    user = User.objects.get(id=user_id)
                    Project.objects.filter(prj_id=prj_id).update(prj_name=prj_name, description=description, sign=sign,
                                                                 user=user, update_time=datetime.now())
                    log.info('edit project   {}  success. project info: {} // {} '.format(prj_name, description, sign))
                    return HttpResponseRedirect("/base/project/")
        prj_id = request.GET['prj_id']
        prj = Project.objects.get(prj_id=prj_id)
        return render(request, "base/project/update.html", {"prj": prj, "sign_list": sign_list})


# 删除项目
# @login_required
def project_delete(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/project/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            prj_id = request.GET['prj_id']
            Project.objects.filter(prj_id=prj_id).delete()
            log.info('用户 {} 删除项目 {} 成功.'.format(user_id, prj_id))
            return HttpResponseRedirect("base/project/")


# 签名首页
# @login_required
# @page_cache(5)
def sign_index(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/sign/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            sign_list = Sign.objects.all()
            page = request.GET.get('page')
            contacts = paginator(sign_list, page)
            return render(request, "system/sign/sign_index.html", {"sign_list": contacts})


# 添加签名
# @login_required
def sign_add(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/sign/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            sign_name = request.POST['sign_name'].strip()
            if sign_name == '':
                return render(request, 'system/sign/sign_add.html', {'error': '签名名称不能为空！'})
            name_exit = Sign.objects.filter(sign_name=sign_name)
            if name_exit:
                return render(request, 'system/sign/sign_add.html', {'error': '签名: {}，已存在！'.format(sign_name)})
            description = request.POST['description']
            username = request.session.get('user', '')
            sign = Sign(sign_name=sign_name, description=description, update_user=username)
            sign.save()
            log.info('add sign   {}  success.  sign info： {} '.format(sign_name, description))
            return HttpResponseRedirect("/base/sign/")
        return render(request, "system/sign/sign_add.html")


# 更新签名
# @login_required
def sign_update(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/sign/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            sign_id = request.POST['sign_id']
            sign_name = request.POST['sign_name'].strip()
            if sign_name == '':
                sign = Sign.objects.get(sign_id=sign_id)
                return render(request, 'system/sign/sign_update.html', {'error': '签名名称不能为空！', "sign": sign})
            name_exit = Sign.objects.filter(sign_name=sign_name).exclude(sign_id=sign_id)
            if name_exit:
                sign = Sign.objects.get(sign_id=sign_id)
                return render(request, 'system/sign/sign_update.html',
                              {'error': '签名: {}，已存在！'.format(sign_name), "sign": sign})
            description = request.POST['description']
            username = request.session.get('user', '')
            Sign.objects.filter(sign_id=sign_id).update(sign_name=sign_name, description=description,
                                                        update_time=datetime.now(), update_user=username)
            log.info('edit sign   {}  success.  sign info： {} '.format(sign_name, description))
            return HttpResponseRedirect("/base/sign/")
        sign_id = request.GET['sign_id']
        sign = Sign.objects.get(sign_id=sign_id)
        return render(request, "system/sign/sign_update.html", {"sign": sign})


# 删除签名
# @login_required
def sign_delete(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/sign/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            sign_id = request.GET['sign_id']
            Sign.objects.filter(sign_id=sign_id).delete()
            log.info('用户 {} 删除签名 {} 成功.'.format(user_id, sign_id))
            return HttpResponseRedirect("base/sign/")


# 测试环境首页
# @login_required
# @page_cache(5)
def env_index(request):
    user_id = request.session.get('user_id', '')
    if get_user(user_id):
        # project_list = request.session.get('project_list', [])
        # env_list = []
        # for project_id in project_list:
        # env = Environment.objects.filter(project_id=int(project_id))
        envs = Environment.objects.all()
        # if env:
        #     env_list.append(env)
        page = request.GET.get('page')
        contacts = paginator(envs, page)
        return render(request, "base/env/index.html", {"contacts": contacts})
    else:
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')


# 设置默认headers
# @login_required
def set_headers(request):
    """设置默认headers"""
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            env_id = request.GET.get('env_id', '')
            make = request.GET.get('make', '')
            env = Environment.objects.get(env_id=env_id)
            env_name = env.env_name
            set_header = env.set_headers
            if make:
                if set_header:
                    set_header = eval(set_header)['header']
                    return JsonResponse(set_header)
                else:
                    return JsonResponse('0', safe=False)
            else:
                return render(request, "base/env/set_headers.html",
                              {'env_id': env_id, 'env_name': env_name, 'env': set_header})

        elif request.method == 'POST':
            content = request.POST.get('content', '')
            env_id = request.POST.get('env_id', '')
            now_time = datetime.now()
            username = request.session.get('user', '')
            Environment.objects.filter(env_id=env_id).update(set_headers=content, update_time=now_time,
                                                             update_user=username)
            log.info(
                'env {} set headers success. headers info: {} '.format(env_id, content))
            return HttpResponseRedirect("/base/env/")


# 添加环境
# @login_required
def env_add(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')
    else:
        # prj_list = Project.objects.filter(user_id=user_id)
        prj_list = Project.objects.all()
        if request.method == 'POST':
            env_name = request.POST['env_name'].strip()
            if env_name == '':
                return render(request, 'base/env/add.html', {'name_error': '环境名称不能为空！', "prj_list": prj_list})
            # name_same = Environment.objects.filter(project__user_id=user_id).filter(env_name=env_name)
            name_exit = Environment.objects.filter(env_name=env_name)
            if name_exit:
                return render(request, 'base/env/add.html',
                              {'name_error': '环境: {}，已存在！'.format(env_name), "prj_list": prj_list})
            prj_id = request.POST['prj_id']
            project = Project.objects.get(prj_id=prj_id)
            url = request.POST['url'].strip()
            if url == '':
                return render(request, 'base/env/add.html', {'url_error': 'url不能为空！', "prj_list": prj_list})
            private_key = request.POST['private_key']
            description = request.POST['description']
            is_swagger = request.POST['is_swagger']
            username = request.session.get('user', '')
            if is_swagger == '1':
                Environment.objects.filter(is_swagger=1).update(is_swagger=0)
            env = Environment(env_name=env_name, url=url, project=project, private_key=private_key,
                              description=description, is_swagger=is_swagger, update_user=username)
            env.save()
            log.info(
                'add env   {}  success.  env info： {} // {} // {} // {} // {} '.format(env_name, project, url,
                                                                                       private_key,
                                                                                       description, is_swagger))
            return HttpResponseRedirect("/base/env/")
        return render(request, "base/env/add.html", {"prj_list": prj_list})


# 测试环境更新
# @login_required
def env_update(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')
    else:
        # prj_list = Project.objects.filter(user_id=user_id)
        prj_list = Project.objects.all()
        if request.method == 'POST':
            env_id = request.POST['env_id']
            env_name = request.POST['env_name'].strip()
            if env_name == '':
                env = Environment.objects.get(env_id=env_id)
                return render(request, 'base/env/update.html',
                              {'name_error': '环境名称不能为空！', "env": env, "prj_list": prj_list})
            # name_exit = Environment.objects.filter(project__user_id=user_id).filter(env_name=env_name).exclude(
            #     env_id=env_id)
            name_exit = Environment.objects.filter(env_name=env_name).exclude(env_id=env_id)
            if name_exit:
                env = Environment.objects.get(env_id=env_id)
                return render(request, 'base/env/update.html',
                              {'name_error': '环境: {}，已存在！'.format(env_name), "env": env, "prj_list": prj_list})
            prj_id = request.POST['prj_id']
            project = Project.objects.get(prj_id=prj_id)
            url = request.POST['url'].strip()
            if url == '':
                env = Environment.objects.get(env_id=env_id)
                return render(request, 'base/env/update.html',
                              {'url_error': 'url不能为空！', "env": env, "prj_list": prj_list})
            private_key = request.POST['private_key']
            description = request.POST['description']
            is_swagger = request.POST['is_swagger']
            username = request.session.get('user', '')
            if is_swagger == '1':
                Environment.objects.filter(is_swagger=1).update(is_swagger=0)
            Environment.objects.filter(env_id=env_id).update(env_name=env_name, url=url, project=project,
                                                             private_key=private_key, description=description,
                                                             update_time=datetime.now(), is_swagger=is_swagger,
                                                             update_user=username)
            log.info(
                'edit env   {}  success.  env info： {} // {} // {} // {} // {}'.format(env_name, project, url,
                                                                                       private_key,
                                                                                       description, is_swagger))
            return HttpResponseRedirect("/base/env/")
        env_id = request.GET['env_id']
        env = Environment.objects.get(env_id=env_id)
        return render(request, "base/env/update.html", {"env": env, "prj_list": prj_list})


# 删除测试环境
# @login_required
def env_delete(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            env_id = request.GET['env_id']
            Environment.objects.filter(env_id=env_id).delete()
            log.info('用户 {} 删除环境 {} 成功.'.format(user_id, env_id))
            return HttpResponseRedirect("base/env/")


# 接口首页
# @login_required
# @page_cache(5)
def interface_index(request):
    user_id = request.session.get('user_id', '')
    if get_user(user_id):
        # project_list = request.session.get('project_list', [])
        # if_list = []
        # for project_id in project_list:
        interface = Interface.objects.all()
        # if interface:
        #     if_list.append(interface)
        page = request.GET.get('page')
        contacts = paginator(interface, page)
        return render(request, "base/interface/index.html", {"contacts": contacts})
    else:
        request.session['login_from'] = '/base/interface/'
        return render(request, 'user/login_action.html')


# 接口搜索功能
# @login_required
def interface_search(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id', '')
        if get_user(user_id):
            search = request.POST.get('search', '').strip()
            # project_list = request.session.get('project_list', [])
            if_list = []
            # interface_lists = []
            # for project_id in project_list:  # 跨项目查询
            if not search:
                return HttpResponse('0')
            else:
                if search in ['get', 'post', 'delete', 'put']:  # 请求方式查询
                    interface_list = Interface.objects.filter(method__contains=search)
                elif search in ['data', 'json']:  # 数据传输类型查询
                    interface_list = Interface.objects.filter(data_type__contains=search)
                else:
                    try:
                        if isinstance(int(search), int):  # ID查询
                            interface_list = Interface.objects.filter(if_id__exact=search)
                            if not interface_list:
                                interface_list = Interface.objects.filter(if_name__contains=search)
                    except ValueError:
                        interface_list = Interface.objects.filter(
                            Q(if_name__contains=search) | Q(project__prj_name__contains=search))  # 接口名称、项目名称查询
                if not interface_list:  # 查询为空
                    return HttpResponse('1')
                else:
                    for interface in interface_list:
                        interface_dict = {'if_id': str(interface.if_id), 'if_name': interface.if_name,
                                          'project': interface.project.prj_name, 'method': interface.method,
                                          'data_type': interface.data_type, 'is_sign': interface.is_sign,
                                          'description': interface.description,
                                          'update_time': str(interface.update_time).split('.')[0],
                                          'update_user': interface.update_user}
                        if_list.append(interface_dict)
                    return HttpResponse(str(if_list))
        else:
            return HttpResponse('2')


# 添加接口
# @login_required
def interface_add(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/interface/'
        return render(request, 'user/login_action.html')
    else:
        # prj_list = Project.objects.filter(user_id=user_id)
        prj_list = Project.objects.all()
        if request.method == 'POST':
            if_name = request.POST['if_name']
            if if_name.strip() == '':
                return HttpResponse('接口名称不能为空！')
            # name_same = Interface.objects.filter(project__user_id=user_id).filter(if_name=if_name)
            name_same = Interface.objects.filter(if_name=if_name)
            if name_same:
                return HttpResponse('接口: {}，已存在！'.format(if_name))
            prj_id = request.POST['prj_id']
            project = Project.objects.get(prj_id=prj_id)
            url = request.POST['url']
            if url.strip() == '':
                return HttpResponse('url不能为空！')
            method = request.POST.get('method', '')
            if method == '':
                return HttpResponse('请选择接口的请求方式！')
            data_type = request.POST['data_type']
            is_sign = request.POST.get('is_sign', '')
            is_headers = request.POST.get('is_headers', '')
            if is_sign == '':
                return HttpResponse('请设置接口是否需要签名！')
            description = request.POST['description']
            request_header_data = request.POST['request_header_data']
            request_body_data = request.POST['request_body_data']
            response_header_data = request.POST['response_header_data']
            response_body_data = request.POST['response_body_data']
            username = request.session.get('user', '')
            interface = Interface(if_name=if_name, url=url, project=project, method=method, data_type=data_type,
                                  is_sign=is_sign, description=description, request_header_param=request_header_data,
                                  request_body_param=request_body_data, response_header_param=response_header_data,
                                  response_body_param=response_body_data, is_header=is_headers, update_user=username)
            interface.save()
            log.info(
                'add interface  {}  success.  interface info： {} // {} // {} // {} // {} // {} // {} // {} // {} // {} '.format(
                    if_name, project, url, method, data_type, is_sign, description, request_header_data,
                    request_body_data, response_header_data, response_body_data, is_header=is_headers))
            return HttpResponseRedirect("/base/interface/")
        return render(request, "base/interface/add.html", {"prj_list": prj_list})


# 接口编辑
# @login_required
def interface_update(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/interface/'
        return render(request, 'user/login_action.html')
    else:
        # prj_list = Project.objects.filter(user_id=user_id)
        prj_list = Project.objects.all()
        if request.method == 'POST':
            if_id = request.POST['if_id']
            interface = Interface.objects.get(if_id=if_id)
            request_header_param_list = interface_get_params(interface.request_header_param)
            request_body_param_list = interface_get_params(interface.request_body_param)
            response_header_param_list = interface_get_params(interface.response_header_param)
            response_body_param_list = interface_get_params(interface.response_body_param)
            if interface.method == 'get':
                method = 0
            elif interface.method == 'post':
                method = 1
            elif interface.method == 'delete':
                method = 2
            elif interface.method == 'put':
                method = 3
            else:
                method = ''
            if interface.is_sign == 0:
                is_sign = 0
            elif interface.is_sign == 1:
                is_sign = 1
            else:
                is_sign = ''
            if_name = request.POST['if_name'].strip()
            if if_name == '':
                return render(request, 'base/interface/update.html',
                              {'name_error': '接口名称不能为空！', "interface": interface,
                               'request_header_param_list': request_header_param_list,
                               'request_body_param_list': request_body_param_list, 'method': method, 'is_sign': is_sign,
                               'response_header_param_list': response_header_param_list,
                               'response_body_param_list': response_body_param_list,
                               "prj_list": prj_list})
            # name_same = Interface.objects.filter(project__user_id=user_id).filter(if_name=if_name).exclude(
            #     if_id=if_id)
            name_same = Interface.objects.filter(if_name=if_name).exclude(if_id=if_id)
            if name_same:
                return render(request, 'base/interface/update.html',
                              {'name_error': '接口：{}，已存在！'.format(if_name), "interface": interface,
                               'request_header_param_list': request_header_param_list,
                               'request_body_param_list': request_body_param_list, 'method': method, 'is_sign': is_sign,
                               'response_header_param_list': response_header_param_list,
                               'response_body_param_list': response_body_param_list,
                               "prj_list": prj_list})
            prj_id = request.POST['prj_id']
            project = Project.objects.get(prj_id=prj_id)
            url = request.POST['url'].strip()
            if url == '':
                return render(request, 'base/interface/update.html',
                              {'url_error': '接口url不能为空！', "interface": interface,
                               'request_header_param_list': request_header_param_list,
                               'request_body_param_list': request_body_param_list, 'method': method, 'is_sign': is_sign,
                               'response_header_param_list': response_header_param_list,
                               'response_body_param_list': response_body_param_list,
                               "prj_list": prj_list})
            method = request.POST.get('method', '')
            if method == '':
                return render(request, 'base/interface/update.html',
                              {'method_error': '请选择接口请求方式！', "interface": interface,
                               'request_header_param_list': request_header_param_list,
                               'request_body_param_list': request_body_param_list, 'method': method, 'is_sign': is_sign,
                               'response_header_param_list': response_header_param_list,
                               'response_body_param_list': response_body_param_list,
                               "prj_list": prj_list})
            data_type = request.POST['data_type']
            is_sign = request.POST.get('is_sign', '')
            is_headers = request.POST.get('is_headers', '')
            if is_sign == '':
                return render(request, 'base/interface/update.html',
                              {'sign_error': '请选择接口是否需要签名！', "interface": interface,
                               'request_header_param_list': request_header_param_list,
                               'request_body_param_list': request_body_param_list, 'method': method, 'is_sign': is_sign,
                               'response_header_param_list': response_header_param_list,
                               'response_body_param_list': response_body_param_list,
                               "prj_list": prj_list})
            description = request.POST['description']
            request_header_data_list = request.POST.getlist('request_header_data', [])
            request_header_data = interface_format_params(request_header_data_list)
            request_body_data_list = request.POST.getlist('request_body_data', [])
            request_body_data = interface_format_params(request_body_data_list)
            response_header_data_list = request.POST.getlist('response_header_data', [])
            response_header_data = interface_format_params(response_header_data_list)
            response_body_data_list = request.POST.getlist('response_body_data', [])
            response_body_data = interface_format_params(response_body_data_list)
            username = request.session.get('user', '')
            Interface.objects.filter(if_id=if_id).update(if_name=if_name, url=url, project=project, method=method,
                                                         data_type=data_type, is_header=is_headers,
                                                         is_sign=is_sign, description=description,
                                                         request_header_param=request_header_data,
                                                         request_body_param=request_body_data,
                                                         response_header_param=response_header_data,
                                                         response_body_param=response_body_data,
                                                         update_time=datetime.now(), update_user=username)
            log.info(
                'edit interface  {}  success.  interface info： {} // {} // {} // {} // {} // {} // {} // {} // {} // {}// {} '.format(
                    if_name, project, url, method, data_type, is_sign, description, request_header_data,
                    request_body_data,
                    response_header_data, response_body_data, is_headers))
            return HttpResponseRedirect("/base/interface/")
        if_id = request.GET['if_id']
        interface = Interface.objects.get(if_id=if_id)
        request_header_param_list = interface_get_params(interface.request_header_param)
        request_body_param_list = interface_get_params(interface.request_body_param)
        response_header_param_list = interface_get_params(interface.response_header_param)
        response_body_param_list = interface_get_params(interface.response_body_param)
        if interface.method == 'get':
            method = 0
        elif interface.method == 'post':
            method = 1
        elif interface.method == 'delete':
            method = 2
        elif interface.method == 'put':
            method = 3
        else:
            method = ''
        if interface.is_sign == 0:
            is_sign = 0
        elif interface.is_sign == 1:
            is_sign = 1
        else:
            is_sign = ''
        if interface.is_header == 0:
            is_headers = 0
        elif interface.is_header == 1:
            is_headers = 1
        else:
            is_headers = ''
        return render(request, "base/interface/update.html",
                      {"interface": interface, 'request_header_param_list': request_header_param_list,
                       'request_body_param_list': request_body_param_list, 'method': method, 'is_sign': is_sign,
                       'response_header_param_list': response_header_param_list,
                       'response_body_param_list': response_body_param_list, 'is_headers': is_headers,
                       "prj_list": prj_list})


# 解析数据库中格式化前的参数
def interface_get_params(params):
    if params:
        param_list = []
        for i in range(len(eval(params))):
            request_header_param = eval(params)[i]['var_name']
            param_list.append(request_header_param)
        return param_list
    else:
        return []


# 格式化存入数据库中的参数
def interface_format_params(params_list):
    if params_list:
        var = []
        for i in range(len(params_list)):
            var.append({"var_name": "", "var_remark": ""})
            var[i]['var_name'] = params_list[i]
        return json.dumps(var)
    else:
        return []


# 接口删除
# @login_required
def interface_delete(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/interface/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            if_id = request.GET['if_id']
            Interface.objects.filter(if_id=if_id).delete()
            log.info('用户 {} 删除接口 {} 成功.'.format(user_id, if_id))
            return HttpResponseRedirect("base/interface/")


# 批量导入接口
def batch_import_interface(interface_params, interface, request):
    for interface_ in interface:
        if_name = interface_.get('name', '')
        method = interface_.get('method', '')
        name = Interface.objects.filter(if_name=if_name).filter(method=method)
        if name:
            log.warning('接口名称已存在. ==> {}'.format(if_name))
            continue
        else:
            url = interface_.get('url', '')
            method = interface_.get('method', '')
            data_type = interface_.get('type', '')
            headers = interface_.get('headers', '')
            body_ = interface_.get('body', '')
            if body_:
                body = interface_params[body_]
            project_id = interface_.get('prj_id', '')
            is_sign = 0
            is_headers = 0
            description = ''
            if headers[0]:
                request_header_data = [{"var_name": "", "var_remark": ""}]
                request_header_data[0]['var_name'] = headers[0]
            else:
                request_header_data = []
            if body[0]:
                request_body_data = [{"var_name": "", "var_remark": ""}]
                request_body_data[0]['var_name'] = body[0]
            else:
                request_body_data = []
            response_header_data = []
            response_body_data = []
            project = Project.objects.get(prj_id=int(project_id))
            username = request.session.get('user', '')
            log.info('interface：{} 正在批量导入中...'.format(if_name))
            interface_tbl = Interface(if_name=if_name, url=url, project=project, method=method,
                                      data_type=data_type, is_header=is_headers,
                                      is_sign=is_sign, description=description,
                                      request_header_param=json.dumps(request_header_data),
                                      request_body_param=json.dumps(request_body_data),
                                      response_header_param=response_header_data,
                                      response_body_param=response_body_data, update_user=username)
            interface_tbl.save()


# 批量导入
# @login_required
def batch_index(request):
    """批量导入"""
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        return HttpResponse('用户未登录！')
    else:
        if request.method == 'GET':
            # Interface.objects.all().delete()  # 清空接口表
            # Case.objects.all().delete()  # 清空用例表
            # Plan.objects.all().delete()  # 清空计划表
            # Report.objects.all().delete()  # 清空报告表
            try:
                env = Environment.objects.get(is_swagger=1)
                env_url = env.url
                prj_id = env.project_id
                interface_params, interface = AnalysisJson(prj_id, env_url).retrieve_data()
                log.info('项目 {} 开始批量导入...'.format(prj_id))
                batch_import_interface(interface_params, interface, request)
                return HttpResponse('批量导入成功！ ==> {}'.format(prj_id))
            except Environment.DoesNotExist:
                return HttpResponse('测试环境中未设置从swagger导入！')


# 用例首页
# @login_required
# @page_cache(5)
def case_index(request):
    user_id = request.session.get('user_id', '')
    if get_user(user_id):
        # project_list = request.session.get('project_list', [])
        # case_list = []
        # for project_id in project_list:
        # case = Case.objects.filter(project_id=int(project_id))
        cases = Case.objects.all().order_by('-case_id')
        # if case:
        #     case_list.append(case)
        page = request.GET.get('page')
        contacts = paginator(cases, page)
        return render(request, "base/case/index.html", {"contacts": contacts})
    else:
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')


# 添加用例
# @login_required
def case_add(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            case_name = request.POST.get('case_name', '')
            if case_name == '':
                return HttpResponse('用例名称不能为空！')
            # name_same = Case.objects.filter(project__user_id=user_id).filter(case_name=case_name)
            name_same = Case.objects.filter(case_name=case_name)
            if name_same:
                return HttpResponse('用例：{}， 已存在！'.format(case_name))
            prj_id = request.POST['prj_id']
            project = Project.objects.get(prj_id=prj_id)
            description = request.POST['description']
            content = request.POST.get('content')
            username = request.session.get('user', '')
            if content == '[]':
                return HttpResponse('请输入接口参数信息11！')
            case = Case(case_name=case_name, project=project, description=description,
                        content=content, update_user=username)
            case.save()
            log.info(
                'add case   {}  success. case info: {} // {} // {}'.format(case_name, project, description, content))
            return HttpResponseRedirect("/base/case/")
        # prj_list = Project.objects.filter(user_id=user_id)
        prj_list = Project.objects.all()
        return render(request, "base/case/add.html", {"prj_list": prj_list})


# 编辑用例
# @login_required
def case_update(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            case_id = request.POST['case_id']
            case_name = request.POST.get('case_name', '')
            if case_name == '':
                return HttpResponse('用例名称不能为空！')
            # name_same = Case.objects.filter(project__user_id=user_id).filter(case_name=case_name).exclude(
            #     case_id=case_id)
            name_same = Case.objects.filter(case_name=case_name).exclude(case_id=case_id)
            if name_same:
                return HttpResponse('用例：{}， 已存在！'.format(case_name))
            prj_id = request.POST['prj_id']
            project = Project.objects.get(prj_id=prj_id)
            description = request.POST['description']
            content = request.POST.get('content')
            username = request.session.get('user', '')
            if content == '[]':
                return HttpResponse('请编辑接口参数信息！')
            Case.objects.filter(case_id=case_id).update(case_name=case_name, project=project, description=description,
                                                        content=content, update_time=datetime.now(),
                                                        update_user=username)
            log.info(
                'edit case   {}  success. case info: {} // {} // {}'.format(case_name, project, description, content))
            return HttpResponseRedirect("/base/case/")
        elif request.method == 'GET':
            # prj_list = Project.objects.filter(user_id=user_id)
            prj_list = Project.objects.all()
            case_id = request.GET['case_id']
            case = Case.objects.get(case_id=case_id)
            interface = Interface.objects.filter(project_id=case.project_id).all().values()
            if_list = ''
            for i in eval(case.content):
                if_list += i['if_id'] + ','
            if eval(case.content):
                if_id = eval(case.content)[0]['if_id']  # 默认显示第一个接口名称
                if_name = eval(case.content)[0]['if_name']
            else:
                if_id = '1'
                if_name = '请选择接口'
            interface_list = []  # 返回所有接口
            for i in interface:
                interface_list.append(i)
            return render(request, 'base/case/update.html',
                          {"prj_list": prj_list, 'case': case, 'interface': interface, 'case_id': case_id,
                           'if_id': if_id, 'if_list': str(if_list), 'if_name': if_name})


# @login_required
def case_copy(request):
    """复制case"""
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            case_id = request.GET.get('case_id', '')
            case_ = Case.objects.get(case_id=case_id)
            case_name = case_.case_name
            content = case_.content
            project = case_.project
            description = case_.description
            username = request.session.get('user', '')
            case = Case(case_name=case_name, project=project, description=description, update_time=datetime.now(),
                        content=content, update_user=username)
            case.save()
            log.info(
                'copy case   {}  success. case info: {} // {} '.format(case_name, project, content))
            return HttpResponseRedirect("base/case/")


# @login_required
def case_logs(request):
    """单个用例运行日志"""
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        log_file_list = os.listdir(logs_path)
        data_list = []
        file_list = []
        now = time.strftime('%Y-%m-%d')
        for file in log_file_list:
            if 'all' in file and now in file:
                file_list.append(file)
        log.info(file_list + now + '------------------1-----------------')
        if not file_list:
            yesterday = datetime.today() + timedelta(-1)
            yesterday_format = yesterday.strftime('%Y_%m_%d')
            for file in log_file_list:
                if 'all' in file and yesterday_format in file:
                    file_list.apppend(file)
            log.info(file_list + now + yesterday_format + '------------------2-----------------')
        log.info(file_list + now + '------------------3-----------------')
        file_list.sort()
        log_file = os.path.join(logs_path, file_list[0])
        with open(log_file, 'rb') as f:
            off = -1024 * 1024
            if f.tell() < -off:
                data = f.readlines()
            else:
                f.seek(off, 2)
                data = f.readlines()
            for line in data:
                data_list.append(line.decode())
            return render(request, 'base/case/log.html', {'data': data_list, 'make': True, 'log_file': log_file})


# 删除用例
# @login_required
def case_delete(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            case_id = request.GET['case_id']
            Case.objects.filter(case_id=case_id).delete()
            log.info('用户 {} 删除用例 {} 成功.'.format(user_id, case_id))
            return HttpResponseRedirect("base/case/")


# 运行用例
# @login_required
def case_run(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        return HttpResponse('0')
    else:
        if request.method == 'POST':
            case_id = request.POST['case_id']
            env_id = request.POST['env_id']
            username = request.session.get('user', '')
            log.info('用户 {} 在 {} 环境 运行用例 {} 成功.'.format(username, env_id, case_id))
            execute = Test_execute(case_id, env_id, ['1'])
            case_result = execute.test_case()
            Case.objects.filter(case_id=case_id).update(update_user=username)
            return JsonResponse(case_result)


# 测试计划首页
# @login_required
# @page_cache(5)
def plan_index(request):
    user_id = request.session.get('user_id', '')
    if get_user(user_id):
        # project_list = request.session.get('project_list', [])
        # plan_list = []
        # for project_id in project_list:
        # plan = Plan.objects.filter(project_id=int(project_id))
        plans = Plan.objects.all().order_by('-plan_id')
        # if plan:
        #     plan_list.append(plan)
        page = request.GET.get('page')
        contacts = paginator(plans, page)
        return render(request, "base/plan/index.html", {"contacts": contacts})
    else:
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')


# 测试计划添加
# @login_required
def plan_add(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')
    else:
        # prj_list = Project.objects.filter(user_id=user_id)
        prj_list = Project.objects.all()
        if request.method == 'POST':
            plan_name = request.POST['plan_name'].strip()
            if plan_name == '':
                return render(request, 'base/plan/add.html',
                              {'name_error': '计划名称不能为空！', "prj_list": prj_list})
            # name_same = Plan.objects.filter(project__user_id=user_id).filter(plan_name=plan_name)
            name_same = Plan.objects.filter(plan_name=plan_name)
            if name_same:
                return render(request, 'base/plan/add.html',
                              {'name_error': '计划: {}，已存在！'.format(plan_name), "prj_list": prj_list})
            prj_id = request.POST['prj_id']
            project = Project.objects.get(prj_id=prj_id)
            is_locust = request.POST['is_locust']
            is_task = request.POST['is_task']
            env_id = request.POST['env_id']
            environment = Environment.objects.get(env_id=env_id)
            description = request.POST['description']
            content = request.POST.getlist("case_id")
            username = request.session.get('user', '')
            if content == []:
                return render(request, 'base/plan/add.html',
                              {'content_error': '请选择用例编号！', 'plan_name': plan_name, "prj_list": prj_list})
            if is_locust == '1':
                Plan.objects.filter(is_locust=1).update(is_locust=0)
            if is_task == '1':
                Plan.objects.filter(is_task=1).update(is_task=0)
            plan = Plan(plan_name=plan_name, project=project, environment=environment, description=description,
                        content=content, is_locust=is_locust, is_task=is_task, update_user=username)
            plan.save()
            log.info('add plan   {}  success. plan info: {} // {} // {} // {} //{} //{}'.
                     format(plan_name, project, environment, description, content, is_locust, is_task))
            return HttpResponseRedirect("/base/plan/")
        return render(request, "base/plan/add.html", {"prj_list": prj_list})


# 测试计划编辑
# @login_required
def plan_update(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')
    else:
        # prj_list = Project.objects.filter(user_id=user_id)
        prj_list = Project.objects.all()
        if request.method == 'POST':
            plan_id = request.POST['plan_id']
            plan = Plan.objects.get(plan_id=plan_id)
            environments = Environment.objects.filter(project_id=plan.project_id).all().values()
            case_list = []
            for case_id in eval(plan.content):
                case = Case.objects.get(case_id=case_id)
                case_list.append(case)
            plan_name = request.POST['plan_name'].strip()
            if plan_name == '':
                return render(request, 'base/plan/update.html',
                              {'name_error': '计划名称不能为空！', "prj_list": prj_list, 'plan': plan, 'case_list': case_list,
                               'environments': environments})
            # name_same = Plan.objects.filter(project__user_id=user_id).filter(plan_name=plan_name).exclude(
            #     plan_id=plan_id)
            name_same = Plan.objects.filter(plan_name=plan_name).exclude(plan_id=plan_id)
            if name_same:
                return render(request, 'base/plan/update.html',
                              {'name_error': '计划: {}，已存在！'.format(plan_name), "prj_list": prj_list, 'plan': plan,
                               'case_list': case_list, 'environments': environments})
            prj_id = request.POST['prj_id']
            project = Project.objects.get(prj_id=prj_id)
            is_locust = request.POST['is_locust']
            env_id = request.POST['env_id']
            is_task = request.POST['is_task']
            environment = Environment.objects.get(env_id=env_id)
            description = request.POST['description']
            content = request.POST.getlist("case_id")
            username = request.session.get('user', '')
            if content == []:
                return render(request, 'base/plan/update.html',
                              {'content_error': '请选择用例编号！', 'plan': plan, "prj_list": prj_list,
                               'case_list': case_list, 'environments': environments})
            if is_locust == '1':
                Plan.objects.filter(is_locust=1).update(is_locust=0)
            if is_task == '1':
                Plan.objects.filter(is_task=1).update(is_task=0)
            Plan.objects.filter(plan_id=plan_id).update(plan_name=plan_name, project=project, environment=environment,
                                                        description=description, content=content, is_locust=is_locust,
                                                        is_task=is_task, update_time=datetime.now(),
                                                        update_user=username)
            log.info('edit plan   {}  success. plan info: {} // {} // {} // {}'.format(plan_name, project, environment,
                                                                                       description, content))
            return HttpResponseRedirect("/base/plan/")
        plan_id = request.GET['plan_id']
        plan = Plan.objects.get(plan_id=plan_id)
        environments = Environment.objects.filter(project_id=plan.project_id).all().values()
        case_list = []
        for case_id in eval(plan.content):
            try:
                case = Case.objects.get(case_id=case_id)
                case_list.append(case)
            except Case.DoesNotExist as e:
                log.error('计划 {} 中的 用例 {} 已被删除！！！'.format(plan.plan_name, case_id))
                plans = Plan.objects.all()
                page = request.GET.get('page')
                contacts = paginator(plans, page)
                return render(request, "base/plan/index.html",
                              {"contacts": contacts, 'error': '计划 {} 中的 用例 {} 已被删除！！！'.format(plan.plan_name, case_id)})
        return render(request, "base/plan/update.html",
                      {"prj_list": prj_list, 'plan': plan, 'case_list': case_list, 'environments': environments})


# 删除测试计划
# @login_required
def plan_delete(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            plan_id = request.GET['plan_id']
            Plan.objects.filter(plan_id=plan_id).delete()
            log.info('用户 {} 删除计划 {} 成功.'.format(user_id, plan_id))
            return HttpResponseRedirect("base/plan/")


# 运行测试计划
# @login_required
def plan_run(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        return HttpResponse('用户未登录')
    else:
        if request.method == 'POST':
            global totalTime, start_time, now_time
            begin_time = time.clock()
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            now_time = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
            plan_id = request.POST['plan_id']
            plan = Plan.objects.get(plan_id=plan_id)
            env_id = plan.environment.env_id
            case_id_list = eval(plan.content)
            case_num = len(case_id_list)
            content = []
            pass_num = 0
            fail_num = 0
            error_num = 0
            i = 0
            for case_id in case_id_list:
                execute = Test_execute(case_id, env_id, case_id_list)
                case_result = execute.test_case()
                if isinstance(case_result, dict):
                    content.append(case_result)
                else:
                    return HttpResponse(case_result)
            end_time = time.clock()
            totalTime = str(end_time - begin_time) + 's'
            for step in content:
                for s in step['step_list']:
                    if s["result"] == "pass":
                        pass_num += 1
                        i += 1
                        s['id'] = i
                    if s["result"] == "fail":
                        fail_num += 1
                        i += 1
                        s['id'] = i
                    if s["result"] == "error":
                        error_num += 1
                        i += 1
                        s['id'] = i
            pic_name = DrawPie(pass_num, fail_num, error_num)
            report_name = plan.plan_name + "-" + str(start_time)
            username = request.session.get('user', '')
            report = Report(plan=plan, report_name=report_name, content=content, case_num=case_num,
                            pass_num=pass_num, fail_num=fail_num, error_num=error_num, pic_name=pic_name,
                            totalTime=totalTime, startTime=start_time, update_user=username)
            report.save()
            Plan.objects.filter(plan_id=plan_id).update(make=0, update_time=datetime.now(), update_user=username)
            return HttpResponse(plan.plan_name + " 执行成功！")


# @login_required
def plan_unittest_run(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        return HttpResponse('用户未登录')
    else:
        if request.method == 'POST':
            global totalTime, start_time, now_time
            plan_id = request.POST['plan_id']
            plan = Plan.objects.get(plan_id=plan_id)
            env = Environment.objects.get(env_id=plan.environment_id)
            case_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'case')
            if not os.path.exists(case_path): os.mkdir(case_path)  # 如果不存在这个logs文件夹，就自动创建一个
            py_path = os.path.join(case_path, 'test_api.py')
            test_data = []
            for case_id in eval(plan.content):
                try:
                    case = Case.objects.get(case_id=int(case_id))
                except Case.DoesNotExist as e:
                    log.error('计划：{} 中的 用例 {} 已被删除！'.format(plan.plan_name, case_id))
                    return HttpResponse('计划：{} 中的 用例 {} 已被删除！'.format(plan.plan_name, case_id))
                set_headers = env.set_headers
                if_list = eval(case.content)
                for i in if_list:
                    interface = Interface.objects.get(if_id=i['if_id'])
                    test_data.append(
                        {'case_name': case.case_name, 'if_id': interface.if_id, 'if_name': interface.if_name,
                         'method': interface.method, 'url': env.url + interface.url, 'data_type': interface.data_type,
                         'headers': eval(set_headers)['header'], 'body': i['body'], 'checkpoint': i['validators'],
                         'extract': i['extract']})
            with open(py_path, 'w', encoding='utf-8') as f:
                data = '# !/user/bin/env python\n' + '# coding=utf-8\n' + 'import json\n' + 'import ddt\n' + 'from common.logger import Log\n' + 'from common import base_api\n' + 'import unittest\n' + 'import requests\n' \
                       + '\ntest_data = {}'.format(
                    test_data) + '\n' + 'log = Log()  # 初始化log\n\n\n' + '@ddt.ddt\n' + 'class Test_api(unittest.TestCase):\n\t' + \
                       '@classmethod\n\t' + 'def setUpClass(cls):\n\t\t' + 'cls.s = requests.session()\n\n\t' + '@ddt.data(*test_data)\n\t' + 'def test_api(self, data):\n\t\t' + '"""{0}"""\n\t\t' \
                       + 'res = base_api.send_requests(self.s, data)  # 调用send_requests方法,请求接口,返回结果\n\t\t' + 'checkpoint = data["checkpoint"]  # 检查点 checkpoint\n\t\t' + 'res_text = res["text"]  # 返回结果\n\t\t' + \
                       'text = json.loads(res_text)\n\t\t' + "for inspect in checkpoint:\n\t\t\t" + 'self.assertTrue(inspect["expect"] in str(text[inspect["check"]]).lower(), "检查点验证失败！")  # 断言\n\n\n' \
                       + "if __name__ == '__main__':\n\t" + 'unittest.main()'
                f.write(data)
            run_this.run_email()
            report_name = get_new_report_html(report_path)
            username = request.session.get('user', '')
            Plan.objects.filter(plan_id=plan_id).update(make=1, report_name=report_name, update_time=datetime.now(),
                                                        update_user=username)
            log.info('-------------------------->plan_unittest_run plan_id: {}'.format(plan_id))
            return HttpResponse(plan.plan_name + " 执行成功！")


# 定时任务
# @login_required
# @page_cache(5)
def timing_task(request):
    user_id = request.session.get('user_id', '')
    if get_user(user_id):
        task_list = PeriodicTask.objects.all()
        task_count = PeriodicTask.objects.all().count()  # 统计数
        periodic_list = IntervalSchedule.objects.all()  # 周期任务 （如：每隔1小时执行1次）
        crontab_list = CrontabSchedule.objects.all()  # 定时任务 （如：某年月日的某时，每天的某时）
        return render(request, "system/task/task_index.html",
                      {"tasks": task_list, "taskcounts": task_count, "periodics": periodic_list,
                       "crontabs": crontab_list})
    else:
        request.session['login_from'] = '/base/timing_task/'
        return render(request, 'user/login_action.html')


# @login_required
def task_logs(request):
    """定时任务运行日志"""
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        task_log_path = '/var/celery_logs/celery_worker_err.log'
        data_list = []
        with open(task_log_path, 'rb') as f:
            off = -1024 * 1024
            if f.tell() < -off:
                data = f.readlines()
            else:
                f.seek(off, 2)
                data = f.readlines()
            for line in data:
                data_list.append(line.decode())
            return render(request, 'system/task/log.html', {'data': data_list, 'make': True, 'log_file': task_log_path})


# 查看报告页面
# @login_required
# @page_cache(5)
def report_page(request):
    if request.method == 'GET':
        user_id = request.session.get('user_id', '')
        if get_user(user_id):
            plan_id = request.GET.get('plan_id', '')
            if plan_id:
                report_list = Report.objects.filter(plan_id=plan_id).order_by('-report_id')
            else:
                report_list = Report.objects.all().order_by('-report_id')
            page = request.GET.get('page')
            contacts = paginator(report_list, page)
            return render(request, "base/report_page/report_page.html",
                          {"contacts": contacts, 'plan_id': plan_id})
        else:
            request.session['login_from'] = '/base/report_page/'
            return render(request, 'user/login_action.html')


# 显示日志信息
# @login_required
def report_logs(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/report_page/'
        return render(request, 'user/login_action.html')
    else:
        report_id = request.GET.get('report_id')
        plan_id = Report.objects.get(report_id=report_id).plan_id
        make = Plan.objects.get(plan_id=plan_id).make
        if make:  # unittest日志
            file_list = []
            now = time.strftime('%Y-%m-%d')
            log_file_list = os.listdir(logs_path)
            for file in log_file_list:
                if file[0].isdigit() and now in file:
                    file_list.append(file)
            if not file_list:
                return render(request, 'base/report_page/log.html', {'unicode': True})
            data_list = []
            file_list.sort()
            log_file = os.path.join(logs_path, file_list[0])
            try:
                with open(log_file, 'rb') as f:
                    off = -1024 * 1024
                    if f.tell() < -off:
                        data = f.readlines()
                    else:
                        f.seek(off, 2)
                        data = f.readlines()
                    for line in data:
                        data_list.append(line.decode())
                return render(request, 'base/report_page/log.html', {'data': data_list, 'make': True})
            except UnicodeDecodeError:
                return render(request, 'base/report_page/log.html', {'unicode': True})

        else:
            try:
                report = Report.objects.get(report_id=report_id)
            except Report.DoesNotExist:
                return render(request, "base/report_page/log.html")
            else:
                report_content = eval(report.content)
                for case in report_content:
                    global class_name
                    class_name = case['class_name']
                return render(request, "base/report_page/log.html",
                              {"report": report, 'plan_id': plan_id, "report_content": report_content,
                               'class_name': class_name})


# 展示报告
# @login_required
def report_index(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/report_page/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            report_id = request.GET.get('report_id', '')
            if not report_id:
                return render(request, "report.html")
            try:
                report = Report.objects.get(report_id=report_id)
            except Report.DoesNotExist:
                return render(request, 'report.html')
            plan_id = Report.objects.get(report_id=report_id).plan_id
            make = Plan.objects.get(plan_id=plan_id).make
            plan_name = Plan.objects.get(plan_id=plan_id).report_name
            if make:  # unittest报告
                log.info('---->report_index plan_id: {} , plan_name: {}'.format(plan_id, plan_name))
                return render(request, '{}'.format(plan_name))
            report = Report.objects.get(report_id=report_id)
            case_num = report.case_num
            pass_num = report.pass_num
            fail_num = report.fail_num
            error_num = report.error_num
            report_content = eval(report.content)
            for case in report_content:
                global class_name
                class_name = case['class_name']
            return render(request, "report.html",
                          {"report": report, 'plan_id': plan_id, 'case_num': case_num, "error_num": error_num,
                           'pass_num': pass_num, 'fail_num': fail_num, "report_content": report_content,
                           'img_name': str(now_time) + 'pie.png', 'class_name': class_name})


# @login_required
def report_search(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        return HttpResponse('0')
    else:
        if request.method == 'POST':
            result = request.POST['result']
            report_id = request.POST['report_id']
            try:
                report = Report.objects.get(report_id=report_id)
            except Report.DoesNotExist:
                return render(request, "report.html")
            report_content = eval(report.content)
            if result not in ['pass', 'fail']:
                return HttpResponse(str(report_content))
            for case in report_content:
                global class_name
                class_name = case['class_name']
                step_list = case['step_list']
                case['step_list'] = []
                for step in step_list:
                    if result == step['result']:
                        case['step_list'].append(step)
                    else:
                        pass
            return HttpResponse(str(report_content))


# 删除报告
# @login_required
def report_delete(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/report_page/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            report_id = request.GET['report_id']
            Report.objects.filter(report_id=report_id).delete()
            log.info('用户 {} 删除报告 {} 成功.'.format(user_id, report_id))
            return HttpResponseRedirect("base/report_page/")


# 下载unittest报告
# @login_required
def file_download(request):
    # do something...
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/report_page/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            plan_id = request.GET.get('plan_id', '')
            name = request.GET.get('log_file', '')
            if plan_id:
                name = Plan.objects.get(plan_id=plan_id).report_name
                if not name:
                    if plan_id:
                        report_list = Report.objects.filter(plan_id=plan_id).order_by('-report_id')
                    else:
                        report_list = Report.objects.all().order_by('-report_id')
                    page = request.GET.get('page')
                    contacts = paginator(report_list, page)
                    return render(request, "base/report_page/report_page.html",
                                  {"contacts": contacts, 'plan_id': plan_id,
                                   'error': '计划 {} 不存在unittest报告'.format(
                                       plan_id)})

            def file_iterator(file_name, chunk_size=512):
                with open(file_name, encoding='utf-8') as f:
                    while True:
                        c = f.read(chunk_size)
                        if c:
                            yield c
                        else:
                            break

            response = StreamingHttpResponse(file_iterator(name))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(name)
            log.info('用户 {} 下载测试报告或日志文件：{} 成功.'.format(user_id, name))
            return response


# locust页面
# @login_required
# @page_cache(5)
def performance_index(request):
    if request.method == 'GET':
        user_id = request.session.get('user_id', '')
        if get_user(user_id):
            return render(request, 'base/performance/performance.html')
        else:
            request.session['login_from'] = '/base/performance/'
            return render(request, 'user/login_action.html')


# 添加用户
# @login_required
# @page_cache(5)
def user_index(request):
    user_id = request.session.get('user_id', '')
    if get_user(user_id):
        user = User.objects.all()
        page = request.GET.get('page')
        contacts = paginator(user, page)
        return render(request, 'system/user/user_index.html', {"contacts": contacts})

    else:
        request.session['login_from'] = '/base/user/'
        return render(request, 'user/login_action.html')


# 异步请求数据
def findata(request):
    if request.method == 'GET':
        get_type = request.GET["type"]
        if get_type == "get_all_if_by_prj_id":
            prj_id = request.GET["prj_id"]
            # 返回字典列表
            if_list = Interface.objects.filter(project=prj_id).all().values()
            # list(if_list)将QuerySet转换成list
            return JsonResponse(list(if_list), safe=False)
        if get_type == "get_if_by_search_name":
            search_name = request.GET["search_name"]
            prj_id = request.GET["prj_id"]
            # 返回字典列表
            if_list = Interface.objects.filter(project=prj_id).filter(if_name__contains=search_name).all().values()
            # list(if_list)将QuerySet转换成list
            return JsonResponse(list(if_list), safe=False)
        if get_type == "get_if_by_if_id":
            if_id = request.GET["if_id"]
            # 查询并将结果转换为json
            interface = Interface.objects.filter(if_id=if_id).values()
            return JsonResponse(list(interface), safe=False)
        if get_type == "get_env_by_prj_id":
            prj_id = request.GET["prj_id"]
            # 查询并将结果转换为json
            env = Environment.objects.filter(project_id=prj_id).values()
            return JsonResponse(list(env), safe=False)
        if get_type == "get_case_by_case_id":  # 增加 get_case_by_case_id 类型，编辑 用例 使用
            case_id = request.GET["case_id"]
            # 查询并将结果转换为json
            case = Case.objects.filter(case_id=case_id).values()
            return JsonResponse(list(case), safe=False)
        if get_type == "get_all_case_by_prj_id":
            prj_id = request.GET["prj_id"]
            # 查询并将结果转换为json
            env = Case.objects.filter(project_id=prj_id).values()
            return JsonResponse(list(env), safe=False)
        if get_type == 'get_log':
            log_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/logs'
            log_file_list = os.listdir(log_path)
            file_list = []
            now = time.strftime('%Y-%m-%d')
            for file in log_file_list:
                if 'all' in file and now in file:
                    file_list.append(file)
            if not file_list:
                yesterday = datetime.today() + timedelta(-1)
                yesterday_format = yesterday.strftime('%Y_%m_%d')
                for file in log_file_list:
                    if 'all' in file and yesterday_format in file:
                        file_list.apppend(file)
            file_list.sort()
            log_file = os.path.join(log_path, file_list[0])
            data_list = []
            with open(log_file, 'r', encoding='utf-8') as f:
                off = -1024 * 1024
                if f.tell() < -off:
                    data = f.readlines()
                else:
                    f.seek(off, 2)
                    data = f.readlines()
                    # data = f.readlines()
            for i in data:
                data_list.append(i.replace('True', 'true').replace('False', 'false').replace('None', 'null'))
            return JsonResponse(data_list, safe=False)
        if get_type == 'get_task_log':
            task_log_path = '/var/celery_logs/celery_worker_err.log'
            data_list = []
            with open(task_log_path, 'r', encoding='utf-8') as f:
                off = -1024 * 1024
                if f.tell() < -off:
                    data = f.readlines()
                else:
                    f.seek(off, 2)
                    data = f.readlines()
                    # data = f.readlines()
            for i in data:
                data_list.append(i.replace('True', 'true').replace('False', 'false').replace('None', 'null'))
            return JsonResponse(data_list, safe=False)
