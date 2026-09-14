from django.contrib import admin
from trading.models import PlatformControl


@admin.register(PlatformControl)
class PlatformControlAdmin(admin.ModelAdmin):
    list_display = (
        "trading_enabled",
        "withdrawals_enabled",
        "updated_at",
    )