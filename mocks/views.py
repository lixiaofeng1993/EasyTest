from django.shortcuts import render
from lib.execute import get_user, is_superuser
from .models import Api
from lib.common import insert_mock_data
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
import json


def mock_api(request):
    user_id = request.session.get('user_id', '')
    if not get_user(user_id):
        request.session['login_from'] = '/base/plan/'
        return render(request, 'user/login_action.html')
    else:
        if request.method == 'POST':
            data = eval(request.body.decode('utf-8'))
            msg = insert_mock_data(**data)
            print(msg, 111111111111111111)
            return JsonResponse(msg)
        else:
            prj_list = is_superuser(user_id)

            info = {
                'prj_list': prj_list
            }
            return render(request, 'mocks/index.html', info)


def add_api(request):
    if request.method == 'POST':
        print(11111111111111)
        return render(request, 'mocks/index.html')
