from django.shortcuts import render
from django.template.exceptions import TemplateDoesNotExist
from django.http import HttpResponse

from .models import DjDynamicTemplate

# Create your views here.
def template_view(request, template_id: int):
    try:
        return render(request, DjDynamicTemplate.objects.get(id=template_id).file_path)
    except TemplateDoesNotExist:
        return HttpResponse("<h1>Template file Does not Exist...!", status=404)

