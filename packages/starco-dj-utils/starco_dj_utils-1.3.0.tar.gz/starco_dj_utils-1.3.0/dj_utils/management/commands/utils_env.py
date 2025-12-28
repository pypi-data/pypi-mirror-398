
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Check and add missing environment variables to .env file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--add-missing',
            action='store_true',
            help='Automatically add missing variables with default values',
        )
        parser.add_argument(
            '--show-values',
            action='store_true',
            help='Show current values of environment variables',
        )

    def handle(self, *args, **options):
        django_root = Path(settings.BASE_DIR)
        env_file = django_root / '.env'
        
        add_missing = options.get('add_missing', False)
        show_values = options.get('show_values', False)

        # Define required environment variables with default values
        required_env_vars = {
            'DEBUG':1,
            'MULTI_LANGUAGES':0,

            'PROJECT_NAME': 'project_name',
            'UTILS_BOT_TOKEN': '',
            'UTILS_TELEGRAM_CHAT_ID': '',
            'BACKUP_DB_TELEGRAM_CHAT_ID':'',
            'ALLOWED_HOSTS':'web 127.0.0.1 localhost',
            'CSRF_TRUSTED_ORIGINS': '',
            'CORS_ALLOWED_ORIGINS': '',
            'POSTGRES_DB': 'DB_NAME',
            'POSTGRES_USER': 'DB_USER',
            'POSTGRES_PASSWORD': 'DB_PASSWORD',
            'POSTGRES_HOST': 'db',
            'POSTGRES_PORT': 5432,
            'CELERY_BROKER_URL':'redis://redis:6379/1',
            'CELERY_RESULT_BACKEND': 'redis://redis:6379/1',
            'CACHE_URL': 'redis://redis:6379/0',
            'BACKUP_EVERY_SECOND':3600,
            'DJANGO_SUPERUSER_EMAIL':'',
            'DJANGO_SUPERUSER_PASSWORD':'',
            'DJANGO_SUPERUSER_USERNAME':'',

        }

        try:
            # Check if .env file exists
            if not env_file.exists():
                self.stdout.write(
                    self.style.WARNING('⚠️  .env file not found!')
                )
                
                if add_missing:
                    env_file.touch()
                    self.stdout.write(
                        self.style.SUCCESS('✓ Created new .env file')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            'Use --add-missing flag to create .env file'
                        )
                    )
                    return

            # Read existing .env content
            existing_vars = {}
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            existing_vars[key.strip()] = value.strip()

            # Check for missing and existing variables
            missing_vars = []
            existing_required_vars = []
            
            for var_name, default_value in required_env_vars.items():
                if var_name not in existing_vars:
                    missing_vars.append((var_name, default_value))
                else:
                    existing_required_vars.append((var_name, existing_vars[var_name]))

            # Display results
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.HTTP_INFO('Environment Variables Status'))
            self.stdout.write('='*60 + '\n')

            # Show existing variables
            if existing_required_vars:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Found {len(existing_required_vars)} required variables:')
                )
                for var_name, var_value in existing_required_vars:
                    if show_values:
                        # Mask sensitive values
                        if any(sensitive in var_name.lower() for sensitive in ['token', 'password', 'secret', 'key']):
                            display_value = var_value[:4] + '*' * (len(var_value) - 4) if len(var_value) > 4 else '****'
                        else:
                            display_value = var_value
                        self.stdout.write(f'  • {var_name} = {display_value}')
                    else:
                        self.stdout.write(f'  • {var_name}')
                self.stdout.write('')

            # Show missing variables
            if missing_vars:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Missing {len(missing_vars)} required variables:')
                )
                for var_name, default_value in missing_vars:
                    self.stdout.write(f'  • {var_name}')
                self.stdout.write('')

                # Add missing variables if flag is set
                if add_missing:
                    with open(env_file, 'a', encoding='utf-8') as f:
                        for var_name, default_value in missing_vars:
                            f.write(f'{var_name}={default_value}\n')
                    
                    self.stdout.write(
                        self.style.SUCCESS('✓ Added missing variables to .env file')
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            '\n⚠️  Please update the following variables with actual values:'
                        )
                    )
                    for var_name, _ in missing_vars:
                        self.stdout.write(f'  • {var_name}')
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            'Use --add-missing flag to add these variables to .env file'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS('✓ All required environment variables are present!')
                )

            # Check for extra variables in .env
            extra_vars = [key for key in existing_vars.keys() if key not in required_env_vars]
            if extra_vars:
                self.stdout.write('')
                self.stdout.write(
                    self.style.HTTP_INFO(f'ℹ️  Found {len(extra_vars)} additional variables:')
                )
                for var_name in extra_vars:
                    if show_values:
                        var_value = existing_vars[var_name]
                        if any(sensitive in var_name.lower() for sensitive in ['token', 'password', 'secret', 'key']):
                            display_value = var_value[:4] + '*' * (len(var_value) - 4) if len(var_value) > 4 else '****'
                        else:
                            display_value = var_value
                        self.stdout.write(f'  • {var_name} = {display_value}')
                    else:
                        self.stdout.write(f'  • {var_name}')

            self.stdout.write('\n' + '='*60 + '\n')

            # Show usage hints
            if not show_values:
                self.stdout.write(
                    self.style.HTTP_INFO('💡 Use --show-values to display variable values')
                )
            if not add_missing and missing_vars:
                self.stdout.write(
                    self.style.HTTP_INFO('💡 Use --add-missing to automatically add missing variables')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error checking .env file: {str(e)}')
            )
