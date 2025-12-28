
from django.urls import path
from . import views

urlpatterns = [
    # Database Management URLs
    path('database/', views.database_management_view, name='database_management'),
    path('database/backup/', views.database_backup_view, name='database_backup'),
    path('database/restore/', views.database_restore_view, name='database_restore'),
    path('database/backup/ajax/', views.database_backup_ajax, name='database_backup_ajax'),
]

