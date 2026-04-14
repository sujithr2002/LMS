from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser
import random

ROLE_CHOICES = [
    ('student', 'Student', '🧑‍🎓'),
    ('teacher', 'Teacher', '👨‍🏫'),
    ('admin',   'Admin',   '🛡️'),
]

def register_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role', 'student')
        admin_code = request.POST.get('admin_code', '').strip()

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('register')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        # Validate admin secret code
        if role == 'admin':
            if admin_code != getattr(settings, 'ADMIN_REGISTRATION_CODE', ''):
                messages.error(request, 'Invalid admin registration code.')
                return redirect('register')

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email_token=otp,
            is_active=False,
        )

        # Set role flags
        if role == 'teacher':
            user.is_teacher = True
        elif role == 'admin':
            user.is_admin = True
            user.is_staff = True
        user.save()

        try:
            send_mail(
                'Verify your email - LMS',
                f'Hello {first_name or email},\n\nYour OTP for LMS registration is: {otp}\n\nThis OTP is valid for your current session.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, f'OTP sent to {email}. Please verify your account.')
            request.session['registration_email'] = email
            return redirect('otp_verify')
        except Exception as e:
            user.delete()
            messages.error(request, 'Failed to send OTP email. Please try again.')
            return redirect('register')

    return render(request, 'accounts/register.html')

def otp_verify_view(request):
    email = request.session.get('registration_email')
    if not email:
        return redirect('register')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        try:
            user = CustomUser.objects.get(email=email)
            if user.email_token == otp:
                user.is_active = True
                user.email_token = None
                user.save()
                messages.success(request, 'Account verified successfully. You can now login.')
                del request.session['registration_email']
                return redirect('login')
            else:
                messages.error(request, 'Invalid OTP.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')

    return render(request, 'accounts/otp_verify.html', {'email': email})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user_obj = CustomUser.objects.get(email=email)
            if not user_obj.is_active:
                messages.error(request, 'Your account is not verified. Please contact admin.')
                return redirect('login')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid credentials.')
            return redirect('login')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.email}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials.')

    return render(request, 'accounts/login.html')

def logout_view(request):
    auth_logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        email = request.POST.get('email')
        
        # Check if email is changing and not already taken
        if email != user.email:
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'This email is already in use.')
                return redirect('profile')
        
        user.email = email
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    return render(request, 'accounts/profile.html')

@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user
        if not user.check_password(old_password):
            messages.error(request, 'Incorrect current password.')
            return redirect('change_password')

        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)  # Keep user logged in
        messages.success(request, 'Password changed successfully.')
        return redirect('profile')

    return render(request, 'accounts/change_password.html')


@login_required
def dashboard_view(request):
    from courses.models import Course, Enrollment, Assignment, AssignmentSubmission
    user = request.user
    context = {'user': user}

    if user.is_admin:
        from courses.models import EnrollmentRequest
        context.update({
            'role': 'admin',
            'total_users': CustomUser.objects.filter(is_active=True).count(),
            'total_students': CustomUser.objects.filter(is_active=True, is_admin=False, is_teacher=False).count(),
            'total_teachers': CustomUser.objects.filter(is_teacher=True, is_active=True).count(),
            'total_courses': Course.objects.count(),
            'total_enrollments': Enrollment.objects.count(),
            'total_assignments': Assignment.objects.count(),
            'total_submissions': AssignmentSubmission.objects.count(),
            'recent_users': CustomUser.objects.filter(is_active=True).order_by('-created_date')[:6],
            'courses': Course.objects.prefetch_related('enrollments', 'assignments').all()[:8],
            'pending_grades': AssignmentSubmission.objects.filter(marks__isnull=True).count(),
            'pending_enrollments': EnrollmentRequest.objects.filter(status='pending').count(),
            'latest_requests': EnrollmentRequest.objects.filter(status='pending').select_related('student', 'course').order_by('-created_date')[:6],
        })

    elif user.is_teacher:
        teaching_courses = Course.objects.filter(teacher=user).prefetch_related('enrollments', 'assignments')
        pending_submissions = AssignmentSubmission.objects.filter(
            assignment__course__teacher=user, marks__isnull=True
        ).count()
        total_students = Enrollment.objects.filter(
            course__teacher=user
        ).values('student').distinct().count()
        recent_submissions = AssignmentSubmission.objects.filter(
            assignment__course__teacher=user
        ).select_related('student', 'assignment').order_by('-submitted_at')[:5]
        context.update({
            'role': 'teacher',
            'teaching_courses': teaching_courses,
            'total_students': total_students,
            'pending_submissions': pending_submissions,
            'total_assignments': Assignment.objects.filter(course__teacher=user).count(),
            'recent_submissions': recent_submissions,
        })

    else:  # student
        enrollments = Enrollment.objects.filter(student=user).select_related('course__teacher')
        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        pending_assignments = Assignment.objects.filter(
            course_id__in=enrolled_course_ids
        ).exclude(submissions__student=user).count()
        my_submissions = AssignmentSubmission.objects.filter(
            student=user
        ).select_related('assignment__course').order_by('-submitted_at')
        graded_count = my_submissions.exclude(marks__isnull=True).count()
        context.update({
            'role': 'student',
            'enrollments': enrollments,
            'total_enrolled': enrollments.count(),
            'pending_assignments': pending_assignments,
            'submitted_count': my_submissions.count(),
            'graded_count': graded_count,
            'my_submissions': my_submissions[:5],
        })

    return render(request, 'accounts/dashboard.html', context)


