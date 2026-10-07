#Irina Majstorovic 0518/2022
#Aleksandar Pavlovic 0093/2022
from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import views

app_name = 'users'

urlpatterns = [
    #Aleksandar Pavlovic 0093/2022:
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='passwordResetForm.html',
        email_template_name='passwordResetEmail.txt',
        subject_template_name='passwordResetSubject.txt',
        success_url=reverse_lazy('users:password_reset_done')
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='passwordResetDone.html'
    ), name='password_reset_done'),
    re_path(
        r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='passwordResetConfirm.html',
            success_url=reverse_lazy('users:password_reset_complete')
        ),
        name='password_reset_confirm'
    ),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='passwordResetComplete.html'
    ), name='password_reset_complete'),

    path('deactivate/', views.deactivate_account, name='deactivate'),
    path('logout/', views.user_logout, name='logout'),
    path('admin-panel/spec-request/<int:req_id>/approve/', views.approve_spec_request, name='approve_spec_request'),
    path('admin-panel/spec-request/<int:req_id>/reject/', views.reject_spec_request, name='reject_spec_request'),


    #Irina Majstorovic 0518/2022:
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/doktor/novi/', views.create_doctor, name='create_doctor'),
    path('admin-panel/vacation/<int:vac_id>/approve/', views.approve_vacation, name='approve_vacation'),
    path('admin-panel/vacation/<int:vac_id>/reject/', views.reject_vacation, name='reject_vacation'),
    path('admin-panel/doktor/<int:med_id>/deaktiviraj/', views.deactivate_doctor, name='deactivate_doctor'),
    path('admin-panel/notifications/add/', views.add_notification, name='add_notification'),
    path('admin-panel/notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
    path("admin-panel/interventions/add/", views.add_intervention, name="add_intervention"),
    path("admin-panel/interventions/<int:intervention_id>/delete/", views.delete_intervention, name="delete_intervention"),
    path("admin-panel/worktime/", views.admin_worktime, name="admin_worktime"),
    path("admin-panel/worktime/plan/", views.worktime_plan, name="worktime_plan"),






]
