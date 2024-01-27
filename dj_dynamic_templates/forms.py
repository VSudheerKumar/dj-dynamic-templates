from django.conf import settings
import os

from django import forms
from .models import *


DJANGO_APPS = []

for app in os.listdir(settings.BASE_DIR):
    if os.path.isdir(os.path.join(settings.BASE_DIR, app)) and apps.is_installed(app):
        DJANGO_APPS.append((app, app.replace("_", " ").title()))

class DjDynamicTemplateCategoryForm(forms.ModelForm):

    app = forms.ChoiceField(choices=DJANGO_APPS, widget=forms.Select())


    class Meta:
        model = DjDynamicTemplateCategory
        fields = '__all__'