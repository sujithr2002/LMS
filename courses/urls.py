from django.urls import path
from . import views

urlpatterns = [
    # Course URLs
    path('', views.course_list, name='course_list'),
    path('create/', views.course_create, name='course_create'),
    path('<uuid:uuid>/', views.course_detail, name='course_detail'),
    path('<uuid:uuid>/edit/', views.course_update, name='course_update'),
    path('<uuid:uuid>/delete/', views.course_delete, name='course_delete'),

    # Module URLs
    path('<uuid:course_uuid>/module/create/', views.module_create, name='module_create'),
    path('module/<uuid:uuid>/edit/', views.module_update, name='module_update'),
    path('module/<uuid:uuid>/delete/', views.module_delete, name='module_delete'),

    # Content URLs
    path('module/<uuid:module_uuid>/content/add/', views.content_create, name='content_create'),
    path('content/<uuid:uuid>/delete/', views.content_delete, name='content_delete'),

    # Enrollment URLs
    path('<uuid:uuid>/enroll/', views.enroll_course, name='enroll_course'),
    path('<uuid:uuid>/unenroll/', views.unenroll_course, name='unenroll_course'),
    path('my-courses/', views.my_enrollments, name='my_enrollments'),
    path('<uuid:uuid>/students/', views.course_students, name='course_students'),

    # Enrollment Request URLs (Admin)
    path('enrollment-requests/', views.enrollment_requests, name='enrollment_requests'),
    path('enrollment-requests/<int:req_id>/approve/', views.approve_enrollment, name='approve_enrollment'),
    path('enrollment-requests/<int:req_id>/reject/', views.reject_enrollment, name='reject_enrollment'),

    # Assignment URLs
    path('<uuid:course_uuid>/assignment/create/', views.assignment_create, name='assignment_create'),
    path('assignment/<uuid:uuid>/delete/', views.assignment_delete, name='assignment_delete'),
    path('assignment/<uuid:uuid>/submit/', views.assignment_submit, name='assignment_submit'),
    path('assignment/<uuid:uuid>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('submission/<uuid:uuid>/grade/', views.grade_submission, name='grade_submission'),
]
