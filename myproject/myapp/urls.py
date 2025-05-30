from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='login'), # done
    path('logout/', views.custom_logout, name='logout'), # done
    path('register/', views.register_view, name='register'), #done
    # path('profile/', views.profile_view, name='profile'),
    # path('profile/', views.donor_profile_view, name='donor_profile'),
    path('profile/', views.profile_redirect_view, name='profile'), 
    path('donor/profile/', views.donor_profile_view, name='donor_profile'), #done
    path('administrator/profile/', views.admin_profile_view, name='admin_profile'),
    path('registration-success/', views.registration_success_view, name='registration_success'), #done
    path('recipient/profile/', views.recipient_profile_view, name='recipient_profile'), #done
    path('recipient/edit/', views.edit_recipient_profile, name='edit_recipient_profile'), #done
    path('profile/edit/', views.edit_donor_profile, name='edit_donor_profile'),
    # path('request/', views.fill_request_form, name='fill_request_form'),
    path('request-blood/<int:pk>/accept/', views.accept_blood_request, name='accept_blood_request'),
    path('request-blood/', views.create_blood_request_user, name='blood-request'),
    path('requests/', views.admin_blood_request_list, name='admin-request-list'),
    path('request-blood/<int:pk>/edit/', views.edit_blood_request_admin, name='admin-request-edit'),
    path('request-blood/<int:pk>/delete/', views.delete_blood_request_admin, name='admin-request-delete'),
    path('edit-request/<int:request_id>/', views.edit_blood_request, name='edit_blood_request'),
    path('request-success/', views.request_success, name='request_success'),
    path('blood-requests/', views.view_blood_requests, name='blood_requests'),
    path('notifications/', views.notification_view, name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('notifications/mark-unread/<int:notification_id>/', views.mark_as_unread, name='mark_as_unread'),
    path('donor/<int:donor_id>/', views.donor_profile, name='requested_donor_profile'),
]
