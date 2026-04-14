from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('ping/', lambda r: HttpResponse('ok', content_type='text/plain')),
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('dashboard/', include('dashboard.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
