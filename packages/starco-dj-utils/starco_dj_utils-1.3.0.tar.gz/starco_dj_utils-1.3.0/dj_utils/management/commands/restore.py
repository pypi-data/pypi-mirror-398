import os
import subprocess
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Restore database from a backup file'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, required=True, help='Path to the backup file')

    def handle(self, *args, **options):
        backup_path = options['path']

        if not os.path.exists(backup_path):
            raise CommandError(f'Backup file does not exist: {backup_path}')

        db_settings = settings.DATABASES['default']
        db_type = db_settings['ENGINE'].split('.')[-1]

        self.stdout.write(self.style.WARNING(f'Restoring database from {backup_path}'))
        self.stdout.write(self.style.WARNING('This will overwrite the current database. Are you sure? (y/n)'))

        # confirm = input()
        # if confirm.lower() != 'y':
        #     self.stdout.write(self.style.ERROR('Restore cancelled.'))
        #     return

        try:
            if db_type == 'postgresql':
                self._restore_postgresql(db_settings, backup_path)
            elif db_type == 'sqlite3':
                self._restore_sqlite3(db_settings, backup_path)
            elif db_type == 'mysql':
                self._restore_mysql(db_settings, backup_path)
            else:
                raise CommandError(f'Unsupported database type: {db_type}')

            self.stdout.write(self.style.SUCCESS('Database restored successfully!'))
        except Exception as e:
            raise CommandError(f'Failed to restore database: {str(e)}')

    def _restore_postgresql(self, db_settings, backup_path):
        """Restore PostgreSQL database from backup file"""
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']

        # Check file extension to determine restore method
        if backup_path.endswith('.sql'):
            # SQL dump file
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password

            command = [
                'psql',
                f'-h{db_host}',
                f'-p{db_port}',
                f'-U{db_user}',
                f'-d{db_name}',
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
                raise CommandError(f'psql command failed: {stderr.decode()}')

        elif backup_path.endswith('.dump'):
            # pg_dump custom format
            env = os.environ.copy()
            env['PGPASSWORD'] = db_password

            command = [
                'pg_restore',
                '--clean',
                '--if-exists',
                f'-h{db_host}',
                f'-p{db_port}',
                f'-U{db_user}',
                f'-d{db_name}',
                backup_path
            ]

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise CommandError(f'pg_restore command failed: {stderr.decode()}')
        else:
            raise CommandError(f'Unsupported file format for PostgreSQL: {backup_path}')

    def _restore_sqlite3(self, db_settings, backup_path):
        """Restore SQLite database from backup file"""
        db_path = db_settings['NAME']

        if os.path.exists(db_path):
            # Create a backup of the current database
            backup_name = f"{db_path}.bak"
            os.rename(db_path, backup_name)
            self.stdout.write(self.style.WARNING(f'Current database backed up to {backup_name}'))

        # For SQLite, we can simply copy the backup file to the database location
        if backup_path.endswith('.sql'):
            # SQL dump file - need to execute the SQL commands
            try:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                with open(backup_path, 'r') as f:
                    sql_script = f.read()
                    cursor.executescript(sql_script)

                conn.commit()
                conn.close()
            except Exception as e:
                raise CommandError(f'Failed to restore SQLite database: {str(e)}')
        else:
            # Binary backup - just copy the file
            import shutil
            shutil.copy2(backup_path, db_path)

    def _restore_mysql(self, db_settings, backup_path):
        """Restore MySQL database from backup file"""
        db_name = db_settings['NAME']
        db_user = db_settings['USER']
        db_password = db_settings['PASSWORD']
        db_host = db_settings['HOST']
        db_port = db_settings['PORT']

        command = [
            'mysql',
            f'-h{db_host}',
            f'-P{db_port}',
            f'-u{db_user}',
            f'-p{db_password}',
            db_name,
            '<', backup_path
        ]

        # For MySQL, we need to use shell=True to handle the redirect operator
        command_str = ' '.join(command)
        process = subprocess.Popen(
            command_str,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise CommandError(f'mysql command failed: {stderr.decode()}')
