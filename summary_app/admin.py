from django.contrib import admin
from django.utils.html import format_html
from .models import Summary

@admin.register(Summary)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'property', 'summary' , 'create_date', 'update_date')
    list_display_links = ('id', 'property')
    search_fields = ['property', 'summary']

