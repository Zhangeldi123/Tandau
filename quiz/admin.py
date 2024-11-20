from django.contrib import admin
from .models import *

@admin.register(Question_Category)
class Question_CategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name','description','created_at']
    readonly_fields =['created_at']
    list_editable = ['name','description']

@admin.register(Questions)
class QuestionsAdmin(admin.ModelAdmin):
    list_display = ['id','text','difficulty','is_active','category','created_at']
    readonly_fields = ['created_at']
    list_editable = ['text','difficulty','is_active','category']

@admin.register(Choices)
class ChoicesAdmin(admin.ModelAdmin):
    list_display = ['id','solution','is_correct','question','created_at']
    readonly_fields = ['created_at']
    list_editable = ['solution','is_correct','question']