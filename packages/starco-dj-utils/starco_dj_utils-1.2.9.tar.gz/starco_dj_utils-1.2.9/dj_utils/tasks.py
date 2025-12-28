from celery import shared_task
import zipfile
import os
from datetime import datetime
from django.core.management import call_command
from .handlers import notifire
@shared_task
def backup_database():
    path= '/app/backup.sql'
    call_command('backup',path= path)
    # Create ZIP archive
    zip_file = f"{path}.zip"
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(path, os.path.basename(path))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    try:
        with open(zip_file, 'rb') as backup:
            notifire.send(
                'backup_database',
                chat_id=os.getenv('BACKUP_DB_TELEGRAM_CHAT_ID'),  # Send to admin group
                file=backup,
                text=f"📂 Database Backup \n📅 {timestamp}\n💾 {os.path.getsize(zip_file) / (1024 * 1024):.2f} MB"
            )
    except Exception as e:
        print(e)
        notifire.send(sender='backup_database', text=f"❌ Error sending backup: {str(e)}")
    os.remove(zip_file)
    os.remove(path)

