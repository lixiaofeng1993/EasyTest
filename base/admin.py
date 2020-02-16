from django.contrib import admin
from .models import Sign, Project, Environment, Interface, Case, Plan, Report, ModularTable, UserPower


class ModelAdmin(admin.ModelAdmin):
    list_display = ["id", "url", "Icon", "model_name"]
    list_filter = ["model_name"]
    search_fields = ["model_name"]


class LocustAdmin(admin.ModelAdmin):
    list_display = ["id", "current_response_time_percentile_50", "current_response_time_percentile_95", "fail_ratio",
                    "total_rps", "user_count", "errors", "slaves", "stats", "update_time", "update_user"]
    list_filter = ["total_rps"]
    search_fields = ["stats", "update_user"]


class SignAdmin(admin.ModelAdmin):
    list_display = ["sign_id", "sign_name", "description", "update_user", "update_time"]
    list_filter = ["update_time"]
    search_fields = ["sign_name", "update_user"]


class ReportAdmin(admin.ModelAdmin):
    list_display = ["report_id", "report_name", "totalTime", "startTime", "plan", "case_num", "pass_num", "fail_num",
                    "error_num", "make", "update_user", "update_time"]
    list_filter = ["update_time"]
    search_fields = ["report_name", "update_user", "make"]


class PlanAdmin(admin.ModelAdmin):
    list_display = ["plan_id", "plan_name", "project", "environment", "is_locust", "is_task", "content", "update_user",
                    "update_time"]
    list_filter = ["update_time"]
    search_fields = ["plan_name", "update_user"]


class CaseAdmin(admin.ModelAdmin):
    list_display = ["case_id", "case_name", "project", "description", "update_user", "update_time"]
    list_filter = ["update_time"]
    search_fields = ["env_name", "update_user"]


class InterfaceAdmin(admin.ModelAdmin):
    list_display = ["if_id", "if_name", "project", "url", "method", "data_type", "is_sign", "is_header", "set_mock",
                    "update_user", "update_time"]
    list_filter = ["update_time"]
    search_fields = ["if_name", "update_user"]


class EnvAdmin(admin.ModelAdmin):
    list_display = ["env_id", "env_name", "project", "url", "is_swagger", "private_key", "update_user", "update_time"]
    list_filter = ["update_time"]
    search_fields = ["env_name", "update_user"]


class ProjectAdmin(admin.ModelAdmin):
    list_display = ["prj_id", "prj_name", "sign", "description", "user", "update_time"]
    list_filter = ["update_time"]
    search_fields = ["prj_name", "user"]


admin.site.register(Project, ProjectAdmin)
admin.site.register(Environment, EnvAdmin)
admin.site.register(Interface, InterfaceAdmin)
admin.site.register(Case, CaseAdmin)
admin.site.register(Plan, PlanAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(Sign, SignAdmin)
admin.site.register(ModularTable, ModelAdmin)
admin.site.register(UserPower)
