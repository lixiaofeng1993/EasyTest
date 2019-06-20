from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import auth  # django认证系统
from djcelery.models import PeriodicTask, CrontabSchedule
from django.contrib.auth.models import User
from django.db.models import Count
from base.models import Project, Sign, Environment, Interface, Case, Plan, Report
import logging, os
from django.http import StreamingHttpResponse
from lib.public import gr_code
from lib.execute import get_user

log = logging.getLogger('log')  # 初始化log
num_list = []


# 首页
# @login_required
# @page_cache(5)
def index(request):
    user_id = request.session.get('user_id', '')  # 从session中获取user_id
    if get_user(user_id):
        if request.method == 'POST':
            url = request.POST.get('url', '')
            if url:
                qr_code_name = gr_code(url)
                log.info('生成二维码 {}-->{}'.format(qr_code_name, url))
                return JsonResponse(str(qr_code_name), safe=False)
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
            username = request.session.get('user', '')
            num_list = [project_num, env_num, interface_num, case_num, plan_num, sign_num, report_num,
                        periodic_num + crontabSchedule_num]
            return render(request, "index.html",
                          {'username': username, 'num_list': num_list, 'project_num': project_num,
                           'env_num': env_num, 'interface_num': interface_num, 'case_num': case_num,
                           'plan_num': plan_num,
                           'sign_num': sign_num, 'report_num': report_num,
                           'task_num': periodic_num + crontabSchedule_num})
    else:
        request.session['login_from'] = '/index/'
        return render(request, 'user/login_action.html')


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
            # prj_list = Project.objects.filter(user_id=user_.id)  # 按照user_id查询项目
            # project_list = []
            # for prj in prj_list:
            #     project_list.append(str(prj.prj_id))
            # request.session['project_list'] = project_list  # 保存项目id
            request.session.set_expiry(60)  # 关闭浏览器后，session失效
            return response
            # return render(request, 'base.html', {"user": username})
        else:
            # return render(request, 'sign/login.html', {'error': 'username or password error!'})
            log.error('用户名或密码错误... {} {}'.format(username, password))
            return render(request, 'user/login_action.html', {'error': 'username or password error!'})


@login_required
def img_download(request):
    # do something...
    user_id = request.session.get('user_id', '')  # 从session中获取user_id
    if get_user(user_id):
        if request.method == 'GET':
            name = request.GET.get('log_file', '')
            name_path = os.path.join('/home/ubuntu/EasyTest/media', name)

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
            log.info('下载的二维码：{}'.format(name_path))
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
