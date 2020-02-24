# -*- coding: utf-8 -*-
import os, time, json, logging, threading, platform, re, zipfile, requests
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .tasks import delete_logs, run_plan, stop_locust, test_httprunner, test_plan
from django.http import StreamingHttpResponse
from base.models import Project, Sign, Environment, Interface, Case, Plan, Report, LocustReport, DebugTalk, \
    ModularTable, UserPower
from django.contrib.auth.models import User  # django自带user
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Q  # 与或非 查询
from lib.execute import Test_execute, get_user, is_superuser, limits_of_authority  # 执行接口
from djcelery.models import PeriodicTask, CrontabSchedule, IntervalSchedule, PeriodicTasks
from datetime import timedelta, datetime
from lib.swagger import AnalysisJson
from django.shortcuts import render_to_response
# from base.page_cache import page_cache  # redis缓存
from lib.public import DrawPie, paginator, pagination_data
from lib.error_code import ErrorCode
from lib.except_check import project_info_logic, sign_info_logic, env_info_logic, interface_info_logic, format_params, \
    case_info_logic, plan_info_logic, header_value_error  # 自定义异常逻辑
from django.views.generic import ListView
from django.conf import settings
from lib.helper import delete_performance, copy_debugtalk

# import paramiko
# from stat import S_ISDIR as isdir
# from lib import readConfig

log = logging.getLogger('log')  # 初始化log
logs_path = os.path.join(os.getcwd(), 'logs')  # 拼接删除目录完整路径
start_time = ''  # 执行测试计划开始时间
totalTime = ''  # 执行测试计划运行时间
now_time = ''  # 饼图命名区分
class_name = ''  # 执行测试类


