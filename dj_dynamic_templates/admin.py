import os
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.contrib.auth.admin import UserAdmin
from .forms import *


@admin.register(DjDynamicTemplateCategory)
class DjDynamicTemplateCategoryAdmin(admin.ModelAdmin):

    list_display = ['id', 'app', 'name', 'last_updated_at', 'last_updated_by']
    list_per_page = 20
    list_filter = ['app', 'created_by', 'last_updated_by', 'last_updated_at']
    list_select_related = True
    list_display_links = ['id', 'app', 'name']
    search_fields = ['name']
    search_help_text = 'Search with Category Name'
    date_hierarchy = 'created_at'

    change_form_template = 'category_change_form.html'
    form = DjDynamicTemplateCategoryForm
    actions = ['create_directory', 'delete_directory']
    readonly_fields = ['created_by', 'created_at', 'last_updated_at', 'last_updated_by']

    fieldsets = [
        ('Basic Information', {
            'fields': ['app', 'name', 'description'],
            'classes': ['wide']
        }),
        ('Creation Details', {
            'fields': ['created_at', 'created_by'],
            'classes': ['collapse', 'wide']
        }),
        ('Update Details', {
            'fields': ['last_updated_at', 'last_updated_by'],
            'classes': ['collapse', 'wide']
        }),
    ]

    @staticmethod
    def is_directory_exists(obj):
        if obj.is_directory_exists:
            return format_html("""<img src="/static/admin/img/icon-yes.svg" alt="True">""")
        else:
            return format_html("""<img src="/static/admin/img/icon-no.svg" alt="True">""")

    def get_list_display(self, request):
        fields = self.list_display.copy()
        if request.user.has_perm('dj_dynamic_templates.can_view_directory_status'):
            fields.append('is_directory_exists')
        return fields

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return [self.fieldsets[0]]
        fieldsets = self.fieldsets.copy()
        if request.user.has_perm('dj_dynamic_templates.can_view_directory_status'):
            fieldsets.append(('Directory Details', {'fields': ['is_directory_exists'], 'classes': ['wide']}))
        if request.user.has_perm('dj_dynamic_templates.can_view_files_in_directory'):
            if fieldsets[-1][0] == 'Directory Details':
                fieldsets[-1][1]['fields'].append('files_in_directory')
            else:
                fieldsets.append(('Directory Details', {'fields': ['files_in_directory'], 'classes': ['wide']}))
        return fieldsets

    def get_actions(self, request):
        actions = super(DjDynamicTemplateCategoryAdmin, self).get_actions(request)
        if not request.user.has_perm('dj_dynamic_templates.can_create_directory'):
            del actions['create_directory']
        if not request.user.has_perm('dj_dynamic_templates.can_delete_directory'):
            del actions['delete_directory']
        return actions

    def get_readonly_fields(self, request, obj=None):
        fields = self.readonly_fields.copy()
        if obj:
            if request.user.has_perm('dj_dynamic_templates.can_view_directory_status'):
                fields.append('is_directory_exists')
            if request.user.has_perm('dj_dynamic_templates.can_view_files_in_directory'):
                fields.append('files_in_directory')
            return fields
        else:
            return []

    @staticmethod
    def files_in_directory(obj):
        return format_html("<ol>" + "".join(['<li>{file_name}</li>'.format(file_name=file) for file in obj.files_in_dir]) + "</ol>")

    @admin.action(description='Generate Category Folders for selected Records')
    def create_directory(self, request, queryset):
        for obj in queryset:
            if obj.make_directory():
                self.message_user(request, f"Directory '{obj.name}' has been successfully created in the 'templates' directory of the '{obj.app}' app.", messages.SUCCESS)
            else:
                self.message_user(request, f"Directory '{obj.name}' already exists in the 'templates' directory of the '{obj.app}' app.", messages.ERROR)

    @admin.action(description='Delete Directory for selected Records')
    def delete_directory(self, request, queryset):
        for obj in queryset:
            if obj.remove_directory():
                self.message_user(request, f"Directory '{obj.name}' has been successfully deleted in the 'templates' directory of the '{obj.app}' app.", messages.SUCCESS)
            else:
                self.message_user(request, f"Directory '{obj.name}' does not exist in the 'templates' directory of the '{obj.app}' app.", messages.ERROR)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if '_sync_dir' in request.POST:
            self.create_directory(request, [self.get_object(request, object_id)])
            return redirect('.')
        elif '_rmdir' in request.POST:
            self.delete_directory(request, [self.get_object(request, object_id)])
            return redirect('.')
        return super().changeform_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if change:
            obj.last_updated_by = request.user
            old_obj = self.model.objects.get(pk=obj.pk)
        else:
            obj.created_by = obj.last_updated_by = request.user
            if '_make_dir' in request.POST:
                self.create_directory(request, [obj])
        obj.save()
        if change and old_obj.directory_path != obj.directory_path and '_make_dir' in request.POST:
            try:
                os.rename(old_obj.directory_path, obj.directory_path)
                self.message_user(request, f"Directory path updated: Changed from '{old_obj.directory_path}' to '{obj.directory_path}'.", messages.SUCCESS)
            except FileExistsError:
                self.message_user(request, f"Directory '{obj.name}' already exists in the 'templates' directory of the '{obj.app}' app.", messages.ERROR)
            except FileNotFoundError:
                if old_obj.app != obj.app:
                    self.create_directory(request, [obj])
                else:
                    self.message_user(request, f"Directory '{old_obj.name}' does not exist in the 'templates' directory of the '{old_obj.app}' app.", messages.ERROR)

    def delete_model(self, request, obj):
        obj.remove_directory()
        obj.delete()


@admin.register(DjDynamicTemplate)
class DjDynamicTemplateAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        else:
            return []

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.save()