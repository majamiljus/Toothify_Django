# Maja Miljuš 0576/2022 
# Irina Majstorovic 0518/2022
from django.urls import path
from .views import *

app_name = 'index'

urlpatterns = [
    # Maja Miljuš 0576/2022 :
   path('', index, name='index'),
   path('about', about, name='about'),
   path('book_int', book_int, name='book_int'),
   path('get_available_times/', get_available_times, name='get_available_times'),
   path("save-rating", save_rating, name="save_rating"),
   # Irina Majstorovic 0518/2022:
   path('doctor', index_doctor, name='doctor_home'),

]