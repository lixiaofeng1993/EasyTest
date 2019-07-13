from django.db import models
from django.contrib.auth.models import User


class Sign(models.Model):
    sign_id = models.AutoField(primary_key=True, null=False)
    sign_name = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.sign_name


class Project(models.Model):
    prj_id = models.AutoField(primary_key=True, null=False)
    prj_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default='')
    sign = models.ForeignKey('Sign', on_delete=models.CASCADE, default='')
    description = models.CharField(max_length=200)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return self.prj_name


class Environment(models.Model):
    env_id = models.AutoField(primary_key=True, null=False)
    env_name = models.CharField(max_length=100)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    url = models.CharField(max_length=100)
    is_swagger = models.IntegerField(default='')  # 导入swagger
    set_headers = models.TextField(default='')  # 设置默认headers
    private_key = models.CharField(max_length=100)
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.env_name


class Interface(models.Model):
    if_id = models.AutoField(primary_key=True, null=False)
    if_name = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    method = models.CharField(max_length=10)
    data_type = models.CharField(max_length=10)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    is_sign = models.IntegerField()
    is_header = models.IntegerField(default='')  # 标记设置header接口
    set_mock = models.TextField(default='')  # 设置mock
    description = models.CharField(max_length=200)
    request_header_param = models.TextField()
    request_body_param = models.TextField()
    response_header_param = models.TextField()
    response_body_param = models.TextField()
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.if_name


class Case(models.Model):
    case_id = models.AutoField(primary_key=True, null=False)
    case_name = models.CharField(max_length=100)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    content = models.TextField()
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.case_name


class Plan(models.Model):
    plan_id = models.AutoField(primary_key=True, null=False)
    plan_name = models.CharField(max_length=100)
    project = models.ForeignKey('Project', on_delete=models.CASCADE)
    environment = models.ForeignKey('Environment', on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    content = models.TextField()
    report_name = models.CharField(max_length=255, default="")
    make = models.IntegerField(null=True)
    is_locust = models.IntegerField(default='')  # 性能测试
    is_task = models.IntegerField(default='')  # 定时任务
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.plan_name


class Report(models.Model):
    report_id = models.AutoField(primary_key=True, null=False)
    report_name = models.CharField(max_length=255)
    pic_name = models.CharField(max_length=255, default='')
    totalTime = models.CharField(max_length=50, default='')
    startTime = models.CharField(max_length=50, default='')
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE)
    content = models.TextField()
    case_num = models.IntegerField(null=True)
    pass_num = models.IntegerField(null=True)
    fail_num = models.IntegerField(null=True)
    error_num = models.IntegerField(null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.report_name
