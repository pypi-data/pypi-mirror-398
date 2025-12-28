import os
import subprocess
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Backup database to a file'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help='Path to save the backup file (optional)')
        parser.add_argument('--format', type=str, choices=['sql', 'dump', 'custom'], default='sql',
                            help='Backup format (sql, dump, or custom for PostgreSQL)')

    def handle(self, *args, **options):
        db_settings = settings.DATABASES['default']
        db_type = db_settings['ENGINE'].split('.')[-1]

        # Generate default backup path if not provided
        backup_path = options.get('path')
        if not backup_path:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            os.makedirs(backup_dir, exist_ok=True)

            if db_type == 'postgresql':
                ext = '.sql' if options['format'] == 'sql' else '.dump'
                backup_path = os.path.join(backup_dir, f'backup_pg_{timestamp}{ext}')
            elif db_type == 'sqlite3':
                backup_path = os.path.join(backup_dir, f'backup_sqlite_{timestamp}.sqlite3')
            elif db_type == 'mysql':
                backup_path = os.path.join(backup_dir, f'backup_mysql_{timestamp}.sql')
            else:
                raise CommandError(f'Unsupported database type: {db_type}')

        try:
            if db_type == 'postgresql':
                self._backup_postgresql(db_settings, backup_path, options['format'])
            elif db_type == 'sqlite3':
                self._backup_sqlite3(db_settings, backup_path)
            elif db_type == 'mysql':
                self._backup_mysql(db_settings, backup_path)
            else:
                raise CommandError(f'Unsupported database type: {db_type}')

            self.stdout.write(self.style.SUCCESS(f'Database backup created successfully at: {backup_path}'))
        except Exception as e:
            raise CommandError(f'Failed to backup database: {str(e)}')

    def _backup_postgresql(self, db_settings, backup_path, format_type):
        """Backup PostgreSQL database to a file"""
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']

        env = os.environ.copy()
        env['PGPASSWORD'] = db_password

        if format_type == 'sql':
            # Plain SQL dump
            command = [
                'pg_dump',
                f'-h{db_host}',
                f'-p{db_port}',
                f'-U{db_user}',
                '-d', db_name,
                '-f', backup_path
            ]
        else:
            # Custom format dump
            format_flag = '-Fc' if format_type == 'dump' else '-Fc'  # Default to custom format
            command = [
                'pg_dump',
                f'-h{db_host}',
                f'-p{db_port}',
                f'-U{db_user}',
                format_flag,
                '-d', db_name,
                '-f', backup_path
            ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise CommandError(f'pg_dump command failed: {stderr.decode()}')

    def _backup_sqlite3(self, db_settings, backup_path):
        """Backup SQLite database to a file"""
        db_path = db_settings['NAME']

        if not os.path.exists(db_path):
            raise CommandError(f'SQLite database file does not exist: {db_path}')

        # For SQLite, we can simply copy the database file
        import shutil
        shutil.copy2(db_path, backup_path)

        # Alternatively, we can use the .dump command for a SQL dump
        if backup_path.endswith('.sql'):
            command = [
                'sqlite3',
                db_path,
                '.dump'
            ]

            with open(backup_path, 'w') as f:
                process = subprocess.Popen(
                    command,
                    stdout=f,
                    stderr=subprocess.PIPE
                )
                _, stderr = process.communicate()

                if process.returncode != 0:
                    raise CommandError(f'sqlite3 dump command failed: {stderr.decode()}')

    def _backup_mysql(self, db_settings, backup_path):
        """Backup MySQL database to a file"""
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']

        command = [
            'mysqldump',
            f'-h{db_host}',
            f'-P{db_port}',
            f'-u{db_user}',
            f'-p{db_password}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            db_name
        ]

        with open(backup_path, 'w') as f:
            process = subprocess.Popen(
                command,
                stdout=f,
                stderr=subprocess.PIPE
            )
            _, stderr = process.communicate()

            if process.returncode != 0:
                raise CommandError(f'mysqldump command failed: {stderr.decode()}')
