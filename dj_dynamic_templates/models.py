from django.conf import settings
from django.apps import apps

from django.db import models
from django.db.models.functions import Now

# Create your models here.

class BaseModel(models.Model):

    created_at = models.DateTimeField(db_default=Now(), editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False)


    class Meta:
        abstract = True


class DjDynamicTemplateCategory(BaseModel):

    app_name = models.CharField(max_length=100, help_text="In this App, Directory will be created within templates folder")
    category_name = models.CharField(max_length=100, help_text="Will use this name as an Directory name")
    description = models.TextField(null=True, blank=True, help_text="Description of the category")

    last_updated = models.DateTimeField(auto_now=True, editable=False)
    last_updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='dj_dynamic_template_category_last_updated_by')

    def __str__(self):
        return f'{self.app_name} - {self.category_name}'


    class Meta:
        managed = apps.is_installed("dj_dynamic_templates")
        ordering = ('app_name', )
        unique_together = ('app_name', 'category_name')
        db_table = 'dj_dynamic_template_category'
        verbose_name = db_table.replace("_", " ").title()
        verbose_name_plural = verbose_name.replace("Category", "Categories")


class DjDynamicTemplate(BaseModel):

    category = models.ForeignKey(DjDynamicTemplateCategory, on_delete=models.CASCADE, help_text="Select the category where you want to save the template")
    template_name = models.CharField(max_length=100, help_text="Entered name will treated as template file name, A template file is created with this file name")
    content = models.TextField(null=True, blank=True, help_text="Insert the content of the template")

    is_active = models.BooleanField(default=True, help_text="This field determines the current status of the template")
    parent_obj = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, editable=False)

    def __str__(self):
        return f'{self.category.app_name} - {self.category.category_name} - {self.template_name}'


    class Meta:
        managed = apps.is_installed("dj_dynamic_templates")
        ordering = ('-created_at', )
        constraints = [
            models.UniqueConstraint(
                fields=('template_name', 'category'),
                condition=models.Q(is_active=True),
                name='unique_category_template',
                violation_error_code=1,
                violation_error_message='They is an already an template in this category'
            )
        ]
        db_table = 'dj_dynamic_template'
        verbose_name = db_table.replace("_", " ").title()
        verbose_name_plural = verbose_name.replace("Template", "Templates")
