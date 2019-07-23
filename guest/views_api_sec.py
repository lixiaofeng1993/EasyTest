import json
from django.contrib import auth as django_auth
import base64
import hashlib
from Crypto.Cipher import AES  # AES加密
from django.http import JsonResponse, HttpResponse
from guest.models import Event, Guest
from django.core.exceptions import ValidationError, ObjectDoesNotExist  # 验证错误
from django.db.utils import IntegrityError  # 完整性错误
from django.db.models import Q  # 与或非 查询
import time
import logging

log = logging.getLogger('log')


# 添加发布会接口-增加签名和时间戳
def sec_add_event(request):
    sign_result = user_sign_api(request)
    if sign_result == 'error':
        return JsonResponse({'status': 10011, 'message': 'request error'})
    elif sign_result == 'sign null':
        return JsonResponse({'status': 10012, 'message': 'user sign null'})
    elif sign_result == 'timeout':
        return JsonResponse({'status': 10013, 'message': 'user sign timeout'})
    elif sign_result == 'sign fail':
        return JsonResponse({'status': 10014, 'message': 'user sign fail'})

    eid = request.POST.get('eid', '')  # 发布会id
    name = request.POST.get('name', '')  # 发布会标题
    limit = request.POST.get('limit', '')  # 限制人数
    status = request.POST.get('status', '')  # 状态
    address = request.POST.get('address', '')  # 地址
    start_time = request.POST.get('start_time', '')  # 发布会时间

    if eid == '' or name == '' or limit == '' or status == '' or address == '' or start_time == '':
        log.info('sec_add_event，参数错误，不能为空.')
        return JsonResponse({'status': 10021, 'message': 'parameter error'})
    result = Event.objects.filter(id=eid)
    if result:
        log.info('sec_add_event，发布会id已经存在.')
        return JsonResponse({'status': 10022, 'message': 'event id already exists'})
    result = Event.objects.filter(name=name)
    if result:
        log.info('sec_add_event，发布会名称已经存在.')
        return JsonResponse({'status': 10023, 'message': 'event name already exists'})
    if status == '':
        status = 1
    try:
        Event.objects.create(id=eid, name=name, limit=limit, address=address, status=int(status), start_time=start_time)
    except ValidationError as e:
        error = 'start_time format error.It must be in YYYY-MM-DD HH:MM:SS format. error: {}'.format(e)
        log.info('sec_add_event，开始时间格式错误.')
        return JsonResponse({'status': 10024, 'message': error})
    log.info('sec_add_event，发布会添加成功！')
    return JsonResponse({'status': 200, 'message': 'add event success'})


# 查询发布会接口--增加用户认证
def sec_get_event_list(request):
    auth_result = user_auth(request)  # 认证函数
    if auth_result == 'null':
        return JsonResponse({'status': 10011, 'message': 'user auth null'})
    if auth_result == 'fail':
        return JsonResponse({'status': 10012, 'message': 'user auth fail'})

    eid = request.GET.get('eid', '')  # 发布会id
    name = request.GET.get('name', '')  # 发布会名称

    if eid == '' and name == '':
        log.info('sec_get_event_list，参数错误，不能为空.')
        return JsonResponse({'status': 10021, 'message': 'parameter error'})
    if eid != '':
        event = {}
        try:
            result = Event.objects.get(id=eid)
        except ObjectDoesNotExist:
            log.info('sec_get_event_list，查询结果为空.')
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})
        else:
            event['name'] = result.name
            event['limit'] = result.limit
            event['status'] = result.status
            event['address'] = result.address
            event['start_time'] = result.start_time
            log.info('sec_get_event_list，查询嘉宾成功！')
            return JsonResponse({'status': 200, 'message': 'success', 'data': event})

    if name != '':
        datas = []
        results = Event.objects.filter(name__contains=name)
        if results:
            for r in results:
                event = {}
                event['name'] = r.name
                event['limit'] = r.limit
                event['status'] = r.status
                event['address'] = r.address
                event['start_time'] = r.start_time
                datas.append(event)
                log.info('sec_get_event_list，查询发布会成功！')
            return JsonResponse({'status': 200, 'message': 'success', 'data': datas})
        else:
            log.info('sec_get_event_list，查询结果为空.')
            return JsonResponse({'status': 10022, 'message': 'query result is empty'})


