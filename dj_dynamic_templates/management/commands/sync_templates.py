from django.core.management.base import BaseCommand, CommandError
from concurrent.futures import ThreadPoolExecutor
import time

from dj_dynamic_templates.forms import DJANGO_APPS
from dj_dynamic_templates.models import *

class Command(BaseCommand):
    help = "Synchronize all templates into project"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--app',
            type=str,
            help='Project app names',
            required=False,
            default=list(dict(DJANGO_APPS).keys()),
            nargs="+"
        )

    def sync_template(self, obj: DjDynamicTemplate) -> bool:
        obj.create_file()
        self.stdout.write(self.style.SUCCESS(f"====> Successfully synced template '{obj.template_name}' in the directory '{obj.category.name}' of app '{obj.category.app}' templates directory. "))
        return True

    def handle(self, *args, **options) -> str:
        for app in options["app"]:
            with ThreadPoolExecutor() as executor:
                for template_obj in DjDynamicTemplate.objects.select_related('category').filter(category__app=app, template_is_active=True).order_by('id'):
                    if template_obj.category.make_directory(exists_ok=True):
                        self.stdout.write(self.style.ERROR("-->"), ending=" ")
                        self.stdout.write(self.style.WARNING(f"Directory '{template_obj.category.name}' is does not exist in template directory of app '{template_obj.category.app}'."), ending=' ')
                        self.stdout.write(self.style.MIGRATE_HEADING(f"So, Created an new Directory '{template_obj.category.name}' in template directory of app '{template_obj.category.app}'"))
                    executor.submit(self.sync_template, template_obj)
        return "Successfully synced all templates into respective project app's template directory"