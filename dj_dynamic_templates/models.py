from django.conf import settings
from django.apps import apps
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
import os
import shutil
from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models.functions import Now


class DjDynamicTemplateCategory(models.Model):

    app = models.CharField(
        verbose_name=_('App'), max_length=100,
        help_text=_("Select the Django app where a directory will be created within the 'templates' folder. "
                    "This helps organize templates under the selected app.")
    )
    name = models.CharField(
        verbose_name=_('Category Name'), max_length=100,
        help_text=_("Enter a unique name for the directory that will be created. "
                    "This name will be used as the directory name within the 'templates' folder for the selected app.")
    )

    description = models.TextField(
        verbose_name=_('Description'), null=True, blank=True,
        help_text=_("Provide a brief description of the category. "
                    "This description is optional and can help document the purpose or content of the templates within the created directory")
    )

    created_at = models.DateTimeField(
        verbose_name=_('Created at'), db_default=Now(), editable=False,
        help_text=_("The date and time when this template category was created. "
                    "This field is automatically set to the current date and time when the record is first created.")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, verbose_name=_('Created by'),
        help_text=_("The user who created this template category. "
                    "This field is automatically populated with the user who initially created the record.")
    )

    last_updated_at = models.DateTimeField(
        verbose_name=_('Last Updated at'), auto_now=True, editable=False,
        help_text=_("The date and time when this template category was last updated. "
                    "This field is automatically updated every time the record is modified.")
    )

    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False,
        related_name='dj_dynamic_template_category_last_updated_by', verbose_name=_('Last Updated by'),
        help_text=_("The user who last updated this template category. "
                    "This field is automatically populated with the user making the modification.")
    )

    def __str__(self):
        return f'{self.app} - {self.name}'

    @cached_property
    def directory_path(self):
        return os.path.join(settings.BASE_DIR, self.app, 'templates', self.name)

    @cached_property
    def is_directory_exists(self):
        return os.path.exists(self.directory_path)

    @cached_property
    def files_in_dir(self):
        if self.is_directory_exists:
            return os.listdir(self.directory_path)
        else:
            return list()

    def make_directory(self):
        if not self.is_directory_exists:
            os.makedirs(self.directory_path, exist_ok=False)
            return True
        return False

    def remove_directory(self):
        if self.is_directory_exists:
            shutil.rmtree(self.directory_path, ignore_errors=True)
            return True
        else:
            return False


    class Meta:
        managed = apps.is_installed("dj_dynamic_templates")
        ordering = ('app', )
        unique_together = ('app', 'name')
        permissions = (
            ('can_create_directory', 'Can Create Directory'),
            ('can_delete_directory', 'Can Delete Directory'),
            ('can_view_files_in_directory', 'Can View Files in Directory'),
            ('can_view_directory_status', 'Can View Directory Status')
        )
        db_table = 'dj_dynamic_template_category'
        verbose_name = _(db_table.replace("_", " ").title())
        verbose_name_plural = verbose_name.replace("Category", "Categories")


class DjDynamicTemplate(models.Model):

    category = models.ForeignKey(
        DjDynamicTemplateCategory, on_delete=models.CASCADE, verbose_name=_('Category'),
        help_text=_("Select the category where you want to save the template. "
                    "This categorization helps organize and manage your templates efficiently.")
    )
    template_name = models.CharField(
        verbose_name=_('Template Name'), max_length=100,
        help_text=_("Enter a name for the template. This name will be treated as the template file name. "
                    "A template file(.html) with this name will be created.")
    )
    try:
        from markdownx.models import MarkdownxField
        content = MarkdownxField(
            verbose_name=_('Content'), null=True, blank=True,
            help_text=_("Insert the content of the template. "
                        "This field allows you to define the content of your template, which can include HTML and inline CSS")
        )
    except ModuleNotFoundError:
        content = models.TextField(
            verbose_name=_('Content'), null=True, blank=True,
            help_text=_("Insert the content of the template. "
                        "This field allows you to define the content of your template, which can include HTML and inline CSS")
        )

    template_is_active = models.BooleanField(
        verbose_name=_("Template is Active"), default=True,
        help_text=_("This field determines the current status of the template. "
                    "If set to 'True', the template is considered active. "
                    "If set to 'False', it is considered inactive. Inactive templates will not clone the templates")
    )

    revision_of = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, editable=False, verbose_name=_("Previous Template Revision"),
        help_text=_("This field is used when editing a template. "
                    "Create a new record to represent the updated version of the template and link it to the previous version using this field. "
                    "It indicates the previous template revision that this record is based on.")
    )

    created_at = models.DateTimeField(
        verbose_name=_('Created at'), db_default=Now(), editable=False,
        help_text=_("The date and time when this template was created. "
                    "This field is automatically set to the current date and time when the record is first created.")
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, verbose_name=_('Created by'),
        help_text=_("The user who created this template. "
                    "This field is automatically populated with the user who initially created the record.")
    )

    def clean(self):
        if self.__class__.objects.filter(template_name=self.template_name, category=self.category, template_is_active=True).exclude(pk=self.pk).exists():
            raise ValidationError({'template_name': f'The template with name "{self.template_name}" already exists in the Category {self.category.name} of App {self.category.app}'})

    @cached_property
    def file_path(self):
        return self.category.directory_path + f'/{self.template_name}.html'

    @cached_property
    def is_file_exist(self):
        return os.path.exists(self.file_path)

    def create_file(self):
        if self.category.is_directory_exists:
            file = open(f'{self.file_path}', 'w')
            file.write(self.content)
            file.close()
            return True
        else:
            return False

    def delete_file(self):
        if self.is_file_exist:
            os.remove(self.file_path)
            return True
        else:
            return False

    def __str__(self):
        return f'{self.category.app} - {self.category.name} - {self.template_name}'


    class Meta:
        managed = apps.is_installed("dj_dynamic_templates")
        ordering = ('-created_at', )
        constraints = [
            models.UniqueConstraint(
                fields=('template_name', 'category'),
                condition=models.Q(template_is_active=True),
                name='unique_category_template',
                violation_error_code='DUPLICATE_TEMPLATE_IN_APP_CATEGORY',
                violation_error_message=_('A template with the same name already exists in this category. '
                                          'Please choose a different name or deactivate the existing template.')
            )
        ]
        permissions = (
            ('can_view_inactive_templates', 'Can view the Inactive Templates'),
            ('can_create_file', 'Can Create File'),
            ('can_delete_file', 'Can Delete File'),
            ('can_view_file_status', 'Can View File Status'),
        )
        db_table = 'dj_dynamic_template'
        verbose_name = _(db_table.replace("_", " ").title())
        verbose_name_plural = verbose_name.replace("Template", "Templates")
