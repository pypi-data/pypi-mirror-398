from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _


class AdvancedUserAdmin(UserAdmin):
    list_display = (
        "__str__",
        "email",
        "phone_number",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_verify",
        "is_ban",
        )
    list_editable = (
        "is_active",
        "is_staff",
        "is_superuser",
        "is_verify",
        "is_ban",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "is_verify",
        "is_ban",
        "date_joined",
        "last_login",
        "verify_date",
    )
    list_per_page = 50

    search_fields = (
        "username",
        "first_name",
        "last_name",
    )
    empty_value_display = _("empty")
    date_hierarchy = "date_joined"

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"),
        {
            "fields": (
                ("first_name","last_name"),
                "email",
                "phone_number",
                "about",
                "bio",
                "avatar"
                ),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_verify",
                    "is_ban",
                    "groups",
                    "user_permissions",
                    "following",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "ban_date", "verify_date")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "phone_number", "usable_password", "password1", "password2"),
            },
        ),
    )