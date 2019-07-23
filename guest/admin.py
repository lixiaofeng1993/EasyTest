from django.contrib import admin
from guest.models import Event, Guest


class EventAdmin(admin.ModelAdmin):
    # list_display 字段名称的数组，定义要在列表中显示的字段 search_fields 设置搜索关键字匹配 list_filter 表字段过滤器
    list_display = ['id', 'name', 'status', 'address', 'start_time', 'create_time']
    search_fields = ['name', 'address']  # 搜索栏
    list_filter = ['status']  # 过滤器


class GuestAdmin(admin.ModelAdmin):
    list_display = ['realname', 'phone', 'email', 'sign', 'create_time', 'event']
    search_fields = ['realname', 'phone']  # 搜索栏
    list_filter = ['sign']  # 过滤器


admin.site.register(Event, EventAdmin)  # 使用EventAdmin类在admin中注册models
admin.site.register(Guest, GuestAdmin)  # 使用GuestAdmin类在admin中注册models
