
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse, HttpResponse, FileResponse
from django.core.management import call_command
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.conf import settings
import os
import zipfile
from datetime import datetime
import tempfile
from io import BytesIO

def is_superuser(user):
    """Check if user is superuser"""
    return user.is_superuser

@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def database_backup_view(request):
    """
    View for creating database backup
    Only accessible by superusers
    """
    if request.method == "POST":
        try:
            # Create temporary backup file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'backup_{timestamp}.sql'
            backup_path = os.path.join(tempfile.gettempdir(), backup_filename)
            
            # Call backup command
            call_command('backup', path=backup_path)
            
            # Create ZIP archive
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, os.path.basename(backup_path))
            
            # Clean up temporary file
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            # Prepare response
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="backup_{timestamp}.zip"'
            
            messages.success(request, f'✅ بک‌آپ با موفقیت ایجاد شد: {backup_filename}')
            return response
            
        except Exception as e:
            messages.error(request, f'❌ خطا در ایجاد بک‌آپ: {str(e)}')
            return redirect('database_management')
    
    return redirect('database_management')

@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
def database_restore_view(request):
    """
    View for restoring database from backup
    Only accessible by superusers
    """
    if request.method == "POST":
        backup_file = request.FILES.get('backup_file')
        
        if not backup_file:
            messages.error(request, '❌ لطفاً فایل بک‌آپ را انتخاب کنید')
            return redirect('database_management')
        
        try:
            # Save uploaded file temporarily
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_dir = tempfile.gettempdir()
            
            # Check if file is ZIP
            if backup_file.name.endswith('.zip'):
                zip_path = os.path.join(temp_dir, f'restore_{timestamp}.zip')
                with open(zip_path, 'wb+') as destination:
                    for chunk in backup_file.chunks():
                        destination.write(chunk)
                
                # Extract ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                    extracted_files = zip_ref.namelist()
                    
                    if not extracted_files:
                        raise Exception('فایل ZIP خالی است')
                    
                    backup_path = os.path.join(temp_dir, extracted_files[0])
                
                # Clean up ZIP file
                os.remove(zip_path)
            else:
                # Direct SQL or dump file
                backup_path = os.path.join(temp_dir, f'restore_{timestamp}{os.path.splitext(backup_file.name)[1]}')
                with open(backup_path, 'wb+') as destination:
                    for chunk in backup_file.chunks():
                        destination.write(chunk)
            
            # Validate file extension
            if not (backup_path.endswith('.sql') or backup_path.endswith('.dump')):
                os.remove(backup_path)
                raise Exception('فرمت فایل پشتیبانی نشده است. فقط .sql یا .dump مجاز است')
            
            # Call restore command
            call_command('restore', path=backup_path)
            
            # Clean up temporary file
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            messages.success(request, '✅ دیتابیس با موفقیت بازیابی شد')
            
        except Exception as e:
            messages.error(request, f'❌ خطا در بازیابی دیتابیس: {str(e)}')
            
            # Clean up on error
            if 'backup_path' in locals() and os.path.exists(backup_path):
                os.remove(backup_path)
    
    return redirect('database_management')

@user_passes_test(is_superuser)
def database_management_view(request):
    """
    Main view for database management
    Shows backup and restore options
    """
    context = {
        'title': 'مدیریت دیتابیس',
        'db_engine': settings.DATABASES['default']['ENGINE'],
        'db_name': settings.DATABASES['default']['NAME'],
    }
    
    return render(request, 'dj_utils/database_management.html', context)

@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def database_backup_ajax(request):
    """
    AJAX endpoint for database backup
    Returns JSON response
    """
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.sql'
        backup_path = os.path.join(tempfile.gettempdir(), backup_filename)
        
        call_command('backup', path=backup_path)
        
        file_size = os.path.getsize(backup_path) / (1024 * 1024)  # Size in MB
        
        # Clean up
        if os.path.exists(backup_path):
            os.remove(backup_path)
        
        return JsonResponse({
            'success': True,
            'message': f'بک‌آپ با موفقیت ایجاد شد',
            'filename': backup_filename,
            'size': f'{file_size:.2f} MB',
            'timestamp': timestamp
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'خطا در ایجاد بک‌آپ: {str(e)}'
        }, status=500)
