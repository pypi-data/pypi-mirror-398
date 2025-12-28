
from django.core.management import call_command
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
import shutil,os


class Command(BaseCommand):
    help = 'Creates bot_panel directory structure in Django root'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if directory exists',
        )

    def handle(self, *args, **options):
        # Get Django project root (where manage.py is located)
        django_root = Path(settings.BASE_DIR)
        core_dir = django_root / 'core'
        call_command('utils_env', add_missing=True, show_values=True)

        try:
            first_run=not os.path.exists(core_dir / 'celery_config.py')
            # Get the dj_utils package directory
            dj_utils_dir = Path(__file__).resolve().parent.parent.parent
            shutil.copy(dj_utils_dir/'copy_files/__init__.py', core_dir)
            shutil.copy(dj_utils_dir/'copy_files/celery_config.py', core_dir)
            shutil.copy(dj_utils_dir/'copy_files/tasks_config.py', core_dir)
            shutil.copy(dj_utils_dir/'copy_files/makemigrations.py', django_root)
            shutil.copy(dj_utils_dir/'copy_files/Dockerfile', django_root)
            shutil.copy(dj_utils_dir/'copy_files/docker-compose.yml', django_root)
            shutil.copy(dj_utils_dir/'copy_files/entrypoint.sh', django_root)
            shutil.copy(dj_utils_dir/'copy_files/requirements.txt', django_root)
            # shutil.copy(dj_utils_dir/'copy_files/docker-compose-dev.yml', django_root)
            shutil.copy(dj_utils_dir/'copy_files/.gitignore', django_root)

            if first_run:
                with open(dj_utils_dir/'copy_files/settings.py') as f:
                    new_setting='\n\n'+ f.read()
                with open(core_dir / 'settings.py', 'a+') as f:
                    f.write(f.read() + new_setting)

                with open(dj_utils_dir/'copy_files/urls.py') as f:
                    new_url='\n\n'+ f.read()
                with open(core_dir / 'urls.py', 'a+') as f:
                    f.write(f.read() + new_url)


            self.stdout.write(
                self.style.SUCCESS('\n✅ Initialization completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during initialization: {str(e)}')
            )
            raise