# 嘉宾查询接口-AES算法
def sec_get_guest_list(request):
    dict_data = aes_encryption(request)
    if dict_data == 'error':
        return JsonResponse({'status': 10011, 'message': 'request error'})

    # 取出对应的发布会id和嘉宾手机号
    name = dict_data['name']

    if name == '':
        datas = []
        results = Guest.objects.all()
        if results:
            for r in results:
                guest = {}
                event = Event.objects.get(id=r.event_id)
                guest['realname'] = r.realname
                guest['phone'] = r.phone
                guest['email'] = r.email
                guest['sign'] = r.sign
                guest['event_name'] = event.name
                datas.append(guest)
            log.info('sec_get_guest_list，AES, 查询嘉宾成功！')
            return JsonResponse({'status': 200, 'message': 'success', 'data': datas})
    else:
        results = Guest.objects.filter(Q(phone__contains=name) | Q(realname__contains=name))  # guest 表中查询
        if results:
            datas = []
            for r in results:
                guest = {}
                event = Event.objects.get(id=r.event_id)
                guest['realname'] = r.realname
                guest['phone'] = r.phone
                guest['email'] = r.email
                guest['sign'] = r.sign
                guest['event_name'] = event.name
                datas.append(guest)
            log.info('sec_get_guest_list，AES, 查询嘉宾成功！')
            return JsonResponse({'status': 200, 'message': 'success', 'data': datas})
        else:
            id_results = Event.objects.filter(name__contains=name)  # event 表联查
            if id_results:
                datas = []
                for event_id in id_results:
                    results = Guest.objects.filter(event_id=event_id)
                    for r in results:
                        if r:
                            guest = {}
                            event = Event.objects.get(id=r.event_id)
                            guest['realname'] = r.realname
                            guest['phone'] = r.phone
                            guest['email'] = r.email
                            guest['sign'] = r.sign
                            guest['event_name'] = event.name
                            datas.append(guest)
                log.info('sec_get_guest_list，AES, 查询嘉宾成功！')
                return JsonResponse({'status': 200, 'message': 'success', 'data': datas})
            else:
                log.info('sec_get_guest_list，AES, 查询结果为空.')
                return JsonResponse({'status': 10022, 'message': 'query result is empty'})


# 用户认证-提取出用户数据，并判断其正确性
def user_auth(request):
    get_http_auth = request.META.get('HTTP_AUTHORIZATION',
                                     'b')  # request.META 一个dict，包含HTTP请求的header信息 HTTP_AUTHORIZATION 获取HTTP认证数据，为空，返回bytes对象 返回值例如: Basic YWRtaW46YW4xMjM0NTY=
    auth = get_http_auth.split()  # 拆分成list
    try:
        auth_parts = base64.b64decode(auth[1]).decode('utf-8').partition(
            ':')  # 取出加密串，通过base64解密 partition()方法以冒号为分隔符对字符串进行拆分 元组
    except IndexError:
        return 'null'
    username, password = auth_parts[0], auth_parts[2]
    user = django_auth.authenticate(username=username, password=password)
    if user is not None:
        django_auth.login(request, user)
        return 'success'
    else:
        return 'fail'


# 用户签名+时间戳
def user_sign_api(request):
    if request.method == 'POST':
        client_time = request.POST.get('time', '')  # 客户端时间戳
        client_sign = request.POST.get('sign', '')  # 客户端签名
        print(client_time)
        print(client_sign)
    else:
        return 'error'

    if client_sign == '' and client_time == '':
        return 'sign null'

    # 服务器时间
    now_time = time.time()
    server_time = str(now_time).split('.')[0]
    # 获取时间差
    time_difference = int(server_time) - int(client_time)
    if time_difference >= 60:
        return 'timeout'

    # 签名检查
    md5 = hashlib.md5()
    sign_str = client_time + '&Guest-Bugmaster'
    sign_bytes_utf8 = sign_str.encode(encoding='utf-8')
    md5.update(sign_bytes_utf8)
    server_sign = md5.hexdigest()

    if server_sign != client_sign:
        return 'fail'
    else:
        return 'sign success'


# AES加密
# ======== AES加密算法 ========

BS = 16
unpad = lambda s: s[0: - ord(s[-1])]  # 通过lambda匿名函数对字符串长度进行还原


def decryptBase64(src):
    print(base64.urlsafe_b64decode(src))
    return base64.urlsafe_b64decode(src)  # urlsafe_b64decode() 对Base64加密字符串进行解密


def decryptAES(src, key):
    """解析AES密文"""
    src = decryptBase64(src)  # 将Base64() 加密字符串解密为AES加密字符串
    iv = b'1172311105789011'
    cryptor = AES.new(key, AES.MODE_CBC, iv)
    text = cryptor.decrypt(src).decode()  # decrypt() 对AES加密字符串进行解密
    return unpad(text)


def aes_encryption(request):
    app_key = 'W7v4D60fds2Cmk2U'

    if request.method == 'GET':
        data = request.GET.get('data', '')
    else:
        return 'error'

    # 解密
    decode = decryptAES(data, app_key.encode('utf-8'))  # 调用decryptAES()函数解密
    # 转化为字典
    dict_data = json.loads(decode)
    return dict_data


if __name__ == '__main__':
    decryptBase64('MzgyNjQzNTU4')
