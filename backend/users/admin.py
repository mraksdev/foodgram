from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin panel for the custom user model."""

    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('id',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin panel for subscriptions."""

    list_display = ('id', 'user', 'author')
    search_fields = ('user__email', 'author__email')
