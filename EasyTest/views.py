from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
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
from lib.execute import get_user, get_total_values

log = logging.getLogger('log')  # 初始化log
num_list = []


# appid = 'wx506830910cbd77e9'
# appsecret = 'e0e5d5ed1d507103f73d6667eef00d7a' pages/index/detail/index?id=365&campId=12&index=1

# 首页
def index(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id', '')  # 从session中获取user_id
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
    else:
        project_num = Project.objects.aggregate(Count('prj_id'))['prj_id__count']
        env_num = Environment.objects.aggregate(Count('env_id'))['env_id__count']
        interface_num = Interface.objects.aggregate(Count('if_id'))['if_id__count']
        case_num = Case.objects.aggregate(Count('case_id'))['case_id__count']
        plan_num = Plan.objects.aggregate(Count('plan_id'))['plan_id__count']
        sign_num = Sign.objects.aggregate(Count('sign_id'))['sign_id__count']
        report_num = Report.objects.aggregate(Count('report_id'))['report_id__count']
        periodic_num = PeriodicTask.objects.aggregate(Count('id'))['id__count']
        crontabSchedule_num = CrontabSchedule.objects.aggregate(Count('id'))['id__count']

        total = get_total_values()

        info = {'project_num': project_num,
                'env_num': env_num, 'interface_num': interface_num, 'case_num': case_num,
                'plan_num': plan_num, 'total': total,
                'sign_num': sign_num, 'report_num': report_num,
                'task_num': periodic_num + crontabSchedule_num}

        return render(request, "index.html", info)


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
            except KeyError as e:
                request.session['login_from'] = '/index/'
            log.info('---------地址来源-------------> {}'.format(request.session['login_from']))
            response = redirect(request.session['login_from'])
            # response = HttpResponseRedirect('/index/')
            log.info('用户： {} 登录成功！'.format(username))
            request.session.set_expiry(None)  # 关闭浏览器后，session失效
            return response
        else:
            log.error('用户名或密码错误... {} {}'.format(username, password))
            return render(request, 'user/login_action.html', {'error': 'username or password error!'})


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
            log.info('用户 {} 下载的二维码：{}'.format(user_id, name_path))
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
