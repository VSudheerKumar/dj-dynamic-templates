
import django.db.models.deletion
import django.db.models.functions.datetime

from django.conf import settings
from django.db import migrations, models

try:
    from markdownx.models import MarkdownxField
    content_field = MarkdownxField
except ModuleNotFoundError:
    content_field = models.TextField


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DjDynamicTemplateCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app', models.CharField(help_text="Select the Django app where a directory will be created within the 'templates' folder. This helps organize templates under the selected app.", max_length=100, verbose_name='App')),
                ('name', models.CharField(help_text="Enter a unique name for the directory that will be created. This name will be used as the directory name within the 'templates' folder for the selected app.", max_length=100, verbose_name='Category Name')),
                ('description', models.TextField(blank=True, help_text='Provide a brief description of the category. This description is optional and can help document the purpose or content of the templates within the created directory', null=True, verbose_name='Description')),
                ('created_at', models.DateTimeField(db_default=django.db.models.functions.datetime.Now(), editable=False, help_text='The date and time when this template category was created. This field is automatically set to the current date and time when the record is first created.', verbose_name='Created at')),
                ('last_updated_at', models.DateTimeField(auto_now=True, help_text='The date and time when this template category was last updated. This field is automatically updated every time the record is modified.', verbose_name='Last Updated at')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text='The user who created this template category. This field is automatically populated with the user who initially created the record.', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Created by')),
                ('last_updated_by', models.ForeignKey(blank=True, editable=False, help_text='The user who last updated this template category. This field is automatically populated with the user making the modification.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dj_dynamic_template_category_last_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Last Updated by')),
            ],
            options={
                'verbose_name': 'Dj Dynamic Template Category',
                'verbose_name_plural': 'Dj Dynamic Template Categories',
                'db_table': 'dj_dynamic_template_category',
                'ordering': ('app',),
                'permissions': (('can_create_directory', 'Can Create Directory'), ('can_delete_directory', 'Can Delete Directory'), ('can_view_files_in_directory', 'Can View Files in Directory'), ('can_view_directory_status', 'Can View Directory Status')),
                'managed': True,
                'unique_together': {('app', 'name')},
            },
        ),
        migrations.CreateModel(
            name='DjDynamicTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_name', models.CharField(help_text='Enter a name for the template. This name will be treated as the template file name. A template file(.html) with this name will be created.', max_length=100, verbose_name='Template Name')),
                ('content', content_field(blank=True, help_text='Insert the content of the template. This field allows you to define the content of your template, which can include HTML and inline CSS', null=True, verbose_name='Content')),
                ('template_is_active', models.BooleanField(default=True, help_text="This field determines the current status of the template. If set to 'True', the template is considered active. If set to 'False', it is considered inactive. Inactive templates will not clone the templates", verbose_name='Template is Active')),
                ('created_at', models.DateTimeField(db_default=django.db.models.functions.datetime.Now(), editable=False, help_text='The date and time when this template was created. This field is automatically set to the current date and time when the record is first created.', verbose_name='Created at')),
                ('created_by', models.ForeignKey(blank=True, editable=False, help_text='The user who created this template. This field is automatically populated with the user who initially created the record.', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Created by')),
                ('revision_of', models.ForeignKey(blank=True, editable=False, help_text='This field is used when editing a template. Create a new record to represent the updated version of the template and link it to the previous version using this field. It indicates the previous template revision that this record is based on.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='dj_dynamic_templates.djdynamictemplate', verbose_name='Previous Template Revision')),
                ('category', models.ForeignKey(help_text='Select the category where you want to save the template. This categorization helps organize and manage your templates efficiently.', on_delete=django.db.models.deletion.CASCADE, to='dj_dynamic_templates.djdynamictemplatecategory', verbose_name='Category')),
            ],
            options={
                'verbose_name': 'Dj Dynamic Template',
                'verbose_name_plural': 'Dj Dynamic Templates',
                'db_table': 'dj_dynamic_template',
                'ordering': ('-created_at',),
                'permissions': (('can_view_inactive_templates', 'Can view the Inactive Templates'), ('can_create_file', 'Can Create File'), ('can_delete_file', 'Can Delete File'), ('can_view_file_status', 'Can View File Status')),
                'managed': True,
            },
        ),
        migrations.AddConstraint(
            model_name='djdynamictemplate',
            constraint=models.UniqueConstraint(condition=models.Q(('template_is_active', True)), fields=('template_name', 'category'), name='unique_category_template', violation_error_code='DUPLICATE_TEMPLATE_IN_APP_CATEGORY', violation_error_message='A template with the same name already exists in this category. Please choose a different name or deactivate the existing template.'),
        ),
    ]
