from django.contrib import admin
from service.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'telegram_id', 'group_number',)
