#Irina Majstorović 2022/0518
#Minja Krivokapić 2022/0615
#Maja Miljuš 2022/0576
from django.urls import path
from .views import *
app_name = 'patients'

urlpatterns = [
    path('med/<int:idMed>/', med, name='med'), 
    path('get_available_times/', get_available_times, name='get_available_times'),
    path('myInterventions', myInterventions, name='myInterventions'),    
    path('cancel/<int:id>/', cancel_intervention, name='cancel_intervention'),
    path('deleteIntervention/<int:idInt>/', deleteIntervention, name='deleteIntervention'), 
    path('profile', profile, name='profile'), 
    path('profile/edit', editProfile, name='editProfile'), 
    path('profile/karton/', karton, name='karton'),  

]
