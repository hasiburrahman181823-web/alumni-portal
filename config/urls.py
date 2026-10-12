from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from portal.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("api/", include("config.api_urls")),
    path("", home, name="home"),  # global name so templates/redirects can use {% url 'home' %}
    path("", include("portal.urls")),
]

# Serve user uploads from the dev server only. In production use nginx / object storage.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
