

# Maja Miljus 2022/0576


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',include('guest.urls')),
    path('index/',include('index.urls')),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('meds/', include('meds.urls')),
    path('patients/', include('patients.urls')),

  

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
