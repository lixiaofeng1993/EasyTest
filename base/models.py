from django.db import models
from django.contrib.auth.models import User
from djcelery.models import PeriodicTask


class Sign(models.Model):
    sign_id = models.AutoField(primary_key=True, null=False)
    sign_name = models.CharField(max_length=100)
    sign_type = models.CharField(max_length=100, default="无")
    description = models.CharField(max_length=200)
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.sign_name

    class Meta:
        verbose_name = "签名管理"
        verbose_name_plural = "签名管理"


class Project(models.Model):
    prj_id = models.AutoField(primary_key=True, null=False)
    prj_name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default='')
    sign = models.ForeignKey(Sign, on_delete=models.CASCADE, default='')
    description = models.CharField(max_length=200)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return self.prj_name

    class Meta:
        verbose_name = "项目管理"
        verbose_name_plural = "项目管理"


class Environment(models.Model):
    env_id = models.AutoField(primary_key=True, null=False)
    env_name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    url = models.CharField(max_length=100)
    is_swagger = models.IntegerField(default='')  # 导入swagger
    set_headers = models.TextField(default='')  # 设置默认headers
    private_key = models.CharField(max_length=100)
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.env_name

    class Meta:
        verbose_name = "测试环境"
        verbose_name_plural = "测试环境"


class Interface(models.Model):
    if_id = models.AutoField(primary_key=True, null=False)
    if_name = models.CharField(max_length=100)
    url = models.CharField(max_length=100)
    method = models.CharField(max_length=10)
    data_type = models.CharField(max_length=10)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
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

    class Meta:
        verbose_name = "接口管理"
        verbose_name_plural = "接口管理"


class Case(models.Model):
    case_id = models.AutoField(primary_key=True, null=False)
    case_name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    content = models.TextField()
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.case_name

    class Meta:
        verbose_name = "测试用例"
        verbose_name_plural = "测试用例"


class Plan(models.Model):
    plan_id = models.AutoField(primary_key=True, null=False)
    plan_name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    content = models.TextField()
    report_name = models.CharField(max_length=255, default="")
    make = models.IntegerField(null=True)
    is_locust = models.IntegerField(default="")  # 性能测试
    is_task = models.IntegerField(default="")  # 定时任务
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    def __str__(self):
        return self.plan_name

    class Meta:
        verbose_name = "测试计划"
        verbose_name_plural = "测试计划"


class Report(models.Model):
    report_id = models.AutoField(primary_key=True, null=False)
    report_name = models.CharField(max_length=255)
    report_path = models.CharField(max_length=255, default='', null=True)
    pic_name = models.CharField(max_length=255, default='')
    totalTime = models.CharField(max_length=50, default='')
    startTime = models.CharField(max_length=50, default='')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    content = models.TextField()
    case_num = models.IntegerField(null=True)
    pass_num = models.IntegerField(null=True)
    fail_num = models.IntegerField(null=True)
    error_num = models.IntegerField(null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')
    make = models.IntegerField(null=True)

    def __str__(self):
        return self.report_name

    class Meta:
        verbose_name = "测试报告"
        verbose_name_plural = "测试报告"


# 发布会表
class Event(models.Model):
    name = models.CharField(max_length=100)  # 发布会标题
    limit = models.IntegerField()  # 参加人数
    status = models.BooleanField()  # 状态
    address = models.CharField(max_length=200)  # 地址
    start_time = models.DateTimeField('events time')  # 发布会时间
    create_time = models.DateTimeField(auto_now=True)  # 创建时间(自动获取当前时间)

    # admin中显示发布会名称
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "发布会表"
        verbose_name_plural = "发布会表"


# 嘉宾表
class Guest(models.Model):
    event = models.ForeignKey(Event, related_name='guests', on_delete=models.CASCADE)  # 关联发布会id
    realname = models.CharField(max_length=64)  # 姓名
    phone = models.CharField(max_length=16)  # 手机号
    email = models.EmailField()  # 邮箱
    sign = models.BooleanField()  # 签到状态
    create_time = models.DateTimeField(auto_now=True)  # 创建时间(自动获取当前时间)

    class Meta:
        unique_together = ('event', 'phone')
        verbose_name = "嘉宾表"
        verbose_name_plural = "嘉宾表"

    # admin中显示嘉宾名称
    def __str__(self):
        return self.realname


# locust报告
class LocustReport(models.Model):
    id = models.AutoField(primary_key=True, null=False)
    current_response_time_percentile_50 = models.FloatField(default=0.0, null=True)
    current_response_time_percentile_95 = models.FloatField(default=0.0, null=True)
    fail_ratio = models.FloatField(default=0.0, null=True)
    total_rps = models.FloatField(default=0.0, null=True)
    user_count = models.IntegerField(default=0, null=True)
    errors = models.TextField()
    slaves = models.TextField()
    stats = models.TextField()
    state = models.CharField(max_length=50, default='')
    update_time = models.DateTimeField('更新时间', auto_now=True)
    update_user = models.CharField(max_length=30, default='')

    class Meta:
        verbose_name = "locust报告"
        verbose_name_plural = "locust报告"


class DebugTalk(models.Model):
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)
    belong_project = models.ForeignKey(Project, on_delete=models.CASCADE)
    debugtalk = models.TextField(null=True, default='#debugtalk.py')

    class Meta:
        verbose_name = '驱动py文件'
        db_table = 'DebugTalk'
