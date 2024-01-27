from django.shortcuts import render

from .models import DjDynamicTemplate

# Create your views here.
def template_view(request, template_id):
    return render(request, DjDynamicTemplate.objects.get(id=template_id).file_path)
