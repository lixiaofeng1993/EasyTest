from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError, ObjectDoesNotExist  # 验证错误
from django.db.utils import IntegrityError  # 完整性错误
from django.db.models import Q  # 与或非 查询
import time, json
import logging
from base.models import Event, Guest

log = logging.getLogger('log')


# from rest_framework.schemas import get_schema_view
#
# from rest_framework.renderers import CoreJSONRenderer
#
# schema_view = get_schema_view(
#     title='A Different API',
#     renderer_classes=[CoreJSONRenderer]
# )


# 添加发布会接口
def add_event(request):
    eid = request.POST.get('eid', '')  # 发布会id
    name = request.POST.get('name', '')  # 发布会标题
    limit = request.POST.get('limit', '')  # 限制人数
    status = request.POST.get('status', '')  # 状态
    address = request.POST.get('address', '')  # 地址
    start_time = request.POST.get('start_time', '')  # 发布会时间

    if eid == '' or name == '' or limit == '' or status == '' or address == '' or start_time == '':
        log.info('默认服务==>  add_event，参数错误，不能为空.')
        return JsonResponse({'status': 200, 'message': 'parameter error', 'error_code': 10021})
    result = Event.objects.filter(id=eid)
    if result:
        log.info('默认服务==>  add_event，发布会id已经存在.')
        return JsonResponse({'status': 200, 'message': 'event id already exists', 'error_code': 10022})
    result = Event.objects.filter(name=name)
    if result:
        log.info('默认服务==>  add_event，发布会名称已经存在.')
        return JsonResponse({'status': 200, 'message': 'event name already exists', 'error_code': 10023})
    if status == '':
        status = 1
    try:
        Event.objects.create(id=eid, name=name, limit=limit, address=address, status=int(status), start_time=start_time)
    except ValidationError as e:
        error = 'start_time format error.It must be in YYYY-MM-DD HH:MM:SS format. error: {}'.format(e)
        log.info('默认服务==>  add_event，发布会开始时间格式错误.')
        return JsonResponse({'status': 200, 'message': error, 'error_code': 10024})
    log.info('默认服务==>  add_event，发布会添加成功！')
    return JsonResponse({'status': 200, 'message': 'add event success'})


# 修改发布会接口
def update_event(request):
    if request.method == 'POST':
        req = json.loads(request.body)
        info = req.get('info', {})
        eid = info.get('eid', '')
        name = info.get('name', '')
        limit = info.get('limit', '')
        status = info.get('status', '')
        address = info.get('address', '')
        start_time = info.get('start_time', '')
        if eid == '':
            log.info('默认服务==>  update_event参数eid，参数错误，不能为空.')
            return JsonResponse({'status': 200, 'message': 'parameter eid error', 'error_code': 10021})
        result = Event.objects.filter(id=eid)
        if not result:
            log.info('默认服务==>  update_event，发布会id不存在，无法修改.')
            return JsonResponse({'status': 200, 'message': 'event id not exists', 'error_code': 10022})
        try:
            result.update(name=name, limit=limit, address=address, status=int(status),
                          start_time=start_time)
        except ValidationError as e:
            error = 'start_time format error.It must be in YYYY-MM-DD HH:MM:SS format. error: {}'.format(e)
            log.info('默认服务==>  update_event，发布会开始时间格式错误.')
            return JsonResponse({'status': 200, 'message': error, 'error_code': 10024})
        log.info('默认服务==>  update_event，发布会 {} 修改成功！'.format(eid))
        return JsonResponse({'status': 200, 'message': 'update event success'})


# 查询发布会接口
def get_event_list(request):
    eid = request.GET.get('eid', '')  # 发布会id
    name = request.GET.get('name', '')  # 发布会名称

    if eid == '' and name == '':
        log.info('默认服务==>  get_event_list，参数错误，不能为空.')
        return JsonResponse({'status': 200, 'message': 'parameter error', 'error_code': 10021})
    if eid != '':
        event = {}
        try:
            result = Event.objects.get(id=eid)
        except ObjectDoesNotExist:
            log.info('默认服务==>  get_event_list，查询结果为空.')
            return JsonResponse({'status': 200, 'message': 'query result is empty', 'error_code': 10022})
        else:
            event['name'] = result.name
            event['limit'] = result.limit
            event['status'] = result.status
            event['address'] = result.address
            event['start_time'] = result.start_time
            event['id'] = result.id
            log.info('默认服务==>  get_event_list，查询发布会成功！')
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
                event['id'] = r.id
                datas.append(event)
            log.info('默认服务==>  get_event_list，查询发布会成功！')
            return JsonResponse({'status': 200, 'message': 'success', 'data': datas})
        else:
            log.info('默认服务==>  get_event_list，查询结果为空.')
            return JsonResponse({'status': 200, 'message': 'query result is empty', 'error_code': 10022})


