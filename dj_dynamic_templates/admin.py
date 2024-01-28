import os
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import reverse, path, include
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError, transaction
from .forms import *
from .views import template_view

try:
    from markdownx.admin import MarkdownxModelAdmin
except ModuleNotFoundError:
    class MarkdownxModelAdmin(admin.ModelAdmin):
        pass


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
        obj.save()
        if '_make_dir' in request.POST:
            self.create_directory(request, [obj])
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
class DjDynamicTemplateAdmin(MarkdownxModelAdmin):
    list_display = ['category', 'template_name', 'created_at', 'created_by']
    list_select_related = True
    list_display_links = ['category', 'template_name', 'id']
    list_filter = ['category', 'created_by', 'created_at']
    readonly_fields = ['created_at', 'created_by']
    exclude = ['template_is_active']
    actions = ['sync_templates', 'delete_templates']
    change_form_template = 'template_change_form.html'

    def get_actions(self, request):
        actions = super(DjDynamicTemplateAdmin, self).get_actions(request)
        if not request.user.has_perm('dj_dynamic_templates.can_create_file'):
            del actions['sync_templates']
        if not request.user.has_perm('dj_dynamic_templates.can_delete_file'):
            del actions['delete_templates']
        return actions

    def get_exclude(self, request, obj=None):
        if not request.user.has_perm('dj_dynamic_templates.can_view_inactive_templates'):
            return self.exclude + ['revision_of']
        return super().get_exclude(request, obj)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        if (change and obj) or add:
            context['template_is_active'] = obj.template_is_active if not add else True
        return super().render_change_form(request, context, add, change)

    def get_queryset(self, request):
        queryset = super(DjDynamicTemplateAdmin, self).get_queryset(request)
        if not request.user.has_perm('dj_dynamic_templates.can_view_inactive_templates'):
            queryset = queryset.exclude(template_is_active=False)
        return queryset

    def get_list_filter(self, request):
        list_filter = self.list_filter.copy()
        if request.user.has_perm('dj_dynamic_templates.can_view_inactive_templates'):
            list_filter += ['template_is_active']
        return list_filter

    def get_list_display(self, request):
        list_display = self.list_display.copy()
        if request.user.has_perm('dj_dynamic_templates.can_view_inactive_templates'):
            list_display += ['template_is_active']
            list_display.insert(0, 'id')
        if request.user.has_perm('dj_dynamic_templates.can_view_file_status'):
            list_display.append('template_status')
        return list_display

    def get_readonly_fields(self, request, obj=None):
        if obj:
            fields = self.readonly_fields + ['revision_of']
            if obj.template_is_active:
                if request.user.has_perm('dj_dynamic_templates.can_view_file_status'):
                    fields.append('template_status')
            return fields
        else:
            return []

    @transaction.atomic()
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        elif '_make_template' in request.POST:
            old_obj = self.model.objects.get(pk=obj.pk)
            old_obj.template_is_active = False
            old_obj.save()
            old_obj.delete_file()
            obj.created_by = request.user
            obj.revision_of = old_obj
            obj.pk = None
            self.sync_templates(request, [obj])
        obj.save()
        if '_make_template' in request.POST:
            self.sync_templates(request, [obj])

    @admin.action(description='Sync Templates to File for selected records')
    def sync_templates(self, request, queryset):
        for obj in queryset:
            if not obj.template_is_active:
                self.message_user(request, f"'{obj.template_name}' Template is Inactive. So, Unable to sync")
            elif obj.create_file():
                self.message_user(request, f"Successfully synced template '{obj.template_name}' into '{obj.category.name} directory of App '{obj.category.app}' template's directory", messages.SUCCESS)
            else:
                if obj.category.make_directory():
                    self.message_user(request, f"Directory does not exist so, '{obj.name}' directory has been created in the 'templates' directory of the '{obj.app}' app.", messages.WARNING)
                    obj.create_file()
                    self.message_user(request, f"Successfully synced template '{obj.template_name}' into '{obj.category.name} directory of App {obj.category.app}' template's directory", messages.SUCCESS)

    @admin.action(description='Delete Template Files for selected records')
    def delete_templates(self, request, queryset):
        for obj in queryset:
            if obj.delete_file():
                self.message_user(request, f"Successfully deleted template '{obj.template_name}' in '{obj.category.name} directory of App {obj.category.app}' template's directory", messages.SUCCESS)
            else:
                self.message_user(request, f"Template File does not exist for template {obj.template_name} to delete it...!", messages.ERROR)

    def has_change_permission(self, request, obj=None):
        return super(DjDynamicTemplateAdmin, self).has_change_permission(request, obj) and (obj.template_is_active if obj else True)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        if object_id:
            extra_context = extra_context or {}
            extra_context['show_save_and_continue'] = obj.template_is_active
            extra_context['show_save'] = obj.template_is_active
            extra_context['show_save_and_add_another'] = obj.template_is_active
        if '_sync_template' in request.POST:
            self.sync_templates(request, [obj])
            return redirect('.')
        elif '_remove_template' in request.POST:
            self.delete_templates(request, [obj])
            return redirect('.')
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        urls = super(DjDynamicTemplateAdmin, self).get_urls()
        return [path('template-view/<int:template_id>/', template_view)] + urls

    # @staticmethod
    # def view_template(obj):
    #     return format_html(f"<a href='/admin/dj_dynamic_templates/djdynamictemplate/template-view/{obj.id}/' data-popup='yes' class='related-widget-wrapper-link'>Click Here to View Template</a>")

    @staticmethod
    def template_status(obj):
        if obj.template_is_active is False:
            return "Inactive"
        elif obj.category.is_directory_exists is False:
            return "Directory Does Not Exists"
        elif obj.is_file_exist is False:
            return "File Does Not Exists"
        else:
            with open(obj.file_path, 'r') as file:
                data = file.read().replace('\r', '')
            content = obj.content.replace('\r', '')
            if data == content:
                return "Synced"
            else:
                return "Not Synced"
