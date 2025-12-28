from core.celery_config import app
import os
app.conf.beat_schedule = {
    'run-backup-task': {
        'task': 'utils.tasks.backup_database',
        'schedule': int(os.getenv('BACKUP_EVERY_SECOND')),  # seconds
    },

}