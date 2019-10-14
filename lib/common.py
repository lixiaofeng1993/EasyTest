import traceback

from flask import json
from sqlalchemy.exc import IntegrityError

from mocks.models import Api


def insert_mock_data(**kwargs):
    try:
        name = kwargs.pop('name')
        project = kwargs.pop('project')
        url = kwargs.pop('url')
        method = kwargs.pop("method")
    except KeyError:
        return {
            'success': False,
            'code': '0009',
            'msg': 'name or url missed'
        }

    if project == '':
        return {
            'success': False,
            'code': '0003',
            'msg': 'please select project'
        }

    if name == '' or url == '':
        return {
            'success': False,
            'code': '0001',
            'msg': 'name or url can not be null'
        }

    if Api.objects.filter(project_id=project).filter(name=name):
        return {
            'success': False,
            'code': '0011',
            'msg': 'api name already exist'
        }

    args = ['GET', 'POST', 'PUT', 'DELETE']

    if method.upper() not in args:
        return {
            'success': False,
            'code': '0009',
            'msg': 'method must in {args}'.format(args=args)
        }

    else:
        body = {
            "name": name,
            "url": url,
            "method": method.upper(),
            "data": {},
            "invalid": {},
            "valid": {}
        }

        body = json.dumps(body, ensure_ascii=False, indent=4, separators=(',', ': '))
        m = Api(name=name, body=body, method=method, url=url, project_id=project)
        try:
            m.save()
            return {
                'success': True,
                'code': '0000',
                'msg': 'success'
            }
        except IntegrityError:
            return {
                'success': False,
                'code': '0002',
                'msg': 'the api {url} is exists'.format(url=url),
            }

        except Exception:
            return {
                'success': False,
                'code': '0010',
                'msg': 'system error',
                'traceback': traceback.format_exc()
            }


def update_mock_data(index, **kwargs):
    name = kwargs.get('name')
    url = kwargs.get('url')
    method = kwargs.get("method")
    print(name, url, method, 11111111111111111)
    if name is None:
        return {
            'success': False,
            'code': '0011',
            'msg': 'mock api name must be need'
        }

    if url is None:
        return {
            'success': False,
            'code': '0012',
            'msg': 'mock api url must be need'
        }

    if method is None:
        return {
            'success': False,
            'code': '0013',
            'msg': 'mock api method must be need'
        }

    if name == '' or url == '':
        return {
            'success': False,
            'code': '0001',
            'msg': 'name or url can not be null'
        }

    args = ['GET', 'POST', 'PUT', 'DELETE']

    if method.upper() not in args:
        return {
            'success': False,
            'code': '0009',
            'msg': 'method must in {args}'.format(args=args)
        }

    else:
        body = json.dumps(kwargs, ensure_ascii=False, indent=4, separators=(',', ': '))
        try:
            Api.objects.filter(id=index).update(name=name, body=body, method=method, url=url)
            return {
                'success': True,
                'code': '0000',
                'msg': 'success'
            }
        except IntegrityError:
            return {
                'success': False,
                'code': '0002',
                'msg': 'the api {url} is exists'.format(url=url),
            }

        except Exception:
            return {
                'success': False,
                'code': '0010',
                'msg': 'system error',
                'traceback': traceback.format_exc()
            }
