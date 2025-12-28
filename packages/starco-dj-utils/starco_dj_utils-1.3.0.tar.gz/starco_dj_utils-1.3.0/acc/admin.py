from django.contrib import admin
from .models import Acc
# Register your models here.
@admin.register(Acc)
class AccAdmin(admin.ModelAdmin):
    list_display = ('name',)