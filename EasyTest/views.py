from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib import auth  # django认证系统
from djcelery.models import PeriodicTask, CrontabSchedule
from django.contrib.auth.models import User
from django.db.models import Count
from django.conf import settings
# from django.shortcuts import render_to_response
from base.models import Project, Sign, Environment, Interface, Case, Plan, Report
import logging, os
from django.http import StreamingHttpResponse
from lib.public import gr_code, getACodeImage
from lib.execute import get_user, get_total_values, is_superuser
from lib.send_email import send_email
from lib.except_check import register_info_logic, change_info_logic
import sys, json, requests, re, datetime

log = logging.getLogger('log')  # 初始化log
num_list = []


# appid = 'wx506830910cbd77e9'
# appsecret = 'e0e5d5ed1d507103f73d6667eef00d7a' pages/index/detail/index?id=365&campId=12&index=1

# 首页
@login_required
def index(request):
    user_id = request.session.get('user_id', '')  # 从session中获取user_id
    if not user_id:
        return render(request, 'user/login_action.html')
    if request.method == 'POST':
        if get_user(user_id):
            url = request.POST.get('url', '')
            path = request.POST.get('path', '')
            appid = request.POST.get('appid', '')
            appsecret = request.POST.get('appsecret', '')
            if appid != '' and appsecret != '':
                if path == '':
                    path = '?from=1'
                url = {'path': path}
                qr_code_name = getACodeImage(appid, appsecret, url)
                if not qr_code_name:
                    log.info('用户 {} 生成小程序码 失败！appid、appsecret错误，未返回正确的token！')
                    return HttpResponse('2')
                else:
                    log.info('用户 {} 生成小程序码 {}-->{}'.format(user_id, qr_code_name, url))
                    return JsonResponse(str(qr_code_name), safe=False)
            elif url != '':
                qr_code_name = gr_code(url)
                log.info('用户 {} 生成二维码 {}-->{}'.format(user_id, qr_code_name, url))
                return JsonResponse(str(qr_code_name), safe=False)
            else:
                return HttpResponse('1')
        else:
            return HttpResponse('0')
    elif request.method == 'GET':
        plan_list = []
        prj_list = is_superuser(user_id, type='list')
        plan = Plan.objects.filter(project_id__in=prj_list)
        for plan_ in plan:
            plan_list.append(plan_.plan_id)
        superuser = User.objects.get(id=user_id).is_superuser
        if superuser:
            project_num = Project.objects.aggregate(Count('prj_id'))['prj_id__count']
        else:
            project_num = Project.objects.filter(user_id=user_id).aggregate(Count('prj_id'))['prj_id__count']
        env_num = Environment.objects.filter(project_id__in=prj_list).aggregate(Count('env_id'))['env_id__count']
        interface_num = Interface.objects.filter(project_id__in=prj_list).aggregate(Count('if_id'))['if_id__count']
        case_num = Case.objects.filter(project_id__in=prj_list).aggregate(Count('case_id'))['case_id__count']
        plan_num = Plan.objects.filter(project_id__in=prj_list).aggregate(Count('plan_id'))['plan_id__count']
        sign_num = Sign.objects.aggregate(Count('sign_id'))['sign_id__count']
        report_num = Report.objects.filter(plan_id__in=plan_list).aggregate(Count('report_id'))['report_id__count']
        periodic_num = PeriodicTask.objects.aggregate(Count('id'))['id__count']
        crontabSchedule_num = CrontabSchedule.objects.aggregate(Count('id'))['id__count']
        user_num = User.objects.aggregate(Count('id'))['id__count']

        total = get_total_values(user_id)

        info = {'project_num': project_num,
                'env_num': env_num, 'interface_num': interface_num, 'case_num': case_num,
                'plan_num': plan_num, 'total': total,
                'sign_num': sign_num, 'report_num': report_num,
                'task_num': periodic_num + crontabSchedule_num, 'user_num': user_num}

        return render(request, "index.html", info)


@login_required
def index_data(request):
    user_id = request.session.get('user_id', '')  # 从session中获取user_id
    if not user_id:
        return render(request, 'user/login_action.html')
    elif request.method == 'GET':
        off = request.GET.get('off', '')
        plan_list = []
        prj_list = is_superuser(user_id, type='list', off=off)
        plan = Plan.objects.filter(project_id__in=prj_list)
        for plan_ in plan:
            plan_list.append(plan_.plan_id)
        if off == '1':
            project_num = Project.objects.aggregate(Count('prj_id'))['prj_id__count']
        else:
            project_num = Project.objects.filter(user_id=user_id).aggregate(Count('prj_id'))['prj_id__count']
        env_num = Environment.objects.filter(project_id__in=prj_list).aggregate(Count('env_id'))['env_id__count']
        interface_num = Interface.objects.filter(project_id__in=prj_list).aggregate(Count('if_id'))['if_id__count']
        case_num = Case.objects.filter(project_id__in=prj_list).aggregate(Count('case_id'))['case_id__count']
        plan_num = Plan.objects.filter(project_id__in=prj_list).aggregate(Count('plan_id'))['plan_id__count']
        sign_num = Sign.objects.aggregate(Count('sign_id'))['sign_id__count']
        report_num = Report.objects.filter(plan_id__in=plan_list).aggregate(Count('report_id'))['report_id__count']
        periodic_num = PeriodicTask.objects.aggregate(Count('id'))['id__count']
        crontabSchedule_num = CrontabSchedule.objects.aggregate(Count('id'))['id__count']
        user_num = User.objects.aggregate(Count('id'))['id__count']

        info = {'project_num': project_num, 'env_num': env_num, 'interface_num': interface_num, 'case_num': case_num,
                'plan_num': plan_num, 'sign_num': sign_num, 'report_num': report_num,
                'task_num': periodic_num + crontabSchedule_num, 'user_num': user_num}

        return JsonResponse(info)


