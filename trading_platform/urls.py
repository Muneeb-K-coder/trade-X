from django.contrib import admin
from django.urls import path, include

from trading.admin_views import admin_dashboard


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "admin-dashboard/",
        admin_dashboard,
        name="admin_dashboard"
    ),

    path("", include("accounts.urls")),

    path(
        "trading/",
        include("trading.urls")
    ),
]