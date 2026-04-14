from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('otp-verify/', views.otp_verify_view, name='otp_verify'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),

    # User Management (Admin only)
    path('users/', views.user_list_view, name='user_list'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:user_id>/toggle/', views.user_toggle_active_view, name='user_toggle'),
    path('users/<int:user_id>/delete/', views.user_delete_view, name='user_delete'),
]
