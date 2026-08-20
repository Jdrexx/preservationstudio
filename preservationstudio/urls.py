"""URL configuration for preservation.studio."""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

handler404 = "studio.views.custom_404"
handler500 = "studio.views.custom_500"

urlpatterns = [
    path("", include("studio.urls")),
]

if settings.ADMIN_URL:
    from django.contrib import admin

    urlpatterns.insert(0, path(f"{settings.ADMIN_URL}/", admin.site.urls))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
