from pathlib import Path

from django.contrib import admin
from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import path, include, re_path


def frontend_index(request, path=''):
    index_path = Path(settings.STATIC_ROOT) / 'index.html'
    if not index_path.is_file():
        raise Http404('The frontend has not been built.')
    return FileResponse(index_path.open('rb'), content_type='text/html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('core.urls')),
    re_path(r'^(?!api/|admin/|static/|media/).*$', frontend_index, name='frontend'),
]