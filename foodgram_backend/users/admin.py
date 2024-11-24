from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


class WorkUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "first_name",
        "last_name",
        "email"
    )
    list_filter = (
        "email",
        "username"
    )


admin.site.register(User, WorkUserAdmin)