# 项目列表
# @page_cache(5)
@method_decorator(login_required, name='dispatch')
class ProjectIndex(ListView):
    model = Project
    template_name = 'base/project/index.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def dispatch(self, *args, **kwargs):
        return super(ProjectIndex, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        project_list = Project.objects.all().order_by('-prj_id')
        return project_list
        # superuser = User.objects.get(id=user_id).is_superuser
        # if superuser:
        #     return Project.objects.all().order_by('-prj_id')
        # else:
        #     return Project.objects.filter(user_id=user_id).order_by('-prj_id')

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        context.update(data)
        user_id = self.request.session.get('user_id', '')
        model_list = limits_of_authority(user_id)
        context.update({"model_list": model_list, "page": self.page})
        return context


def project_add(request):
    """
    增加项目
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/project/'
        return render(request, 'user/login_action.html')
    else:
        sign_list = Sign.objects.all()  # 所有签名
        model_list = limits_of_authority(user_id)
        if request.method == 'POST':
            prj_name = request.POST['prj_name'].strip()

            msg = project_info_logic(prj_name)
            if msg != 'ok':  # 判断输入框
                log.error('project add error：{}'.format(msg))
                info = {'error': msg, "sign_list": sign_list, "model_list": model_list, "page": "1"}
                return render(request, 'base/project/add.html', info)
            else:
                description = request.POST['description']
                sign_id = request.POST['sign']
                sign = Sign.objects.get(sign_id=sign_id)
                user = User.objects.get(id=user_id)
                prj = Project(prj_name=prj_name, description=description, sign=sign, user=user)
                prj.save()
                log.info('add project   {}  success. project info: {} // {} '.format(prj_name, description, sign))
                return HttpResponseRedirect("/base/project/")
        elif request.method == 'GET':
            if not sign_list:
                querysetlist = []
                sign_dict = [{"id": 1, "name": "不签名", "type": "无"}, {"id": 2, "name": "md5加密", "type": "md5加密"},
                             {"id": 3, "name": "用户认证", "type": "用户认证"}, {"id": 4, "name": "AES算法", "type": "AES算法"}]
                for signer in sign_dict:
                    querysetlist.append(
                        Sign(sign_id=signer["id"], sign_name=signer["name"], sign_type=signer["type"], description="",
                             update_time=datetime.now(), update_user="root"))
                Sign.objects.bulk_create(querysetlist)
                sign_list = Sign.objects.all()
            info = {"sign_list": sign_list, "model_list": model_list}
            return render(request, "base/project/add.html", info)


def project_update(request):
    """
    项目编辑
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/project/'
        return render(request, 'user/login_action.html')
    else:
        sign_list = Sign.objects.all()
        model_list = limits_of_authority(user_id)
        if request.method == 'POST':
            prj_id = request.POST['prj_id']
            page = request.POST['page']
            prj_name = request.POST['prj_name'].strip()

            msg = project_info_logic(prj_name, prj_id)
            if msg != 'ok':
                log.error('project update error：{}'.format(msg))
                prj = Project.objects.get(prj_id=prj_id)
                info = {'error': msg, "prj": prj, "sign_list": sign_list, "model_list": model_list, "page": page}
                return render(request, 'base/project/update.html', info)
            else:
                description = request.POST['description']
                sign_id = request.POST['sign_id']
                sign = Sign.objects.get(sign_id=sign_id)
                user = User.objects.get(id=user_id)
                Project.objects.filter(prj_id=prj_id).update(prj_name=prj_name, description=description, sign=sign,
                                                             user=user, update_time=datetime.now())
                log.info('edit project   {}  success. project info: {} // {} '.format(prj_name, description, sign))
                return HttpResponseRedirect("/base/project/?page={}".format(page))
        elif request.method == 'GET':
            prj_id = request.GET['prj_id']
            page = request.GET.get("page", "1")
            user_id_belong = Project.objects.get(prj_id=prj_id).user_id
            if user_id == user_id_belong:
                prj = Project.objects.get(prj_id=prj_id)
                info = {"prj": prj, "sign_list": sign_list, "model_list": model_list, "page": page}
                return render(request, "base/project/update.html", info)
            else:
                info = {'error': '非本人创建项目，不可以修改！', "model_list": model_list}
                return render(request, "base/project/update.html", info)


def project_delete(request):
    """
    删除项目
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/project/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            prj_id = request.GET['prj_id']
            page = request.GET.get("page", "1")
            Project.objects.filter(prj_id=prj_id).delete()
            log.info('用户 {} 删除项目 {} 成功.'.format(user_id, prj_id))
            return HttpResponseRedirect("base/project/?page={}".format(page))


# 签名列表
# @page_cache(5)
@method_decorator(login_required, name='dispatch')
class SignIndex(ListView):
    model = Sign
    template_name = 'system/sign/sign_index.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def dispatch(self, *args, **kwargs):
        return super(SignIndex, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        sign_list = Sign.objects.all().order_by("-sign_id")
        return sign_list

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        context.update(data)
        user_id = self.request.session.get('user_id', '')
        model_list = limits_of_authority(user_id)
        context.update({"model_list": model_list, "page": self.page})
        return context


def sign_add(request):
    """
    添加签名
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/sign/'
        return render(request, 'user/login_action.html')
    else:
        model_list = limits_of_authority(user_id)
        if request.method == 'POST':
            sign_name = request.POST['sign_name'].strip()
            sign_type = request.POST['sign_type'].strip()

            msg = sign_info_logic(sign_name)
            if msg != 'ok':
                log.error('sign add error：{}'.format(msg))
                info = {'error': msg, "model_list": model_list, "page": "1"}
                return render(request, 'system/sign/sign_add.html', info)
            else:
                description = request.POST['description']
                username = request.session.get('user', '')
                sign = Sign(sign_name=sign_name, description=description, update_user=username, sign_type=sign_type)
                sign.save()
                log.info('add sign   {}  success.  sign info： {} '.format(sign_name, description))
                return HttpResponseRedirect("/base/sign/")
        elif request.method == 'GET':
            return render(request, "system/sign/sign_add.html", {"model_list": model_list})


def sign_update(request):
    """
    更新签名
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/sign/'
        return render(request, 'user/login_action.html')
    else:
        model_list = limits_of_authority(user_id)
        if request.method == 'POST':
            sign_id = request.POST['sign_id']
            page = request.POST.get("page", "1")
            sign_name = request.POST['sign_name'].strip()
            sign_type = request.POST['sign_type'].strip()

            msg = sign_info_logic(sign_name, sign_id)
            if msg != 'ok':
                log.error('sign update error：{}'.format(msg))
                sign = Sign.objects.get(sign_id=sign_id)
                info = {'error': msg, "sign": sign, "page": page, "model_list": model_list}
                return render(request, 'system/sign/sign_update.html', info)
            else:
                description = request.POST['description']
                username = request.session.get('user', '')
                Sign.objects.filter(sign_id=sign_id).update(
                    sign_name=sign_name, description=description, update_time=datetime.now(), update_user=username,
                    sign_type=sign_type)
                log.info('edit sign   {}  success.  sign info： {} '.format(sign_name, description))
                return HttpResponseRedirect("/base/sign/?page={}".format(page))
        elif request.method == 'GET':
            sign_id = request.GET['sign_id']
            page = request.GET.get("page", "1")
            sign = Sign.objects.get(sign_id=sign_id)
            info = {"sign": sign, "model_list": model_list, "page": page}
            return render(request, "system/sign/sign_update.html", info)


def sign_delete(request):
    """
    删除签名
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/sign/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            sign_id = request.GET['sign_id']
            page = request.GET.get("page", "1")
            Sign.objects.filter(sign_id=sign_id).delete()
            log.info('用户 {} 删除签名 {} 成功.'.format(user_id, sign_id))
            return HttpResponseRedirect("base/sign/?page={}".format(page))


# 测试环境列表
# @page_cache(5)
@method_decorator(login_required, name='dispatch')
class EnvIndex(ListView):
    model = Environment
    template_name = 'base/env/index.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def dispatch(self, *args, **kwargs):
        return super(EnvIndex, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        env_list = Environment.objects.all().order_by('-env_id')
        return env_list

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        context.update(data)
        user_id = self.request.session.get('user_id', '')
        model_list = limits_of_authority(user_id)
        context.update({"model_list": model_list, "page": self.page})
        return context


def set_headers(request):
    """
    设置默认headers
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            env_id = request.GET.get('env_id', '')
            page = request.GET.get('page', '')
            make = request.GET.get('make', '')
            env = Environment.objects.get(env_id=env_id)
            env_name = env.env_name
            set_header = env.set_headers
            model_list = limits_of_authority(user_id)
            if make:
                if set_header:
                    set_header = eval(set_header)['header']
                    return JsonResponse(set_header)
                else:
                    return JsonResponse('0', safe=False)
            else:
                info = {'env_id': env_id, 'env_name': env_name, 'env': set_header, "model_list": model_list,
                        "page": page}
                return render(request, "base/env/set_headers.html", info)
        elif request.method == 'POST':
            content = request.POST.get('content', '')

            msg = header_value_error(content)
            if msg != 'ok':
                log.error('set headers error：{}'.format(msg))
                return HttpResponse(msg)
            else:
                env_id = request.POST.get('env_id', '')
                now_time = datetime.now()
                username = request.session.get('user', '')
                Environment.objects.filter(env_id=env_id).update(set_headers=content, update_time=now_time,
                                                                 update_user=username)
                log.info('env {} set headers success. headers info: {} '.format(env_id, content))
                return HttpResponse("ok")


def set_mock(request):
    """
    设置默认mock
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            if_id = request.GET.get('if_id', '')
            make = request.GET.get('make', '')
            interface = Interface.objects.get(if_id=if_id)
            if_name = interface.if_name
            set_mock = interface.set_mock
            model_list = limits_of_authority(user_id)
            if make:
                if set_mock:
                    set_mock = eval(set_mock)['mock']
                    return JsonResponse(set_mock)
                else:
                    return JsonResponse('0', safe=False)
            else:
                info = {'if_id': if_id, 'if_name': if_name, 'env': set_mock, "model_list": model_list}
                return render(request, "base/interface/set_mock.html", info)
        elif request.method == 'POST':
            content = request.POST.get('content', '')
            if_id = request.POST.get('if_id', '')
            now_time = datetime.now()
            username = request.session.get('user', '')
            Interface.objects.filter(if_id=if_id).update(set_mock=content, update_time=now_time, update_user=username)
            log.info('interface {} set mock success. mock info: {} '.format(if_id, content))
            return HttpResponseRedirect("/base/interface/")


def env_add(request):
    """
    添加环境
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')
    else:
        prj_list = Project.objects.all()
        model_list = limits_of_authority(user_id)
        if request.method == 'POST':
            env_name = request.POST['env_name'].strip()
            url = request.POST['url'].strip()

            msg = env_info_logic(env_name, url)
            if msg != 'ok':
                log.error('env add error：{}'.format(msg))
                info = {'error': msg, "prj_list": prj_list, "model_list": model_list, "page": "1"}
                return render(request, 'base/env/add.html', info)
            else:
                prj_id = request.POST['prj_id']
                project = Project.objects.get(prj_id=prj_id)
                private_key = request.POST['private_key']
                description = request.POST['description']
                is_swagger = request.POST['is_swagger']
                username = request.session.get('user', '')
                if is_swagger == '1':
                    Environment.objects.filter(is_swagger=1).update(is_swagger=0)
                env = Environment(env_name=env_name, url=url, project=project, private_key=private_key,
                                  description=description, is_swagger=is_swagger, update_user=username)
                env.save()
                log.info('add env   {}  success.  env info： {} // {} // {} // {} // {} '
                         .format(env_name, project, url, private_key, description, is_swagger))
                return HttpResponseRedirect("/base/env/")
        elif request.method == 'GET':
            info = {"prj_list": prj_list, "model_list": model_list}
            return render(request, "base/env/add.html", info)


def env_update(request):
    """
    测试环境更新
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')
    else:
        prj_list = Project.objects.all()
        model_list = limits_of_authority(user_id)
        if request.method == 'POST':
            env_id = request.POST['env_id']
            page = request.POST.get("page", "1")
            env_name = request.POST['env_name'].strip()
            url = request.POST['url'].strip()

            msg = env_info_logic(env_name, url, env_id)
            if msg != 'ok':
                log.error('env update error：{}'.format(msg))
                env = Environment.objects.get(env_id=env_id)
                info = {'error': msg, "env": env, "prj_list": prj_list, "model_list": model_list, "page": page}
                return render(request, 'base/env/update.html', info)
            else:
                prj_id = request.POST['prj_id']
                project = Project.objects.get(prj_id=prj_id)

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
                log.info('edit env   {}  success.  env info： {} // {} // {} // {} // {}'
                         .format(env_name, project, url, private_key, description, is_swagger))
                return HttpResponseRedirect("/base/env/?page={}".format(page))
        elif request.method == 'GET':
            env_id = request.GET['env_id']
            page = request.GET.get("page", "1")
            env = Environment.objects.get(env_id=env_id)
            info = {"env": env, "prj_list": prj_list, "model_list": model_list, "page": page}
            return render(request, "base/env/update.html", info)


def env_delete(request):
    """
    删除测试环境
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/env/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            env_id = request.GET['env_id']
            page = request.GET.get("page", "1")
            Environment.objects.filter(env_id=env_id).delete()
            log.info('用户 {} 删除环境 {} 成功.'.format(user_id, env_id))
            return HttpResponseRedirect("base/env/?page={}".format(page))


# 接口列表
@method_decorator(login_required, name='dispatch')
class InterfaceIndex(ListView):
    model = Interface
    template_name = 'base/interface/index.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def dispatch(self, *args, **kwargs):
        return super(InterfaceIndex, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        interface_list = Interface.objects.all().order_by('-if_id')
        return interface_list

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        context.update(data)
        user_id = self.request.session.get('user_id', '')
        model_list = limits_of_authority(user_id)
        context.update({"model_list": model_list, "page": self.page})
        return context


def interface_copy(request):
    """
    复制interface
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            if_id = request.GET.get('if_id', '')
            interface_ = Interface.objects.get(if_id=if_id)
            if_name = interface_.if_name + 'copy'
            url = interface_.url
            method = interface_.method
            data_type = interface_.data_type
            is_sign = interface_.is_sign
            is_header = interface_.is_header
            mock = interface_.set_mock
            skip = interface_.skip
            description = interface_.description
            request_header_param = interface_.request_header_param
            request_body_param = interface_.request_body_param
            response_header_param = interface_.response_header_param
            response_body_param = interface_.response_body_param
            project = interface_.project
            username = request.session.get('user', '')
            interface = Interface(if_name=if_name, url=url, project=project, method=method, data_type=data_type,
                                  is_sign=is_sign, description=description, request_header_param=request_header_param,
                                  request_body_param=request_body_param, response_header_param=response_header_param,
                                  response_body_param=response_body_param, is_header=is_header, update_user=username,
                                  set_mock=mock, skip=skip)
            interface.save()
            log.info(
                'add interface  {}  success.  interface info： {} // {} // {} // {} // {} // {} // {} // {} // {} // {} '
                    .format(if_name, project, url, method, data_type, is_sign, description, request_header_param,
                            request_body_param, response_header_param, response_body_param, is_header))
            return HttpResponseRedirect("base/interface/")


def interface_search(request):
    """
    接口搜索功能
    :param request:
    :return:
    """
    if request.method == 'POST':
        user_id = request.session.get('user_id', '')
        if get_user(user_id):
            search = request.POST.get('search', '').strip()
            if_list = []
            interface_list = []
            if not search:
                return HttpResponse('0')
            else:
                if search in ['get', 'post', 'delete', 'put']:  # 请求方式查询
                    interface_list = Interface.objects.filter(method__contains=search)
                elif search in ['data', 'json']:  # 数据传输类型查询
                    interface_list = Interface.objects.filter(data_type__contains=search)
                else:
                    try:
                        if isinstance(int(search), int):
                            if search in ['0', '1']:  # 设置header、签名查询
                                interface_list = Interface.objects.filter(
                                    Q(is_header=search) | Q(is_sign=search) | Q(if_id__exact=search) | Q(
                                        if_name__contains=search))
                            else:  # ID查询
                                interface_list = Interface.objects.filter(
                                    Q(if_id__exact=search) | Q(if_name__contains=search))
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
                                          'response_header_param': interface.response_header_param,
                                          'update_time': str(interface.update_time).split('.')[0],
                                          'update_user': interface.update_user}
                        if_list.append(interface_dict)
                    return HttpResponse(str(if_list))
        else:
            return HttpResponse('2')


def interface_add(request):
    """
    添加接口
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/interface/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            if_name = request.POST['if_name'].strip()
            prj_id = request.POST['prj_id']
            url = request.POST['url'].strip()
            method = request.POST.get('method', '')
            skip = request.POST.get('skip', '').strip()
            data_type = request.POST['data_type']
            is_sign = request.POST.get('is_sign', '')
            is_headers = request.POST.get('is_headers', '')
            mock = request.POST.get('mock', '')
            request_header_data = request.POST['request_header_data']
            request_body_data = request.POST['request_body_data']
            # response_header_data = request.POST['response_header_data']
            # response_body_data = request.POST['response_body_data']

            msg = interface_info_logic(if_name, url, method, is_sign, data_type, is_headers, request_header_data,
                                       request_body_data)

            if msg != 'ok':
                log.error('interface add error：{}'.format(msg))
                return HttpResponse(msg)
            description = request.POST['description']
            username = request.session.get('user', '')
            if is_headers == '1':
                Interface.objects.filter(project_id=prj_id).filter(is_header=1).update(is_header=0)
            project = Project.objects.get(prj_id=prj_id)
            interface = Interface(if_name=if_name, url=url, project=project, method=method, data_type=data_type,
                                  is_sign=is_sign, description=description, request_header_param=request_header_data,
                                  request_body_param=request_body_data, is_header=is_headers, update_user=username,
                                  set_mock=mock, skip=skip)
            interface.save()
            log.info(
                'add interface  {}  success.  interface info： {} // {} // {} // {} // {} // {} // {} // {} //  '
                    .format(if_name, project, url, method, data_type, is_sign, description, request_header_data,
                            request_body_data, is_headers))
            return HttpResponseRedirect("/base/interface/")
        elif request.method == 'GET':
            prj_list = Project.objects.all()
            model_list = limits_of_authority(user_id)
            info = {"prj_list": prj_list, "model_list": model_list}
            return render(request, "base/interface/add.html", info)


def interface_update(request):
    """
    接口编辑
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/interface/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            if_id = request.POST['if_id']
            if_name = request.POST['if_name'].strip()
            prj_id = request.POST['prj_id']
            url = request.POST['url'].strip()
            skip = request.POST['skip'].strip()
            method = request.POST.get('method', '')
            page = request.POST.get('page', '1')
            data_type = request.POST['data_type']
            is_sign = request.POST.get('is_sign', '')
            is_headers = request.POST.get('is_headers', '')
            mock = request.POST.get('mock', '')
            request_header_data_list = request.POST.get('request_header_data', [])
            request_header_data = interface_format_params(request_header_data_list)
            request_body_data_list = request.POST.get('request_body_data', [])
            request_body_data = interface_format_params(request_body_data_list)
            # response_header_data_list = request.POST.get('response_header_data', [])
            # response_header_data = interface_format_params(response_header_data_list)
            # response_body_data_list = request.POST.get('response_body_data', [])
            # response_body_data = interface_format_params(response_body_data_list)

            msg = interface_info_logic(if_name, url, method, is_sign, data_type, is_headers, request_header_data,
                                       request_body_data, if_id)
            if msg != 'ok':
                log.error('interface update error：{}'.format(msg))
                return HttpResponse(msg)
            else:
                description = request.POST['description']
                username = request.session.get('user', '')
                if is_headers == '1':
                    Interface.objects.filter(project_id=prj_id).filter(is_header=1).update(is_header=0)
                project = Project.objects.get(prj_id=prj_id)
                Interface.objects.filter(if_id=if_id).update(if_name=if_name, url=url, project=project, method=method,
                                                             data_type=data_type, is_header=is_headers,
                                                             is_sign=is_sign, description=description,
                                                             request_header_param=request_header_data, skip=skip,
                                                             request_body_param=request_body_data, set_mock=mock,
                                                             update_time=datetime.now(), update_user=username)
                log.info(
                    'edit interface  {}  success.  interface info： {} // {} // {} // {} // {} // {} // {} // {} // {} '.format(
                        if_name, project, url, method, data_type, is_sign, description, request_header_data,
                        request_body_data, is_headers))
                return HttpResponse("ok")
        elif request.method == 'GET':
            prj_list = Project.objects.all()
            if_id = request.GET['if_id']
            page = request.GET['page']
            interface = Interface.objects.get(if_id=if_id)
            request_header_param_list = interface_get_params(interface.request_header_param)
            request_body_param_list = interface_get_params(interface.request_body_param)
            # response_header_param_list = interface_get_params(interface.response_header_param)
            # response_body_param_list = interface_get_params(interface.response_body_param)
            method, is_sign, is_headers, mock = format_params(interface)
            model_list = limits_of_authority(user_id)
            info = {"interface": interface, 'request_header_param_list': request_header_param_list,
                    'request_body_param_list': request_body_param_list, 'method': method, 'is_sign': is_sign,
                    'is_headers': is_headers, 'mock': mock, "prj_list": prj_list, "model_list": model_list,
                    "page": page}
            return render(request, "base/interface/update.html", info)


def interface_get_params(params):
    """
    解析数据库中格式化前的参数
    :param params:
    :return:
    """
    if params and params != '[]':
        param_list = []
        for i in range(len(eval(params))):
            param_list.append({"var_name": "", "var_remark": ""})
            param_list[i]['var_name'] = eval(params)[i]['var_name']
        return param_list
    else:
        return []


def interface_format_params(params_list):
    """
    格式化存入数据库中的参数
    :param params_list:
    :return:
    """
    if params_list:
        var = []
        params_list = eval(params_list)
        for i in range(len(params_list)):
            var.append({"var_name": "", "var_remark": ""})
            var[i]['var_name'] = params_list[i]['var_name']
        return json.dumps(var)
    else:
        return []


def interface_delete(request):
    """
    接口删除
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/interface/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            if_id = request.GET['if_id']
            page = request.GET.get("page", "1")
            Interface.objects.filter(if_id=if_id).delete()
            log.info('用户 {} 删除接口 {} 成功.'.format(user_id, if_id))
            return HttpResponseRedirect("base/interface/?page={}".format(page))


# 执行导入的异步线程
class BatchInterface(threading.Thread):
    def run(self):
        for key, value in self.interface.items():
            log.info(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " {} ==== BatchInterface ".format(self.getName(), ))
            if_name = value.get('name', '').strip()
            method = value.get('method', '')
            tags = value.get('tags', '')
            url = value.get('url', '')
            data_type = value.get('type', '')
            headers = value.get('headers', '')
            body = value.get('body', '')
            project_id = value.get('prj_id', '')
            is_sign = 0
            is_headers = 0
            mock = '0'
            description = ''
            request_header_data = []
            request_body_data = []
            response_body_data = []
            if isinstance(headers, dict):
                for k, v in headers.items():
                    headers_data = {}
                    headers_data['var_name'] = k
                    if isinstance(v, dict):
                        v = json.dumps(v)
                    headers_data['var_remark'] = ''
                    request_header_data.append(headers_data)
            if isinstance(body, dict):
                for k, v in body.items():
                    body_data = {}
                    body_data['var_name'] = k
                    if isinstance(v, dict):
                        v = json.dumps(v)
                    body_data['var_remark'] = ''
                    request_body_data.append(body_data)
            project = Project.objects.get(prj_id=int(project_id))
            username = self.request.session.get('user', '')
            interface_list = Interface.objects.filter(if_name=if_name).filter(url=url).filter(method=method)
            if interface_list:
                for name in interface_list:
                    Interface.objects.filter(if_id=name.if_id).update(if_name=if_name, url=url, project=project,
                                                                      method=method, response_header_param=tags,
                                                                      data_type=data_type, description=description,
                                                                      request_header_param=json.dumps(
                                                                          request_header_data),
                                                                      request_body_param=json.dumps(request_body_data),
                                                                      update_time=datetime.now(), update_user=username)
                log.warning('接口名称已存在，更新接口参数中... ==> {}'.format(if_name))
            else:
                log.info('接口名称：{}， 正在批量导入中...'.format(if_name))
                interface_tbl = Interface(if_name=if_name, url=url, project=project, method=method,
                                          data_type=data_type, is_header=is_headers,
                                          is_sign=is_sign, description=description,
                                          request_header_param=json.dumps(request_header_data),
                                          request_body_param=json.dumps(request_body_data),
                                          response_header_param=tags, set_mock=mock,
                                          response_body_param=response_body_data, update_user=username)
                interface_tbl.save()

    def __init__(self, interface, request, user_id):
        threading.Thread.__init__(self)
        self.interface = interface
        self.request = request
        self.user_id = user_id
        self.setDaemon(True)  # 守护线程


def batch_index(request):
    """
    批量导入接口
    :param request:
    :return:
    """
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
                interface = AnalysisJson(prj_id, env_url).retrieve_data()
                if interface == 'error':
                    return HttpResponse('请求swagger url 发生错误，请联系管理员！')
                elif isinstance(interface, dict):
                    log.info('项目 {} 开始批量导入...'.format(prj_id))
                    batch = BatchInterface(interface, request, user_id)
                    batch.start()
                    return HttpResponse('批量导入成功！ ==> {}'.format(prj_id))
            except Environment.DoesNotExist:
                return HttpResponse('测试环境中未设置从swagger导入！')


# 用例首页
@method_decorator(login_required, name='dispatch')
class CaseIndex(ListView):
    model = Case
    template_name = 'base/case/index.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def dispatch(self, *args, **kwargs):
        return super(CaseIndex, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        case_list = Case.objects.all().order_by('-case_id')
        return case_list

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        context.update(data)
        user_id = self.request.session.get('user_id', '')
        model_list = limits_of_authority(user_id)
        context.update({"model_list": model_list, "page": self.page})
        return context


def case_add(request):
    """
    添加用例
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            case_name = request.POST.get('case_name', '').strip()
            weight = request.POST.get('weight', 1)
            content = request.POST.get('content')

            msg = case_info_logic(case_name, content)
            if msg != 'ok':
                log.error('case add error：{}'.format(msg))
                return HttpResponse(msg)
            else:
                prj_id = request.POST['prj_id']
                project = Project.objects.get(prj_id=prj_id)
                description = request.POST['description']
                username = request.session.get('user', '')
                case = Case(case_name=case_name, project=project, description=description,
                            content=content, update_user=username, weight=weight)
                case.save()
                log.info(
                    'add case   {}  success. case info: {} // {} // {} // {}'.format(case_name, project, description,
                                                                                     content, weight))
                return HttpResponse("ok")
        elif request.method == 'GET':
            prj_list = Project.objects.all()
            model_list = limits_of_authority(user_id)
            info = {"prj_list": prj_list, "model_list": model_list}
            return render(request, "base/case/add.html", info)


def case_update(request):
    """
    编辑用例
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            case_id = request.POST['case_id']
            case_name = request.POST.get('case_name', '').strip()
            weight = request.POST.get('weight', 1)
            content = request.POST.get('content')

            msg = case_info_logic(case_name, content, case_id, user_id)
            if msg != 'ok':
                log.error('case update error：{}'.format(msg))
                return HttpResponse(msg)
            else:
                prj_id = request.POST['prj_id']
                project = Project.objects.get(prj_id=prj_id)
                description = request.POST['description']
                username = request.session.get('user', '')
                Case.objects.filter(case_id=case_id).update(case_name=case_name, project=project,
                                                            description=description,
                                                            content=content, update_time=datetime.now(),
                                                            update_user=username, weight=weight)
                log.info('edit case   {}  success. case info: {} // {} // {} // {}'
                         .format(case_name, project, description, content, weight))
                return HttpResponse("ok")
        elif request.method == 'GET':
            prj_list = Project.objects.all()
            case_id = request.GET['case_id']
            page = request.GET.get("page", "1")
            case = Case.objects.get(case_id=case_id)
            interface = Interface.objects.all().values()
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
            model_list = limits_of_authority(user_id)
            info = {"prj_list": prj_list, 'case': case, 'interface': interface, 'case_id': case_id,
                    'if_id': if_id, 'if_list': str(if_list), 'if_name': if_name, "model_list": model_list, "page": page}
            return render_to_response('base/case/update.html', info)


def case_copy(request):
    """
    复制case
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            case_id = request.GET.get('case_id', '')
            case_ = Case.objects.get(case_id=case_id)
            case_name = case_.case_name + 'copy'
            content = case_.content
            weight = case_.weight
            project = case_.project
            description = case_.description
            username = request.session.get('user', '')
            case = Case(case_name=case_name, project=project, description=description, update_time=datetime.now(),
                        content=content, update_user=username, weight=weight)
            case.save()
            log.info('copy case   {}  success. case info: {} // {} // {} '.format(case_name, project, content, weight))
            return HttpResponseRedirect("base/case/")


def case_search(request):
    """
    用例搜索功能
    :param request:
    :return:
    """
    if request.method == 'POST':
        user_id = request.session.get('user_id', '')
        if get_user(user_id):
            search = request.POST.get('search', '').strip()
            case_list = []
            if not search:
                return HttpResponse('0')
            else:
                case = Case.objects.filter(case_name__contains=search)

                if not case:  # 查询为空
                    return HttpResponse('1')
                else:
                    for case_ in case:
                        case_dict = {'case_id': str(case_.case_id), 'case_name': case_.case_name,
                                     'project': case_.project.prj_name, 'description': case_.description,
                                     'update_time': str(case_.update_time).split('.')[0],
                                     'update_user': case_.update_user, 'prj_id': case_.project.prj_id}
                        case_list.append(case_dict)
                    return HttpResponse(str(case_list))
        else:
            return HttpResponse('2')


def case_logs(request):
    """
    单个用例运行日志
    :param request:
    :return:
    """
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
        if not file_list:
            yesterday = datetime.today() + timedelta(-1)
            yesterday_format = yesterday.strftime('%Y-%m-%d')
            for file in log_file_list:
                if 'all' in file and yesterday_format in file:
                    file_list.append(file)
        try:
            file_list.sort()
            log_file = os.path.join(logs_path, file_list[0])
        except IndexError:
            for file in log_file_list:
                if 'all' in file:
                    file_list.append(file)
            file_list.sort()
            log_file = os.path.join(logs_path, file_list[-1])
        with open(log_file, 'rb') as f:
            off = -1024 * 1024
            if f.tell() < -off:
                data = f.readlines()
            else:
                f.seek(off, 2)
                data = f.readlines()
            for line in data:
                data_list.append(line.decode())
            model_list = limits_of_authority(user_id)
            info = {'data': data_list, 'make': True, 'log_file': log_file, "model_list": model_list}
            log.info('case_logs 查询日志文件名称 ===========================>>> {}'.format(log_file))
            return render(request, 'base/case/log.html', info)


def case_delete(request):
    """
    删除用例
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            case_id = request.GET['case_id']
            page = request.GET.get("page", "1")
            Case.objects.filter(case_id=case_id).delete()
            log.info('用户 {} 删除用例 {} 成功.'.format(user_id, case_id))
            return HttpResponseRedirect("base/case/?page={}".format(page))


def case_run(request):
    """
    运行用例
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        return JsonResponse({'error': ErrorCode.user_not_logged_in_error})
    else:
        if request.method == 'POST':
            case_id = request.POST['case_id']
            run_mode = request.POST['run_mode']
            case_id_list = [case_id]
            env_id = request.POST['env_id']
            username = request.session.get('user', '')
            log.info('用户 {} 在 {} 环境 运行用例 {} .'.format(username, env_id, case_id))
            execute = Test_execute(env_id, case_id_list, case_id=case_id, run_mode=run_mode)
            case_result = execute.test_case
            case_result = json.dumps(case_result, ensure_ascii=False).replace('Markup', '') \
                .replace('&#34;', '').replace('true', 'True').replace('false', 'False').replace('null', 'None')
            import urllib.parse
            case_result = eval(urllib.parse.unquote(case_result))
            Case.objects.filter(case_id=case_id).update(update_user=username)
            return JsonResponse(case_result)


# 测试计划列表
@method_decorator(login_required, name='dispatch')
class PlanIndex(ListView):
    model = Plan
    template_name = 'base/plan/index.html'
    context_object_name = 'object_list'
    paginate_by = 2

    def dispatch(self, *args, **kwargs):
        return super(PlanIndex, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        plan_list = Plan.objects.all().order_by('-plan_id')
        return plan_list

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        context.update(data)
        user_id = self.request.session.get('user_id', '')
        model_list = limits_of_authority(user_id)
        context.update({"model_list": model_list, "page": self.page})
        return context


def plan_add(request):
    """
    测试计划添加
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')
    else:
        prj_list = Project.objects.all()
        model_list = limits_of_authority(user_id)
        if request.method == 'POST':
            plan_name = request.POST['plan_name'].strip()
            content = request.POST.getlist("case_id")

            msg = plan_info_logic(plan_name, content)
            if msg != 'ok':
                log.error('plan add error：{}'.format(msg))
                info = {'error': msg, "prj_list": prj_list, "model_list": model_list}
                return render(request, 'base/plan/add.html', info)
            else:
                prj_id = request.POST['prj_id']
                project = Project.objects.get(prj_id=prj_id)
                is_locust = request.POST['is_locust']
                env_id = request.POST['env_id']
                environment = Environment.objects.get(env_id=env_id)
                description = request.POST['description']
                username = request.session.get('user', '')
                if is_locust == '1':
                    Plan.objects.filter(is_locust=1).update(is_locust=0)
                plan = Plan(plan_name=plan_name, project=project, environment=environment, description=description,
                            content=content, is_locust=is_locust, update_user=username, is_task=0)
                plan.save()
                log.info('add plan   {}  success. plan info: {} // {} // {} // {} //{} //'.
                         format(plan_name, project, environment, description, content, is_locust))
                return HttpResponseRedirect("/base/plan/")
        elif request.method == 'GET':
            info = {"prj_list": prj_list, "model_list": model_list}
            return render(request, "base/plan/add.html", info)


def plan_update(request):
    """
    测试计划编辑
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')
    else:
        prj_list = Project.objects.all()
        model_list = limits_of_authority(user_id)
        if request.method == 'POST':
            plan_id = request.POST['plan_id']
            page = request.POST.get('page', '1')
            plan_name = request.POST['plan_name'].strip()
            content = request.POST.getlist("case_id")
            plan = Plan.objects.get(plan_id=plan_id)
            environments = Environment.objects.filter(project_id=plan.project_id).all().values()
            case_list = []
            for case_id in eval(plan.content):
                case = Case.objects.get(case_id=case_id)
                case_list.append(case)

            msg = plan_info_logic(plan_name, content, plan_id)
            if msg != 'ok':
                log.error('plan update error：{}'.format(msg))
                info = {'error': msg, "prj_list": prj_list, 'plan': plan, 'case_list': case_list,
                        'environments': environments, "page": page, "model_list": model_list}
                return render(request, 'base/plan/update.html', info)
            else:
                prj_id = request.POST['prj_id']
                project = Project.objects.get(prj_id=prj_id)
                is_locust = request.POST['is_locust']
                env_id = request.POST['env_id']
                environment = Environment.objects.get(env_id=env_id)
                description = request.POST['description']

                username = request.session.get('user', '')

                if is_locust == '1':
                    Plan.objects.filter(is_locust=1).update(is_locust=0)
                Plan.objects.filter(plan_id=plan_id).update(plan_name=plan_name, project=project,
                                                            environment=environment,
                                                            description=description, content=content,
                                                            is_locust=is_locust, update_time=datetime.now(),
                                                            update_user=username)
                log.info(
                    'edit plan   {}  success. plan info: {} // {} // {} // {}'.format(plan_name, project, environment,
                                                                                      description, content))
                return HttpResponseRedirect("/base/plan/?page={}".format(page))
        elif request.method == 'GET':
            plan_id = request.GET['plan_id']
            page = request.GET.get("page", "1")
            plan = Plan.objects.get(plan_id=plan_id)
            environments = Environment.objects.filter(project_id=plan.project_id).all().values()
            case_list = []
            for case_id in eval(plan.content):
                try:
                    case = Case.objects.get(case_id=case_id)
                    case_list.append(case)
                except Case.DoesNotExist as e:
                    log.error('计划 {} 中的 用例 {} 已被删除！！！'.format(plan.plan_name, case_id))
                    plans = Plan.objects.all().order_by('-plan_id')
                    page = request.GET.get('page')
                    contacts = paginator(plans, page)
                    info = {"contacts": contacts, "model_list": model_list,
                            'error': '计划 {} 中的 用例 {} 已被删除！！！'.format(plan.plan_name, case_id)}
                    return render(request, "base/plan/index.html", info)
            info = {"prj_list": prj_list, 'plan': plan, 'case_list': case_list, 'environments': environments,
                    "model_list": model_list, "page": page}
            return render(request, "base/plan/update.html", info)


def plan_delete(request):
    """
    删除测试计划
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            plan_id = request.GET['plan_id']
            page = request.GET.get("page", "1")
            Plan.objects.filter(plan_id=plan_id).delete()
            log.info('用户 {} 删除计划 {} 成功.'.format(user_id, plan_id))
            return HttpResponseRedirect("base/plan/?page={}".format(page))


def plan_run(request):
    """
    运行测试计划
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        return JsonResponse({'error': ErrorCode.user_not_logged_in_error})
    else:
        if request.method == 'POST':
            global totalTime, start_time, now_time
            start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            now_time = int(time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S')))
            plan_id = request.POST.get('plan_id', '')
            run_mode = request.POST.get('run_mode', '')
            plan = Plan.objects.get(plan_id=plan_id)
            env_id = request.POST.get('env_id', '')
            case_id_list = eval(plan.content)
            username = request.session.get('user', '')
            if run_mode == '1':
                test_httprunner.delay(env_id, case_id_list, plan=plan, username=username)
                return HttpResponse('测试计划执行中，稍后可在【运行报告】处查看！')
            elif run_mode == '0':
                test_plan.delay(env_id, case_id_list, plan=plan, username=username)
                return HttpResponse("测试计划执行中，稍后可在【运行报告】处查看！")


# 测试计划列表
@method_decorator(login_required, name='dispatch')
class TaskIndex(ListView):
    model = PeriodicTask
    template_name = 'system/task/task_index.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def dispatch(self, *args, **kwargs):
        return super(TaskIndex, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        task_list = PeriodicTask.objects.all().order_by('-id')
        return task_list

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        user_id = self.request.session.get('user_id', '')
        model_list = limits_of_authority(user_id)
        context.update({"model_list": model_list, "page": self.page})
        context.update(data)
        return context


def task_run(request):
    """
    定时任务
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/task_index/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            task_id = request.POST.get('id', '')
            if task_id:
                task = PeriodicTask.objects.get(id=task_id)
                if 'run_plan' in task.task:
                    run_plan.delay(task.args, data=task.kwargs)
                    return HttpResponse('定时任务执行中，稍后在【运行报告】处查看即可,默认以 任务名称 + 时间戳 命名.【点击确定立即查看】')
                elif 'delete_logs' in task.task:
                    delete_logs.delay()
                    return HttpResponse('用例执行中，稍后可在日志中查看执行记录.')
                elif 'stop_locust' in task.task:
                    stop_locust.delay()
                    return HttpResponse('用例执行中，稍后可在日志中查看执行记录.')
                else:
                    return HttpResponse('未定义该定时任务.{}--{}'.format(task_id, task.task))
            else:
                return HttpResponse('未定义该定时任务.{}'.format(task_id))


def task_logs(request):
    """
    定时任务运行日志
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/case/'
        return render(request, 'user/login_action.html')
    else:
        model_list = limits_of_authority(user_id)
        data_list = []
        if platform.system() != 'Windows':
            task_log_path = '/www/wwwlogs/celery_worker.log'
            if os.path.exists(task_log_path):
                with open(task_log_path, 'rb') as f:
                    off = -1024 * 1024
                    if f.tell() < -off:
                        data = f.readlines()
                    else:
                        f.seek(off, 2)
                        data = f.readlines()
                    for line in data:
                        data_list.append(line.decode())
                    info = {'data': data_list, 'make': True, 'log_file': task_log_path, "model_list": model_list}
                    return render(request, 'system/task/log.html', info)
            else:
                return render(request, 'system/task/log.html', {'unicode': True, "model_list": model_list})
        else:
            return render(request, 'system/task/log.html', {'unicode': True, "model_list": model_list})


# 增加定时任务
def task_add(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == "GET":
            interval_list = IntervalSchedule.objects.all()
            crontab_list = CrontabSchedule.objects.all()
            model_list = limits_of_authority(user_id)
            info = {"interval_list": interval_list, "crontab_list": crontab_list, "model_list": model_list}
            return render(request, 'system/task/add.html', info)
        elif request.method == "POST":
            task_name = request.POST.get("task_name", "")
            plan_id = request.POST.get("plan_id", "")
            status = request.POST.get("status", "")
            crontab_time = request.POST.get("crontab_time", "")
            task = "base.tasks.run_plan"
            plan_id_list = plan_id.split(",")
            kwargs = {"task_name": task_name, "task_id": ""}
            periodic = PeriodicTask.objects.filter(name=task_name)
            if periodic:
                return JsonResponse("任务名称已存在！", safe=False)
            if crontab_time == "1":
                task_time = request.POST.get("task_time", "")
                interval = ""
                id_every = request.POST.get("id_every", 0)
                id_period = request.POST.get("id_period", "")
                if task_time == "1":
                    interval = IntervalSchedule.objects.filter(every=1).filter(period="days")
                    if not interval:
                        interval = IntervalSchedule.objects.create(every=1, period="days")
                    else:
                        interval = interval[0]
                elif task_time == "2":
                    interval = IntervalSchedule.objects.filter(every=7).filter(period="days")
                    if not interval:
                        interval = IntervalSchedule.objects.create(every=7, period="days")
                    else:
                        interval = interval[0]
                elif task_time == "3":
                    interval = IntervalSchedule.objects.filter(every=int(id_every)).filter(period=id_period)
                    if not interval:
                        interval = IntervalSchedule.objects.create(every=int(id_every), period=id_period)
                    else:
                        interval = interval[0]
                elif task_time == "4":
                    interval = request.POST.get("interval", 0)
                    interval = IntervalSchedule.objects.filter(id=int(interval))
                    if not interval:
                        return JsonResponse("选择时间间隔不存在！", safe=False)
                    if id_every.strip() != "" and id_period.strip() != "":
                        interval.update(every=int(id_every), period=id_period)
                    interval = interval[0]
                periodic = PeriodicTask.objects.create(name=task_name, task=task, enabled=int(status),
                                                       date_changed=datetime.now(),
                                                       interval=interval, args=json.dumps(plan_id_list))
                kwargs["task_id"] = periodic.id
                PeriodicTask.objects.filter(id=periodic.id).update(kwargs=json.dumps(kwargs))
            if crontab_time == "2":
                crontab_div_time = request.POST.get("crontab_div_time", "")
                crontab = ""
                make = False
                crontab_dict = eval(request.POST.get("crontab", ""))
                if crontab_div_time == "1":
                    crontab = CrontabSchedule.objects.filter(minute=crontab_dict["id_minute"]).filter(
                        hour=crontab_dict["id_hour"]).filter(day_of_week=crontab_dict["id_day_of_week"]).filter(
                        day_of_month=crontab_dict["id_day_of_month"]).filter(
                        month_of_year=crontab_dict["id_month_of_year"])
                    if not crontab:
                        crontab = CrontabSchedule.objects.create(minute=crontab_dict["id_minute"],
                                                                 hour=crontab_dict["id_hour"],
                                                                 day_of_week=crontab_dict["id_day_of_week"],
                                                                 day_of_month=crontab_dict["id_day_of_month"],
                                                                 month_of_year=crontab_dict["id_month_of_year"])
                elif crontab_div_time == "2":
                    crontab_ = request.POST.get("crontab_", "")
                    crontab = CrontabSchedule.objects.filter(id=int(crontab_))
                    if not crontab:
                        return JsonResponse("选择Crontab时间不存在！", safe=False)
                    for key, value in crontab_dict.items():
                        if value.strip() == "":
                            make = True
                    if not make:
                        crontab.update(minute=crontab_dict["id_minute"], hour=crontab_dict["id_hour"],
                                       day_of_week=crontab_dict["id_day_of_week"],
                                       day_of_month=crontab_dict["id_day_of_month"],
                                       month_of_year=crontab_dict["id_month_of_year"])
                    crontab = crontab[0]
                periodic = PeriodicTask.objects.create(name=task_name, task=task, enabled=int(status),
                                                       date_changed=datetime.now(), args=json.dumps(plan_id_list),
                                                       crontab=crontab)
                kwargs["task_id"] = periodic.id
                PeriodicTask.objects.filter(id=periodic.id).update(kwargs=json.dumps(kwargs))
            return JsonResponse("ok", safe=False)


def task_update(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == "GET":
            task_id = request.GET.get("task_id", "1")
            page = request.GET.get("page", "1")
            periodic = PeriodicTask.objects.get(id=task_id)
            interval_list = IntervalSchedule.objects.all()
            model_list = limits_of_authority(user_id)
            if periodic.interval_id:
                interval = IntervalSchedule.objects.get(id=periodic.interval_id)
            else:
                interval = ""
            if periodic.crontab_id:
                crontab = CrontabSchedule.objects.get(id=periodic.crontab_id)
            else:
                crontab = ""
            crontab_list = CrontabSchedule.objects.all()
            plan_id_list = eval(periodic.args)
            plan_list = []
            for plan_id in plan_id_list:
                try:
                    plan = Plan.objects.get(plan_id=plan_id)
                except Plan.DoesNotExist:
                    info = {"error": "任务中的计划 {} 已删除！".format(plan_id), "model_list": model_list, "page": page}
                    return render(request, "system/task/task_index.html", info)
                plan_list.append(plan)
            info = {"interval_list": interval_list, "periodic": periodic, "plan_list": plan_list, "interval": interval,
                    "crontab_list": crontab_list, "crontab": crontab, "model_list": model_list, "page": page}
            return render(request, 'system/task/update.html', info)
        elif request.method == "POST":
            task_name = request.POST.get("task_name", "")
            task_id = request.POST.get("task_id", "")
            kwargs = {"task_name": task_name, "task_id": task_id}
            plan_id = request.POST.get("plan_id", "")
            status = request.POST.get("status", "")
            crontab_time = request.POST.get("crontab_time", "")
            plan_id_list = plan_id.split(",")
            now_time = datetime.now()
            periodic = PeriodicTask.objects.filter(name=task_name).exclude(id=task_id)
            if not task_name:
                return JsonResponse("任务名称不能为空！", safe=False)
            if periodic:
                return JsonResponse("任务名称已存在！", safe=False)
            periodic = PeriodicTask.objects.get(id=task_id)
            if "run_plan" not in periodic.task:
                return JsonResponse("非选择测试计划的定时任务，无法保存！", safe=False)
            if crontab_time == "1":
                task_time = request.POST.get("task_time", "")
                id_every = request.POST.get("id_every", "")
                id_period = request.POST.get("id_period", "")
                interval = ""
                if task_time == "1":
                    interval = IntervalSchedule.objects.filter(every=1).filter(period="days")
                    if not interval:
                        interval = IntervalSchedule.objects.create(every=1, period="days")
                    else:
                        interval = interval[0]
                elif task_time == "2":
                    interval = IntervalSchedule.objects.filter(every=7).filter(period="days")
                    if not interval:
                        interval = IntervalSchedule.objects.create(every=7, period="days")
                    else:
                        interval = interval[0]
                elif task_time == "3":
                    interval = IntervalSchedule.objects.filter(every=int(id_every)).filter(period=id_period)
                    if not interval:
                        interval = IntervalSchedule.objects.create(every=int(id_every), period=id_period)
                    else:
                        interval = interval[0]
                elif task_time == "4":
                    interval = request.POST.get("interval", "")
                    interval = IntervalSchedule.objects.filter(id=int(interval))
                    if not interval:
                        return JsonResponse("选择时间间隔不存在！", safe=False)
                    if id_every.strip() != "" and id_period.strip() != "":
                        interval.update(every=int(id_every), period=id_period)
                    interval = interval[0]
                PeriodicTask.objects.filter(id=task_id).update(name=task_name, enabled=int(status),
                                                               date_changed=now_time, crontab="",
                                                               interval=interval, args=json.dumps(plan_id_list),
                                                               kwargs=json.dumps(kwargs))
            if crontab_time == "2":
                crontab_div_time = request.POST.get("crontab_div_time", "")
                crontab = ""
                make = False
                crontab_dict = eval(request.POST.get("crontab", ""))
                if crontab_div_time == "1":
                    crontab = CrontabSchedule.objects.filter(minute=crontab_dict["id_minute"]).filter(
                        hour=crontab_dict["id_hour"]).filter(day_of_week=crontab_dict["id_day_of_week"]).filter(
                        day_of_month=crontab_dict["id_day_of_month"]).filter(
                        month_of_year=crontab_dict["id_month_of_year"])
                    if not crontab:
                        crontab = CrontabSchedule.objects.create(minute=crontab_dict["id_minute"],
                                                                 hour=crontab_dict["id_hour"],
                                                                 day_of_week=crontab_dict["id_day_of_week"],
                                                                 day_of_month=crontab_dict["id_day_of_month"],
                                                                 month_of_year=crontab_dict["id_month_of_year"])
                    else:
                        crontab = crontab[0]
                elif crontab_div_time == "2":
                    crontab_ = request.POST.get("crontab_", "")
                    crontab = CrontabSchedule.objects.filter(id=int(crontab_))
                    if not crontab:
                        return JsonResponse("选择Crontab时间不存在！", safe=False)
                    for key, value in crontab_dict.items():
                        if value.strip() == "":
                            make = True
                    if not make:
                        crontab.update(minute=crontab_dict["id_minute"], hour=crontab_dict["id_hour"],
                                       day_of_week=crontab_dict["id_day_of_week"],
                                       day_of_month=crontab_dict["id_day_of_month"],
                                       month_of_year=crontab_dict["id_month_of_year"])
                    crontab = crontab[0]
                PeriodicTask.objects.filter(id=task_id).update(name=task_name, enabled=int(status),
                                                               date_changed=now_time,
                                                               args=json.dumps(plan_id_list), crontab=crontab,
                                                               interval="", kwargs=json.dumps(kwargs))
            PeriodicTasks.objects.filter(ident=1).update(last_update=now_time)
            log.info("用户 {} 更新定时任务 {} 成功！".format(user_id, task_id))
            return JsonResponse("ok", safe=False)


def task_delete(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/task_index/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            # task_id = request.build_absolute_uri().split("/")[-1]
            task_id = request.GET.get("task_id", "")
            page = request.GET.get("page", "1")
            PeriodicTask.objects.filter(id=task_id).delete()
            log.info("用户 {} 删除定时任务 {} 成功！".format(user_id, task_id))
            return HttpResponseRedirect("/base/task/?page={}".format(page))


# 报告列表
@method_decorator(login_required, name='dispatch')
class ReportPage(ListView):
    model = Report
    template_name = 'base/report_page/report_page.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def dispatch(self, *args, **kwargs):
        return super(ReportPage, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        self.plan_id = self.request.GET.dict().get('plan_id', '')
        if self.plan_id:
            report_list = Report.objects.filter(plan_id=self.plan_id).order_by('-report_id')
            return report_list
        else:
            report_list = Report.objects.all().order_by('-report_id')
            return report_list

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        context.update({'plan_id': self.plan_id})
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        context.update(data)
        user_id = self.request.session.get('user_id', '')
        model_list = limits_of_authority(user_id)
        context.update({"model_list": model_list, "page": self.page})
        return context


def report_logs(request):
    """
    显示日志信息
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/report_page/'
        return render(request, 'user/login_action.html')
    else:
        report_id = request.GET.get('report_id')
        model_list = limits_of_authority(user_id)
        try:
            report = Report.objects.get(report_id=report_id)
        except Report.DoesNotExist:
            return render(request, "base/report_page/log.html", {"model_list": model_list})
        else:
            report_content = eval(report.content.replace('Markup', ''))
            for case in report_content:
                global class_name
                class_name = case['class_name']
            info = {"report": report, 'plan_id': report.plan_id, "report_content": report_content,
                    'class_name': class_name, "model_list": model_list}
            return render(request, "base/report_page/log.html", info)


def report_index(request):
    """
    展示报告
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/report_index/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            report_id = request.GET.get('report_id', '')
            page = request.GET.get('page', '')
            if not report_id:
                return render(request, "report.html")
            try:
                report = Report.objects.get(report_id=report_id)
            except Report.DoesNotExist:
                return render(request, 'report.html')
            plan_id = report.plan_id
            make = report.make
            case_num = report.case_num
            pass_num = report.pass_num
            fail_num = report.fail_num
            error_num = report.error_num
            skip_num = report.skip_num
            report_content = eval(report.content.replace('Markup', ''))
            for case in report_content:
                global class_name
                class_name = case['class_name']
            info = {"report": report, 'plan_id': plan_id, 'case_num': case_num, "error_num": error_num,
                    'pass_num': pass_num, 'fail_num': fail_num, "report_content": report_content,
                    'img_name': str(now_time) + 'pie.png', 'class_name': class_name, "skip_num": skip_num, "page": page}
            if make:
                return render(request, "report_httprunner.html", info)
            else:
                return render(request, "report.html", info)


def report_search(request):
    """
    报告搜索
    :param request:
    :return:
    """
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
            report_content = eval(report.content.replace('Markup', ''))
            if result not in ['pass', 'fail', 'error', "skipped"]:
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


def report_delete(request):
    """
    删除报告
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/report_page/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            report_id = request.GET['report_id']
            page = request.GET.get("page", "1")
            Report.objects.filter(report_id=report_id).delete()
            log.info('用户 {} 删除报告 {} 成功.'.format(user_id, report_id))
            return HttpResponseRedirect("base/report_page/?page={}".format(page))


def file_download(request):
    """
    下载HttpRunner报告
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/report_page/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            report_id = request.GET.get('report_id', '')
            model_list = limits_of_authority(user_id)
            local_path = ""
            name = ""
            make = False
            if report_id:
                report = Report.objects.get(report_id=report_id)
                name = report.report_name[-19:]
                report_path = report.report_path
                if report_path:
                    if "[" in report_path:
                        file_name = eval(report_path)
                    else:
                        file_name = report_path
                else:
                    report_path = os.path.join(os.getcwd(), 'reports')  # 拼接删除目录完整路径
                    file_name = os.path.join(report_path, name + '.html')
            else:
                file_name = request.GET.get("log_file", "")

            def convert_zip(zip_path):
                '''
                # zip_path 要压缩文件的路径
                # save_path 文件压缩后保存的路径
                '''

                nonlocal local_path
                report_dir = settings.MEDIA_ROOT
                local_path = os.path.join(report_dir, "{}.zip".format(name))
                zip = zipfile.ZipFile(local_path, "w", zipfile.ZIP_DEFLATED)  # zipfile.ZIP_DEFLATED
                for file in zip_path:
                    zip.write(file)
                zip.close()

            if isinstance(file_name, list):
                try:
                    convert_zip(file_name)
                except FileNotFoundError:
                    log.info('文件：{} 中有文件不存在！'.format(file_name))
                    return render(request, "base/report_page/report_page.html",
                                  {'error': '文件：{} 中有文件不存在！'.format(file_name), "model_list": model_list})
                file_name = local_path
                make = True
            if not os.path.exists(file_name):
                log.info('文件：{} 无法下载！'.format(file_name))
                return render(request, "base/report_page/report_page.html",
                              {'error': '文件：{} 无法下载！'.format(file_name), "model_list": model_list})
            if make:
                if settings.DEBUG:
                    url = "http://localhost:8000/media/{}.zip".format(name)
                else:
                    url = "http://www.easytest.xyz/media/{}.zip".format(name)
                log.info('用户 {} 下载测试报告或日志文件：{} .'.format(user_id, url))
                return render(request, "base/report_page/report_page.html",
                              {'url': url, "model_list": model_list})

            def file_iterator(file_name, chunk_size=512):
                with open(file_name, encoding='utf-8') as f:
                    while True:
                        c = f.read(chunk_size)
                        if c:
                            yield c
                        else:
                            break

            response = StreamingHttpResponse(file_iterator(file_name))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_name)
            log.info('用户 {} 下载测试报告或日志文件：{} .'.format(user_id, file_name))
            return response


def performance_index(request):
    """
    locust页面
    :param request:
    :return:
    """
    if request.method == 'GET':
        user_id = request.session.get('user_id', '')
        if get_user(user_id):
            try:
                debug = DebugTalk.objects.get(belong_project_id=None)
                status = debug.status
            except DebugTalk.DoesNotExist:
                status = 0
            model_list = limits_of_authority(user_id)
            info = {"debug": settings.DEBUG, "status": status, "model_list": model_list}
            return render(request, 'base/performance/performance.html', info)
        else:
            request.session['login_from'] = '/base/performance/'
            return render(request, 'user/login_action.html')


class StartLocust(threading.Thread):
    def __init__(self, make, slave, path, status):
        threading.Thread.__init__(self)
        self.make = make
        self.slave = slave
        self.status = status
        self.path = path

    def run(self):
        log.info(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " {} ==== StartLocust ===={}==={}== {}"
            .format(self.getName(), self.make, self.slave, self.status))
        if self.make == 'master':
            if self.status == "True":
                copy_debugtalk()
                p = os.popen('{}'.format(self.slave))
            else:
                pattern = '/' if platform.system() != 'Windows' else '\\'
                path_list = self.path.split("performance" + pattern)
                execute_path = os.path.join(path_list[0], "performance")
                locust_path = path_list[1]
                os.chdir(execute_path)
                if str(self.slave).isdigit():
                    p = os.popen('locusts -f {} --processes {}'.format(locust_path, int(self.slave)))
                else:
                    p = os.popen('locusts -f {} --processes'.format(locust_path))
                os.chdir(settings.BASE_DIR)
            log.info("---------p-----------{}".format(p))
        elif self.make == 'stop':
            if platform.system() == 'Windows':
                find_port = 'netstat -aon | findstr "8089"'
                result = os.popen(find_port)
                text = result.read()
                log.info("返回的 8089 端口相关的信息：{}".format(text))
                listening_patt = re.compile("LISTENING       (\d+)")
                established_patt = re.compile("ESTABLISHED     (\d+)")
                listening = listening_patt.findall(text)[0]
                established_list = established_patt.findall(text)
                established_list.append(listening)
                established_list = list(set(established_list))
                # for pid in established_list:
                if 1 <= int(listening) <= 65535 and listening != "8089":
                    # 占用端口的pid
                    find_kill = 'taskkill -f -pid %s' % listening
                    result = os.popen(find_kill)
                    log.info("--stop--->>> {}".format(result.read()))
            else:
                p = os.system("/home/lixiaofeng/./stop_locust.sh")
                log.info("--stop---success-{}=====!".format(p))
            if self.status == "False":
                delete_performance(os.path.join(settings.BASE_DIR, "performance"))


def start_locust(request):
    if request.method == 'GET':
        user_id = request.session.get('user_id', '')
        if get_user(user_id):
            make = request.GET.get('make')
            slave = request.GET.get('slave')
            status = request.GET.get('status')
            testsuites_json_path = ""
            if status == "False":
                try:
                    plan = Plan.objects.get(is_locust=1)
                except Plan.DoesNotExist:
                    return HttpResponse("no")
                env_id = plan.environment_id
                case_id_list = eval(plan.content)
                execute = Test_execute(env_id, case_id_list, run_mode="1", plan=plan, locust=True)
                testsuites_json_path = execute.test_case
            locust = StartLocust(make, slave, testsuites_json_path, status)
            locust.start()
            return HttpResponse('ok')
        else:
            request.session['login_from'] = '/base/performance/'
            return render(request, 'user/login_action.html')


def performance_report(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/performance_report/'
        return render(request, 'user/login_action.html')
    else:
        model_list = limits_of_authority(user_id)
        if request.method == 'GET':
            try:
                res = requests.get('http://localhost:8089/stats/requests')
                res = res.json()
                info = {'info': res, "model_list": model_list}
                return render(request, 'base/performance/locust_report.html', info)
            except requests.exceptions.ConnectionError:
                locust_report = LocustReport.objects.all().order_by('-id')[:1]
                if locust_report:
                    for report in locust_report:
                        stats_list = eval(report.stats)
                        slave_list = eval(report.slaves)
                        return render(request, 'base/performance/locust_report.html',
                                      {'locust_report': locust_report, 'stats_list': stats_list,
                                       'slave_list': slave_list, "model_list": model_list})
                else:
                    info = {'error': '请先执行locust性能测试！', "model_list": model_list}
                    return render(request, 'base/performance/locust_report.html', info)
        info = {'error': '额，数据丢失了呢！', "model_list": model_list}
        return render(request, 'base/performance/locust_report.html', info)


def performance_real(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/performance_report/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            model_list = limits_of_authority(user_id)
            try:
                res = requests.get('http://localhost:8089/stats/requests')
            except requests.exceptions.ConnectionError:
                info = {'error': '未运行locust，无法获取实时数据！', "model_list": model_list}
                return render(request, 'base/performance/locust_real.html', info)
            res = res.json()
            current_response_time_percentile_50 = res.get('current_response_time_percentile_50', '0.0')
            current_response_time_percentile_95 = res.get('current_response_time_percentile_95', '0.0')
            errors = res.get('errors', [])
            fail_ratio = res.get('fail_ratio', '0.0')
            slaves = res.get('slaves', [])
            state = res.get('state', '')
            stats = res.get('stats', [])
            total_rps = res.get('total_rps', '0.0')
            user_count = res.get('user_count', '1')
            username = User.objects.get(id=user_id).username
            locust_report = LocustReport(current_response_time_percentile_50=current_response_time_percentile_50,
                                         current_response_time_percentile_95=current_response_time_percentile_95,
                                         errors=errors, fail_ratio=fail_ratio, slaves=slaves, state=state, stats=stats,
                                         total_rps=total_rps, user_count=user_count, update_user=username)
            locust_report.save()
            info = {'info': res, "model_list": model_list}
            log.info('用户 {} ，查看性能测试实时数据 并 写入到数据库中.'.format(user_id))
            return render(request, 'base/performance/locust_real.html', info)


def performance_history(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/performance_report/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            locust_report = LocustReport.objects.all().order_by('-id')
            stats_list = []
            for report in locust_report:
                stats = report.stats
                stats_list.append(eval(stats))
            model_list = limits_of_authority(user_id)
            info = {'info': stats_list, "model_list": model_list}
            log.info('用户 {} ，正在查看性能测试历史数据.'.format(user_id))
            return render(request, 'base/performance/locust_history.html', info)


def performance_delete(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/performance_report/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'GET':
            LocustReport.objects.all().delete()
            log.info('用户 {} ，清空性能测试历史数据完成！'.format(user_id))
            return render(request, 'base/performance/locust_history.html')


def performance_status(request):
    try:
        requests.get('http://localhost:8089/stats/requests')
        return HttpResponse("locust运行中，无法切换！")
    except requests.exceptions.ConnectionError:
        if request.method == "POST":
            status = request.POST.get("off", 0)
            debug = DebugTalk.objects.filter(belong_project_id=None)
            if debug:
                debug.update(status=status)
            else:
                debug.create(create_time=datetime.now(), update_time=datetime.now(), debugtalk="",
                             belong_project_id=None, status=1)
            if status == "1":
                info = "切换到自定义脚本模式成功！"
            elif status == "0":
                info = "切换到HttpRunner模式成功！"
            return HttpResponse(info)


# 用户列表
@method_decorator(login_required, name='dispatch')
class UserIndex(ListView):
    model = User
    template_name = 'system/user/user_index.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def dispatch(self, *args, **kwargs):
        return super(UserIndex, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        user_list = User.objects.all().order_by('-id')
        return user_list

    def get_context_data(self, **kwargs):
        self.page = self.request.GET.dict().get('page', '1')
        context = super().get_context_data(**kwargs)
        paginator = context.get('paginator')
        page = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        data = pagination_data(paginator, page, is_paginated)
        context.update(data)
        user_id = self.request.session.get('user_id', '')
        model_list = limits_of_authority(user_id)
        context.update({"model_list": model_list, "page": self.page})
        return context


def user_power(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/user/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == "GET":
            # patt = re.compile("\/(\d+)\/")
            # id = patt.findall(request.get_full_path())[0]
            id = request.GET.get("user_id")
            page = request.GET.get("page", "1")
            model_nav = limits_of_authority(user_id)
            model_list = []
            try:
                power_list = UserPower.objects.get(user_id=id).power
                model = ModularTable.objects.filter(id__in=json.loads(power_list))
                exclude = ModularTable.objects.all().exclude(id__in=json.loads(power_list))
                for foo in model:
                    model_list.append(
                        {"id": foo.id, "model_name": foo.model_name, "url": foo.url, "icon": foo.Icon, "make": True})
                for foo in exclude:
                    model_list.append(
                        {"id": foo.id, "model_name": foo.model_name, "url": foo.url, "icon": foo.Icon, "make": False})
            except UserPower.DoesNotExist:
                model = ModularTable.objects.all()
                for foo in model:
                    model_list.append(
                        {"id": foo.id, "model_name": foo.model_name, "url": foo.url, "icon": foo.Icon, "make": False})
            info = {"model": model_list, "id": id, "model_nav": model_nav, "page": page}
            superuser = is_superuser(user_id, make=False)
            if not superuser:
                if user_id != int(id):
                    info.update({"error": "非超级管理员只能修改自己的权限！"})
                    return render(request, 'system/user/power.html', info)
            return render(request, 'system/user/power.html', info)
        if request.method == "POST":
            body = request.body.decode("utf-8")
            patt = re.compile("power\d+=(\d+)")
            user_patt = re.compile("user_id=(\d+)")
            page_patt = re.compile("page=(\d+)")
            power = patt.findall(body)
            id = user_patt.findall(body)[0]
            page = page_patt.findall(body)[0]
            try:
                user = UserPower.objects.get(user_id=id)
                user.power = json.dumps(power)
                user.save()
            except UserPower.DoesNotExist:
                UserPower.objects.create(user_id=id, power=json.dumps(power))
            return HttpResponseRedirect("/base/user/?page={}".format(page))


def about_index(request):
    """
    关于我们
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if get_user(user_id):
        model_list = limits_of_authority(user_id)
        return render(request, 'system/about/about_us.html', {"model_list": model_list})

    else:
        request.session['login_from'] = '/base/about/'
        return render(request, 'user/login_action.html')


def document(request):
    """
    关于我们
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/document_download/'
        return render(request, 'user/login_action.html')
    else:
        document_dir = '/var/lib/jenkins/workspace/EasyTest/media/'
        document_list = os.listdir(document_dir)
        file_list = []
        num = 0
        for doc in document_list:
            document_path = os.path.join(document_dir, doc)
            if os.path.isdir(document_path):
                path = os.path.join(document_dir, doc)
                media_path = os.path.join('http://www.easytest.xyz/media/', doc)
                path_list = os.listdir(path)
                path_list.sort()
                num += 1
                file_num = 0
                document_dict = {"id": num, "doc_name": doc, "file_dict": []}
                for file in path_list:
                    file_path = os.path.join(path, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        file_num += 1
                        file_dict = {"file_id": file_num, "file_name": file,
                                     "file_path": os.path.join(media_path, file),
                                     "file_size": str(size / 1024)[:4]}
                        document_dict["file_dict"].append(file_dict)
                file_list.append(document_dict)
                # log.info('-----------------------------{}'.format(file_list))
        return render(request, 'system/about/document_download.html', {"file_list": file_list})


def findata(request):
    """
    异步请求数据
    :param request:
    :return:
    """
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
            try:
                # 查询并将结果转换为json
                interface = Interface.objects.filter(if_id=if_id).values()
                return JsonResponse(list(interface), safe=False)
            except ValueError:
                return HttpResponse('no')
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
        if get_type == "get_all_plan":
            plan = Plan.objects.all().values()
            if not plan:
                return JsonResponse("no", safe=False)
            return JsonResponse(list(plan), safe=False)
        if get_type == "get_all_case_by_prj_id":
            prj_id = request.GET["prj_id"]
            try:
                # 查询并将结果转换为json
                case = Case.objects.filter(project_id=prj_id).values()
                return JsonResponse(list(case), safe=False)
            except ValueError:
                return HttpResponse('no')
        if get_type == "get_crontab_or_id":
            crontab_id = request.GET.get("crontab_id")
            try:
                crontab = CrontabSchedule.objects.filter(id=crontab_id).values()
                return JsonResponse(list(crontab), safe=False)
            except CrontabSchedule.DoesNotExist:
                return HttpResponse("no")
        if get_type == "get_interval_or_id":
            interval_id = request.GET.get("interval_id")
            try:
                interval = IntervalSchedule.objects.filter(id=interval_id).values()
                return JsonResponse(list(interval), safe=False)
            except CrontabSchedule.DoesNotExist:
                return HttpResponse("no")
        if get_type == 'get_log':
            log_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/logs'
            log_file_list = os.listdir(log_path)
            file_list = []
            data_list = []
            now = time.strftime('%Y-%m-%d')
            for file in log_file_list:
                if 'all' in file and now in file:
                    file_list.append(file)
            if not file_list:
                yesterday = datetime.today() + timedelta(-1)
                yesterday_format = yesterday.strftime('%Y-%m-%d')
                for file in log_file_list:
                    if 'all' in file and yesterday_format in file:
                        file_list.append(file)
            try:
                file_list.sort()
                log_file = os.path.join(log_path, file_list[0])
            except IndexError:
                for file in log_file_list:
                    if 'all' in file:
                        file_list.append(file)
                file_list.sort()
                log_file = os.path.join(log_path, file_list[-1])
            with open(log_file, 'r', encoding='utf-8') as f:
                off = -1024 * 1024
                if f.tell() < -off:
                    data = f.readlines()
                else:
                    f.seek(off, 2)
                    data = f.readlines()
            for i in data:
                data_list.append(i.replace('True', 'true').replace('False', 'false').replace('None', 'null'))
            log.info('get_log 查询日志文件名称 ===========================>>> {}'.format(log_file))
            return JsonResponse(data_list, safe=False)
        if get_type == 'get_task_log':
            data_list = []
            if platform.system() != 'Windows':
                task_log_path = '/www/wwwlogs/celery_worker.log'
                if os.path.exists(task_log_path):
                    with open(task_log_path, 'r', encoding='utf-8') as f:
                        off = -1024 * 1024
                        if f.tell() < -off:
                            data = f.readlines()
                        else:
                            f.seek(off, 2)
                            data = f.readlines()
                    for i in data:
                        data_list.append(i.replace('True', 'true').replace('False', 'false').replace('None', 'null'))
                    return JsonResponse(data_list, safe=False)
                else:
                    return JsonResponse(data_list, safe=False)
            else:
                return JsonResponse(data_list, safe=False)
    elif request.method == 'POST':
        get_type = request.POST.get("type", '')
        if get_type == 'analysis_request_header_json':
            request_header_json = request.POST.get('request_header_json', '')
            try:
                data = eval(
                    request_header_json.replace('false', 'False').replace('null', 'None').replace('true', 'True'))
                return JsonResponse(list(data), safe=False)
            except Exception as e:
                log.error('解析参数错误. {}'.format(e))
                return HttpResponse('no')


def report_results(request):
    """
    获取报告结果接口
    :param request:
    :return:
    """
    user_id = request.session.get('user_id', '')  # 从session中获取user_id
    if not get_user(user_id):
        return JsonResponse({"msg": "请先登录您的帐号！"})
    else:
        superuser = User.objects.get(id=user_id).is_superuser
        if not superuser:
            return JsonResponse({"msg": "您的帐号没有管理员权限，请跟测试人员了解详情！"})
        else:
            if request.method != "GET":
                return JsonResponse({"msg": "您的请求方式错误，该接口需要使用 GET 请求！"})
            else:
                report_id = request.GET.get("report_id", "")
                if report_id:
                    try:
                        report = Report.objects.get(report_id=report_id)
                    except Report.DoesNotExist:
                        return JsonResponse({"error": "查看的报告不存在，请跟测试人员核实！"})
                else:
                    report = Report.objects.all().order_by("-report_id").first()
                name = report.report_name
                case_num = report.case_num
                pass_num = int(report.pass_num)
                fail_num = int(report.fail_num)
                error_num = int(report.error_num)
                error_list = []
                if fail_num or error_num:
                    content = eval(report.content)
                    if isinstance(content, list):
                        for case in content:
                            for data in case.get("step_list", []):
                                if data.get("result", "") in ("fail", "error"):
                                    error_dict = {
                                        "接口名称": data.get("if_name", ""),
                                        "接口地址": data.get("url", ""),
                                        "自定义报错信息": data.get("error", ""),
                                        "检查点": data.get("msg", ""),
                                        "接口请求参数": data.get("body", ""),
                                        "接口请求头": data.get("header", ""),
                                        "接口返回信息": data.get("res_content", ""),
                                    }
                                    error_list.append(error_dict)

                info = {
                    "报告名称": name,
                    "用例数量": case_num,
                    "接口通过数量": pass_num,
                    "接口失败数量": fail_num,
                    "接口错误数量": error_num,
                    "接口通过率": str(format(pass_num / (error_num + fail_num + pass_num) * 100, ".2f")) + "%",
                    "异常接口信息": error_list,
                }
                return JsonResponse(info)


def debugtalk(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        return render(request, 'user/login_action.html')

    else:
        if request.method == 'GET':
            # patt = re.compile("\/(\d+)\/")
            # id = patt.findall(request.get_full_path())[0]
            id = request.GET.get("prj_id")
            page = request.GET.get("page")
            try:
                if not id:
                    debugtalk = DebugTalk.objects.values('id', 'debugtalk', "status", "page").get(
                        belong_project_id=None)
                else:
                    DebugTalk.objects.filter(belong_project_id=id).update(page=page)
                    debugtalk = DebugTalk.objects.values('id', 'debugtalk', "status", "page").get(belong_project_id=id)
                return render_to_response('debugtalk.html', debugtalk)
            except DebugTalk.DoesNotExist:
                return render(request, "debugtalk.html", {"id": id, "page": page})
        elif request.method == "POST":
            id = request.POST.get('id')
            page = request.POST.get('page', "1")
            debugtalk = request.POST.get('debugtalk')
            status = request.POST.get('status', "False")
            code = debugtalk.replace('new_line', '\r\n')
            if status == "True":
                try:
                    obj = DebugTalk.objects.get(id=id)
                    obj.debugtalk = code
                except DebugTalk.DoesNotExist:
                    obj = DebugTalk(create_time=datetime.now(), update_time=datetime.now(), debugtalk=code,
                                    belong_project_id=None, status=1)
                obj.save()
                return HttpResponseRedirect("/base/performance/")
            else:
                try:
                    obj = DebugTalk.objects.get(id=id)
                    obj.debugtalk = code
                    obj.page = page
                except DebugTalk.DoesNotExist:
                    obj = DebugTalk(create_time=datetime.now(), update_time=datetime.now(), debugtalk=code,
                                    belong_project_id=id, page=page)
                obj.save()
                return HttpResponseRedirect("/base/project/?page={}".format(page))