# 天气
def get_whether(request):
    if request.method == 'GET':
        city_code_dict = {
            '北京': '101010100', '上海': '101020100',
            '天津': '101030100', '重庆': '101040100',
        }
        postal_code = city_code_dict['北京']
        if postal_code.isdigit() == False:
            log.error("input is not number!")
            sys.exit()
        url = "http://www.weather.com.cn/data/cityinfo/" + postal_code + ".html"
        try:
            res = requests.get(url)
        except requests.RequestException as e:
            log.error('请求天气接口失败： {}'.format(e))
            return HttpResponse('0')
        content = res.content
        if isinstance(content, bytes):
            content = str(content, encoding='utf-8')
        result_dict = json.loads(content)  # 从网页爬取的json转化成字典
        now = str(datetime.datetime.now())[:10]
        item = result_dict.get('weatherinfo')  # 取字典的值用get方法
        item['now'] = now
        # log.info('获取北京天气信息==============> {} '.format(item))
        return JsonResponse(item)


# 登录
def login_action(request):
    if request.method == 'GET':
        # 把来源的url保存到session中
        request.session['login_from'] = request.META.get('HTTP_REFERER', '/')
        return render(request, 'user/login_action.html')
    else:
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            # response.set_cookie('user', username, 3600)  # 添加浏览器cookie，设置过期时间
            request.session['user'] = username  # 将session信息记录到浏览器
            user_ = User.objects.get(username=username)
            request.session['user_id'] = user_.id  # 将session信息记录到浏览器
            try:
                if request.session['login_from'] == '//':
                    request.session['login_from'] = '/index/'
                elif 'api' in request.session['login_from']:
                    request.session['login_from'] = '/index/'
            except KeyError as e:
                request.session['login_from'] = '/index/'
            log.info('---------地址来源-------------> {}'.format(request.session['login_from']))
            response = redirect(request.session['login_from'])
            log.info('用户： {} 登录成功！'.format(username))
            request.session.set_expiry(None)  # 关闭浏览器后，session失效
            return response
        else:
            log.error('用户名或密码错误... {} {}'.format(username, password))
            return render(request, 'user/login_action.html', {'error': 'username or password error!'})


# 修改密码
def change_password(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')

        msg = change_info_logic(new_password)
        if msg != 'ok':
            return JsonResponse({'msg': msg})
        else:
            user_id = request.session.get('user_id', '')
            if not user_id:
                return render(request, 'user/login_action.html')
            user = User.objects.get(id=user_id)
            user.set_password(new_password)
            user.save()
            return JsonResponse({'msg': 'success'})


# 注册
def register(request):
    if request.method == 'GET':
        return render(request, 'user/register.html')
    else:
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        pswd_again = request.POST.get('pswd-again', '')
        email = request.POST.get('email', '')
        msg = register_info_logic(username, password, pswd_again, email)
        if msg != 'ok':
            return render(request, 'user/register.html', {'error': msg})
        else:
            User.objects.create_user(username=username, password=password, email=email)
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                request.session['user'] = username  # 将session信息记录到浏览器
                user_ = User.objects.get(username=username)
                request.session['user_id'] = user_.id  # 将session信息记录到浏览器
                response = redirect('/index/')
                send_email('18701137212@163.com', '注册登录记录', report_id=username, register=True)
                log.info('用户： {} 注册并登录成功！'.format(username))
                request.session.set_expiry(None)  # 关闭浏览器后，session失效
                return response


# @login_required
def img_download(request):
    # do something...
    user_id = request.session.get('user_id', '')  # 从session中获取user_id
    if get_user(user_id):
        if request.method == 'GET':
            name = request.GET.get('log_file', '')
            name_path = os.path.join(settings.MEDIA_ROOT, name)

            def file_iterator(file_name, chunk_size=512):
                with open(file_name, 'rb') as f:
                    while True:
                        c = f.read(chunk_size)
                        if c:
                            yield c
                        else:
                            break

            response = StreamingHttpResponse(file_iterator(name_path))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(name_path)
            log.info('用户 {} 下载的二维码：{}'.format(user_id, 'http://39.105.136.231/media/{}'.format(name)))
            return response
    else:
        request.session['login_from'] = '/index/'
        return render(request, 'user/login_action.html')


# 退出
def logout(request):
    username = request.session.get('user', '')
    log.info('用户：{},退出登录！'.format(username))
    auth.logout(request)  # 退出登录
    response = HttpResponseRedirect('/login_action/')
    return response


# 400 
def bad_request(request, exception, template_name='error_page/400.html'):
    log.error('-------------------->400 error<--------------------')
    return render(request, template_name)


# 403
def permission_denied(request, exception, template_name='error_page/403.html'):
    log.error('-------------------->403 error<--------------------')
    return render(request, template_name)


# 404
def page_not_found(request, exception, template_name='error_page/404.html'):
    log.error('-------------------->404 error<--------------------')
    return render(request, template_name)


# 500
def server_error(exception, template_name='error_page/500.html'):
    log.error('-------------------->500 error<--------------------')
    return render(exception, template_name)
