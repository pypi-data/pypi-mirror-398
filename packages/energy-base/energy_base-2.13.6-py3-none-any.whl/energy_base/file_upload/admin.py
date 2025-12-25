from django.contrib import admin

from .models import ImportFile, TemporaryData


@admin.register(ImportFile)
class ImportFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'status', 'active', 'created_by']


@admin.register(TemporaryData)
class TemporaryDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'file', 'data']
