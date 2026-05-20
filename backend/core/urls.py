from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/drivers/', include('apps.drivers.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/announcements/', include('apps.announcements.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