# 添加嘉宾接口
def add_guest(request):
    eid = request.POST.get('eid', '')  # 关联发布会id
    realname = request.POST.get('realname', '')  # 姓名
    phone = request.POST.get('phone', '')  # 手机号
    email = request.POST.get('email', '')  # 邮箱

    if eid == '' or realname == '' or phone == '':
        log.info('默认服务==>  add_guest，参数错误，不能为空.')
        return JsonResponse({'status': 200, 'message': 'parameter error', 'error_code': 10021})
    result = Event.objects.filter(id=eid)
    if not result:
        log.info('默认服务==>  add_guest，关联Event id 为 null.')
        return JsonResponse({'status': 200, 'message': 'event id null', 'error_code': 10022})
    result = Event.objects.get(id=eid).status
    if not result:
        log.info('默认服务==>  add_guest，Event 状态未激活.')
        return JsonResponse({'status': 200, 'message': 'event status is not available', 'error_code': 10023})

    event_limit = Event.objects.get(id=eid).limit  # 限制人数
    guest_limit = Guest.objects.filter(event_id=eid)  # 发布会已添加的嘉宾数
    if len(guest_limit) >= event_limit:
        log.info('默认服务==>  add_guest，参加发布会的人已满.')
        return JsonResponse({'status': 200, 'message': 'event number is full', 'error_code': 10024})

    event_time = Event.objects.get(id=eid).start_time  # 发布会时间
    etime = str(event_time).split('+')[0]
    timeArray = time.strptime(etime, '%Y-%m-%d %H:%M:%S')
    e_time = int(time.mktime(timeArray))

    now_time = str(time.time())  # 当前时间
    ntime = now_time.split('.')[0]
    now_time = int(ntime)

    if now_time >= e_time:
        log.info('默认服务==>  add_guest，活动已开始.')
        return JsonResponse({'status': 200, 'message': 'event has started', 'error_code': 10025})
    try:
        Guest.objects.create(realname=realname, phone=int(phone), email=email, sign=0, event_id=int(eid))
    except IntegrityError:
        log.info('默认服务==>  add_guest，手机号已存在.')
        return JsonResponse({'status': 200, 'message': 'the event guest phone number repeat', 'error_code': 10026})
    log.info('默认服务==>  add_guest，嘉宾添加成功！')
    return JsonResponse({'status': 200, 'message': 'add guest success'})


# 查询嘉宾接口
def get_guest_list(request):
    name = request.GET.get('name', '')

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
                guest['id'] = event.id
                datas.append(guest)
            log.info('默认服务==>  get_guest_list，查询嘉宾成功！')
            return JsonResponse({'status': 200, 'message': 'success'})
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
                guest['id'] = r.id
                datas.append(guest)
            log.info('默认服务==>  get_guest_list，查询嘉宾成功！')
            return JsonResponse({'status': 200, 'message': 'success'})
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
                log.info('默认服务==>  get_guest_list，查询嘉宾成功！')
                return JsonResponse({'status': 200, 'message': 'success', 'test': False})
            else:
                log.info('默认服务==>  get_guest_list，查询结果为空.')
                return JsonResponse({'status': 200, 'message': 'query result is empty', 'error_code': 10022})


# 签到接口
def user_sign(request):
    eid = request.POST.get('eid', '')  # 发布会id
    phone = request.POST.get('phone', '')  # 嘉宾手机号

    if eid == '' or phone == '':
        log.info('默认服务==>  user_sign，参数错误，不能为空.')
        return JsonResponse({'status': 200, 'message': 'parameter error', 'error_code': 10021})

    result = Event.objects.filter(id=eid)
    if not result:
        return JsonResponse({'status': 200, 'message': 'event id null', 'error_code': 10022})

    result = Event.objects.get(id=eid).status
    if not result:
        log.info('默认服务==>  user_sign，Event 状态未激活.')
        return JsonResponse({'status': 200, 'message': 'event status is not available', 'error_code': 10023})

    event_time = Event.objects.get(id=eid).start_time  # 发布会时间
    etime = str(event_time).split('+')[0]
    timeArray = time.strptime(etime, '%Y-%m-%d %H:%M:%S')
    e_time = int(time.mktime(timeArray))

    now_time = str(time.time())  # 当前时间
    ntime = now_time.split('.')[0]
    now_time = int(ntime)

    if now_time >= e_time:
        log.info('默认服务==>  user_sign，活动已开始.')
        return JsonResponse({'status': 200, 'message': 'event has started', 'error_code': 10024})

    result = Guest.objects.filter(phone=phone)
    if not result:
        log.info('默认服务==>  user_sign，嘉宾手机号不存在.')
        return JsonResponse({'status': 200, 'message': 'user phone null', 'error_code': 10025})

    result = Guest.objects.filter(event_id=eid, phone=phone)
    if not result:
        log.info('默认服务==>  user_sign，嘉宾签到发布会和参加发布会不符.')
        return JsonResponse(
            {'status': 200, 'message': 'user did not participate in the conference', 'error_code': 10026})
    result = Guest.objects.get(event_id=eid, phone=phone).sign
    if result:
        log.info('默认服务==>  user_sign，嘉宾已签到.')
        return JsonResponse({'status': 200, 'message': 'user has sign in', 'error_code': 10027})
    else:
        Guest.objects.filter(event_id=eid, phone=phone).update(sign='1')
        return JsonResponse({'status': 200, 'message': 'sign success'})
