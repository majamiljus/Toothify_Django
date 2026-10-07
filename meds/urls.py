#Minja Krivokapic 0615/2022 
#Irina Majstorovič 2022/0518
from django.urls import path
from . import views


app_name = 'meds'

urlpatterns = [
    path('vacation/', views.vacation, name='vacation'),
    path('myVacations/', views.myVacations, name='myVacations'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.editProfile, name='editProfile'),
    path('deleteVacation/<int:idVacation>/', views.deleteVacation, name='deleteVacation'),
    path('myInterventions/', views.myInterventions, name='myInterventionsMeds'),
    path('addIntervention/', views.addIntervention, name='addIntervention'),
    path('addIntervention/karton/<int:idPat>/', views.karton, name='karton'),
    path('addIntervention/karton/<int:idPat>/edit/', views.editKarton, name='editKarton'),
    path('deleteIntervention/<int:idInter>/', views.deleteIntervention, name='deleteIntervention'),
    path('confirmIntervention/<int:idInter>/', views.confirmIntervention, name='confirmIntervention'),
    path('cancel/<int:id>/', views.cancelIntervention, name='cancelIntervention'),
    path('indexDoctor/', views.indexDoctor, name='indexDoctor'),
    path('notifications/', views.notificationsMeds, name='notificationsMeds'),
    path('notifications/add/', views.addNotificationMeds, name='addNotificationMeds'),
    path('specialization/request/', views.request_specialization_upgrade, name='request_specialization_upgrade'),
    path("worktime/2weeks/", views.myWorkTimeTwoWeeks, name="myWorkTimeTwoWeeks"),
    path("worktime/2weeks/set/", views.setWorkTimeTwoWeeks, name="setWorkTimeTwoWeeks"),

]

