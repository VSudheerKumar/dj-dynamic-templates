from django.contrib import admin

from .models import *


class BaseAdmin(admin.ModelAdmin):
    readonly_fields = ['created_at', 'created_by']


@admin.register(DjDynamicTemplateCategory)
class DjDynamicTemplateCategoryAdmin(BaseAdmin):

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['last_updated', 'last_updated_by']
        else:
            return []

    def save_model(self, request, obj, form, change):
        if change:
            obj.last_updated_by = request.user
        else:
            obj.created_by = request.user
        obj.save()


@admin.register(DjDynamicTemplate)
class DjDynamicTemplateAdmin(admin.ModelAdmin):
    pass