# ─── User Management (Admin only) ────────────────────────────────────────────

def admin_required(view_func):
    """Decorator: only active admins can access."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            messages.error(request, 'Access denied. Admins only.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def user_list_view(request):
    role_filter = request.GET.get('role', 'all')
    search = request.GET.get('q', '').strip()

    users = CustomUser.objects.all().order_by('-created_date')

    if role_filter == 'student':
        users = users.filter(is_admin=False, is_teacher=False)
    elif role_filter == 'teacher':
        users = users.filter(is_teacher=True)
    elif role_filter == 'admin':
        users = users.filter(is_admin=True)

    if search:
        users = users.filter(
            email__icontains=search
        ) | CustomUser.objects.filter(
            first_name__icontains=search
        ) | CustomUser.objects.filter(
            last_name__icontains=search
        )
        users = users.distinct().order_by('-created_date')

    counts = {
        'all': CustomUser.objects.count(),
        'student': CustomUser.objects.filter(is_admin=False, is_teacher=False).count(),
        'teacher': CustomUser.objects.filter(is_teacher=True).count(),
        'admin': CustomUser.objects.filter(is_admin=True).count(),
    }

    return render(request, 'accounts/user_list.html', {
        'users': users,
        'role_filter': role_filter,
        'search': search,
        'counts': counts,
    })


@login_required
@admin_required
def user_create_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role', 'student')
        password = request.POST.get('password', '').strip()

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return render(request, 'accounts/user_form.html', {'action': 'Create', 'current_role': 'student', 'role_choices': ROLE_CHOICES})

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'accounts/user_form.html', {'action': 'Create', 'current_role': 'student', 'role_choices': ROLE_CHOICES})

        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_active=True,  # Admin-created users are active by default
        )
        if role == 'teacher':
            user.is_teacher = True
        elif role == 'admin':
            user.is_admin = True
            user.is_staff = True
        user.save()

        messages.success(request, f'User "{email}" created successfully as {role}.')
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {'action': 'Create', 'current_role': 'student', 'role_choices': ROLE_CHOICES})


@login_required
@admin_required
def user_edit_view(request, user_id):
    target_user = CustomUser.objects.get(id=user_id)

    # Determine current role
    if target_user.is_admin:
        current_role = 'admin'
    elif target_user.is_teacher:
        current_role = 'teacher'
    else:
        current_role = 'student'

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        role = request.POST.get('role', 'student')
        new_password = request.POST.get('password', '').strip()

        # Check email uniqueness
        if email != target_user.email and CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'This email is already in use.')
            return render(request, 'accounts/user_form.html', {
                'action': 'Edit', 'target_user': target_user, 'current_role': current_role, 'role_choices': ROLE_CHOICES,
            })

        target_user.email = email
        target_user.first_name = first_name
        target_user.last_name = last_name
        target_user.phone = phone

        # Reset roles then apply new one
        target_user.is_admin = False
        target_user.is_staff = False
        target_user.is_teacher = False
        if role == 'teacher':
            target_user.is_teacher = True
        elif role == 'admin':
            target_user.is_admin = True
            target_user.is_staff = True

        if new_password:
            target_user.set_password(new_password)

        target_user.save()
        messages.success(request, f'User "{email}" updated successfully.')
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {
        'action': 'Edit',
        'target_user': target_user,
        'current_role': current_role,
        'role_choices': ROLE_CHOICES,
    })


@login_required
@admin_required
def user_toggle_active_view(request, user_id):
    target_user = CustomUser.objects.get(id=user_id)
    if target_user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('user_list')
    target_user.is_active = not target_user.is_active
    target_user.save()
    status = 'activated' if target_user.is_active else 'deactivated'
    messages.success(request, f'User "{target_user.email}" has been {status}.')
    return redirect('user_list')


@login_required
@admin_required
def user_delete_view(request, user_id):
    target_user = CustomUser.objects.get(id=user_id)
    if target_user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_list')
    if request.method == 'POST':
        email = target_user.email
        target_user.delete()
        messages.success(request, f'User "{email}" deleted permanently.')
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'target_user': target_user})
