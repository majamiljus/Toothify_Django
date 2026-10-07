from django.urls import path
from .views import *

app_name = 'guest'

urlpatterns = [
   path('', guest, name='guest'),
]