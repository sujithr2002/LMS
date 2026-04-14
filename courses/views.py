from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, CourseModule, CourseContent, Enrollment, EnrollmentRequest, Assignment, AssignmentSubmission


# ─── Permission helpers ──────────────────────────────────────────────────────

def is_admin(user):
    return user.is_authenticated and user.is_admin

def is_admin_or_teacher(user):
    return user.is_authenticated and (user.is_admin or user.is_teacher)

def is_course_teacher(user, course):
    """True if user is the assigned teacher of this course OR is admin."""
    return user.is_admin or (user.is_teacher and course.teacher == user)


# ─── Course Views ─────────────────────────────────────────────────────────────

@login_required
def course_list(request):
    courses = Course.objects.all()
    enrolled_ids = set()
    request_states = {}   # course_id -> 'pending' | 'rejected'
    if request.user.is_authenticated and not is_admin_or_teacher(request.user):
        enrolled_ids = set(
            Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
        )
        for er in EnrollmentRequest.objects.filter(student=request.user).exclude(status='approved'):
            request_states[er.course_id] = er.status
    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'enrolled_ids': enrolled_ids,
        'request_states': request_states,
    })


@login_required
def course_detail(request, uuid):
    course = get_object_or_404(Course, uuid=uuid)
    modules = course.modules.prefetch_related('contents').all()
    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    assignments = course.assignments.all() if is_enrolled or is_course_teacher(request.user, course) else []
    # For each assignment, check if student has submitted
    submitted_ids = set()
    if not is_admin_or_teacher(request.user):
        submitted_ids = set(
            AssignmentSubmission.objects.filter(
                student=request.user, assignment__course=course
            ).values_list('assignment_id', flat=True)
        )
    enrollment_request = EnrollmentRequest.objects.filter(student=request.user, course=course).first()
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'modules': modules,
        'is_enrolled': is_enrolled,
        'enrollment_request': enrollment_request,
        'assignments': assignments,
        'submitted_ids': submitted_ids,
        'is_course_teacher': is_course_teacher(request.user, course),
    })


@login_required
def course_create(request):
    if not is_admin(request.user):
        messages.error(request, 'Only administrators can create courses.')
        return redirect('course_list')

    if request.method == 'POST':
        name = request.POST.get('course_name', '').strip()
        desc = request.POST.get('description', '').strip()
        thumbnail = request.FILES.get('thumbnail')
        teacher_id = request.POST.get('teacher') or None

        if not name:
            messages.error(request, 'Course name is required.')
            return render(request, 'courses/course_form.html', {'action': 'Create'})

        course = Course.objects.create(
            course_name=name,
            description=desc,
            thumbnail=thumbnail,
            teacher_id=teacher_id,
        )
        messages.success(request, f'Course "{course.course_name}" created successfully.')
        return redirect('course_detail', uuid=course.uuid)

    from accounts.models import CustomUser
    teachers = CustomUser.objects.filter(is_teacher=True, is_active=True)
    return render(request, 'courses/course_form.html', {'action': 'Create', 'teachers': teachers})


@login_required
def course_update(request, uuid):
    if not is_admin(request.user):
        messages.error(request, 'Only administrators can edit courses.')
        return redirect('course_list')

    course = get_object_or_404(Course, uuid=uuid)

    if request.method == 'POST':
        course.course_name = request.POST.get('course_name', course.course_name).strip()
        course.description = request.POST.get('description', course.description).strip()
        teacher_id = request.POST.get('teacher') or None
        course.teacher_id = teacher_id
        if request.FILES.get('thumbnail'):
            course.thumbnail = request.FILES['thumbnail']
        course.save()
        messages.success(request, 'Course updated successfully.')
        return redirect('course_detail', uuid=course.uuid)

    from accounts.models import CustomUser
    teachers = CustomUser.objects.filter(is_teacher=True, is_active=True)
    return render(request, 'courses/course_form.html', {'action': 'Update', 'course': course, 'teachers': teachers})


@login_required
def course_delete(request, uuid):
    if not is_admin(request.user):
        messages.error(request, 'Only administrators can delete courses.')
        return redirect('course_list')

    course = get_object_or_404(Course, uuid=uuid)

    if request.method == 'POST':
        name = course.course_name
        course.delete()
        messages.success(request, f'Course "{name}" deleted successfully.')
        return redirect('course_list')

    return render(request, 'courses/course_confirm_delete.html', {'object': course, 'type': 'Course'})


# ─── CourseModule Views ───────────────────────────────────────────────────────

@login_required
def module_create(request, course_uuid):
    if not is_admin_or_teacher(request.user):
        messages.error(request, 'Only administrators or teachers can create modules.')
        return redirect('course_detail', uuid=course_uuid)

    course = get_object_or_404(Course, uuid=course_uuid)

    if request.method == 'POST':
        name = request.POST.get('module_name', '').strip()
        desc = request.POST.get('module_description', '').strip()
        order = request.POST.get('order', 0)

        if not name:
            messages.error(request, 'Module name is required.')
            return render(request, 'courses/module_form.html', {'action': 'Create', 'course': course})

        CourseModule.objects.create(
            course=course,
            module_name=name,
            module_description=desc,
            order=order,
        )
        messages.success(request, f'Module "{name}" created successfully.')
        return redirect('course_detail', uuid=course_uuid)

    return render(request, 'courses/module_form.html', {'action': 'Create', 'course': course})


@login_required
def module_update(request, uuid):
    if not is_admin_or_teacher(request.user):
        messages.error(request, 'Only administrators or teachers can edit modules.')
        return redirect('course_list')

    module = get_object_or_404(CourseModule, uuid=uuid)

    if request.method == 'POST':
        module.module_name = request.POST.get('module_name', module.module_name).strip()
        module.module_description = request.POST.get('module_description', module.module_description).strip()
        module.order = request.POST.get('order', module.order)
        module.save()
        messages.success(request, 'Module updated successfully.')
        return redirect('course_detail', uuid=module.course.uuid)

    return render(request, 'courses/module_form.html', {'action': 'Update', 'course': module.course, 'module': module})


@login_required
def module_delete(request, uuid):
    if not is_admin_or_teacher(request.user):
        messages.error(request, 'Only administrators or teachers can delete modules.')
        return redirect('course_list')

    module = get_object_or_404(CourseModule, uuid=uuid)
    course_uuid = module.course.uuid

    if request.method == 'POST':
        name = module.module_name
        module.delete()
        messages.success(request, f'Module "{name}" deleted successfully.')
        return redirect('course_detail', uuid=course_uuid)

    return render(request, 'courses/course_confirm_delete.html', {'object': module, 'type': 'Module'})


# ─── CourseContent Views ──────────────────────────────────────────────────────

@login_required
def content_create(request, module_uuid):
    if not is_admin_or_teacher(request.user):
        messages.error(request, 'Only administrators or teachers can add content.')
        return redirect('course_list')

    module = get_object_or_404(CourseModule, uuid=module_uuid)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content_type = request.POST.get('content_type', '')
        content_file = request.FILES.get('content_file')
        order = request.POST.get('order', 0)

        if not title or not content_type or not content_file:
            messages.error(request, 'Title, content type, and file are all required.')
            return render(request, 'courses/content_form.html', {'module': module, 'action': 'Add'})

        CourseContent.objects.create(
            module=module,
            title=title,
            content_type=content_type,
            content_file=content_file,
            order=order,
        )
        messages.success(request, f'Content "{title}" added successfully.')
        return redirect('course_detail', uuid=module.course.uuid)

    return render(request, 'courses/content_form.html', {'module': module, 'action': 'Add'})


@login_required
def content_delete(request, uuid):
    if not is_admin_or_teacher(request.user):
        messages.error(request, 'Only administrators or teachers can delete content.')
        return redirect('course_list')

    content = get_object_or_404(CourseContent, uuid=uuid)
    course_uuid = content.module.course.uuid

    if request.method == 'POST':
        title = content.title
        content.delete()
        messages.success(request, f'Content "{title}" deleted successfully.')
        return redirect('course_detail', uuid=course_uuid)

    return render(request, 'courses/course_confirm_delete.html', {'object': content, 'type': 'Content'})


# ─── Enrollment Request Views (Student) ──────────────────────────────────────

@login_required
def enroll_course(request, uuid):
    """Student submits an enrollment request (not directly enrolled)."""
    course = get_object_or_404(Course, uuid=uuid)

    if is_admin_or_teacher(request.user):
        messages.info(request, 'Admins and teachers do not need to enroll.')
        return redirect('course_detail', uuid=uuid)

    # Already enrolled?
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('course_detail', uuid=uuid)

    # Already requested?
    existing_req = EnrollmentRequest.objects.filter(student=request.user, course=course).first()
    if existing_req:
        if existing_req.status == 'pending':
            messages.info(request, 'Your enrollment request is already pending admin approval.')
        elif existing_req.status == 'rejected':
            messages.error(request, f'Your request was rejected. {existing_req.note or ""}')
        return redirect('course_detail', uuid=uuid)

    EnrollmentRequest.objects.create(student=request.user, course=course)
    messages.success(request, f'Enrollment request sent for "{course.course_name}". Awaiting admin approval.')
    return redirect('course_detail', uuid=uuid)


@login_required
def unenroll_course(request, uuid):
    course = get_object_or_404(Course, uuid=uuid)
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    if enrollment:
        if request.method == 'POST':
            enrollment.delete()
            # Also clear any old request so student can re-request
            EnrollmentRequest.objects.filter(student=request.user, course=course).delete()
            messages.success(request, f'You have unenrolled from "{course.course_name}".')
            return redirect('course_list')
        return render(request, 'courses/course_confirm_delete.html', {
            'object': f'your enrollment in "{course.course_name}"',
            'type': 'Enrollment',
        })
    messages.error(request, 'You are not enrolled in this course.')
    return redirect('course_detail', uuid=uuid)


@login_required
def my_enrollments(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    pending_requests = EnrollmentRequest.objects.filter(
        student=request.user, status='pending'
    ).select_related('course')
    rejected_requests = EnrollmentRequest.objects.filter(
        student=request.user, status='rejected'
    ).select_related('course')
    return render(request, 'courses/my_enrollments.html', {
        'enrollments': enrollments,
        'pending_requests': pending_requests,
        'rejected_requests': rejected_requests,
    })


@login_required
def course_students(request, uuid):
    course = get_object_or_404(Course, uuid=uuid)
    if not is_course_teacher(request.user, course):
        messages.error(request, 'You are not authorised to view this course\'s students.')
        return redirect('course_detail', uuid=uuid)
    enrollments = Enrollment.objects.filter(course=course).select_related('student')
    return render(request, 'courses/course_students.html', {'course': course, 'enrollments': enrollments})


# ─── Enrollment Request Management (Admin only) ───────────────────────────────

@login_required
def enrollment_requests(request):
    """Admin views all pending enrollment requests."""
    if not is_admin(request.user):
        messages.error(request, 'Only admins can manage enrollment requests.')
        return redirect('dashboard')

    status_filter = request.GET.get('status', 'pending')
    reqs = EnrollmentRequest.objects.select_related('student', 'course').filter(status=status_filter)
    counts = {
        'pending':  EnrollmentRequest.objects.filter(status='pending').count(),
        'approved': EnrollmentRequest.objects.filter(status='approved').count(),
        'rejected': EnrollmentRequest.objects.filter(status='rejected').count(),
    }
    return render(request, 'courses/enrollment_requests.html', {
        'requests': reqs,
        'status_filter': status_filter,
        'counts': counts,
    })


@login_required
def approve_enrollment(request, req_id):
    """Admin approves a request → creates Enrollment record."""
    if not is_admin(request.user):
        messages.error(request, 'Not authorised.')
        return redirect('dashboard')

    req = get_object_or_404(EnrollmentRequest, id=req_id)
    if req.status != 'pending':
        messages.info(request, 'This request has already been processed.')
        return redirect('enrollment_requests')

    # Create the actual enrollment
    Enrollment.objects.get_or_create(student=req.student, course=req.course)
    req.status = 'approved'
    req.save()
    messages.success(request, f'Approved enrollment: {req.student.email} → {req.course.course_name}')
    return redirect('enrollment_requests')


@login_required
def reject_enrollment(request, req_id):
    """Admin rejects a request with an optional note."""
    if not is_admin(request.user):
        messages.error(request, 'Not authorised.')
        return redirect('dashboard')

    req = get_object_or_404(EnrollmentRequest, id=req_id)
    if request.method == 'POST':
        note = request.POST.get('note', '').strip()
        req.status = 'rejected'
        req.note = note
        req.save()
        messages.success(request, f'Rejected enrollment: {req.student.email} → {req.course.course_name}')
        return redirect('enrollment_requests')

    return render(request, 'courses/reject_enrollment.html', {'req': req})


# ─── Assignment Views ─────────────────────────────────────────────────────────

@login_required
def assignment_create(request, course_uuid):
    course = get_object_or_404(Course, uuid=course_uuid)
    if not is_course_teacher(request.user, course):
        messages.error(request, 'Only the assigned teacher or admin can create assignments.')
        return redirect('course_detail', uuid=course_uuid)

    if request.method == 'POST':
        name = request.POST.get('assignment_name', '').strip()
        desc = request.POST.get('description', '').strip()
        due_date = request.POST.get('due_date') or None

        if not name:
            messages.error(request, 'Assignment name is required.')
            return render(request, 'courses/assignment_form.html', {'course': course, 'action': 'Create'})

        Assignment.objects.create(course=course, assignment_name=name, description=desc, due_date=due_date)
        messages.success(request, f'Assignment "{name}" created.')
        return redirect('course_detail', uuid=course_uuid)

    return render(request, 'courses/assignment_form.html', {'course': course, 'action': 'Create'})


@login_required
def assignment_delete(request, uuid):
    assignment = get_object_or_404(Assignment, uuid=uuid)
    course = assignment.course
    if not is_course_teacher(request.user, course):
        messages.error(request, 'Not authorised.')
        return redirect('course_detail', uuid=course.uuid)

    if request.method == 'POST':
        name = assignment.assignment_name
        assignment.delete()
        messages.success(request, f'Assignment "{name}" deleted.')
        return redirect('course_detail', uuid=course.uuid)

    return render(request, 'courses/course_confirm_delete.html', {'object': assignment, 'type': 'Assignment'})


@login_required
def assignment_submit(request, uuid):
    assignment = get_object_or_404(Assignment, uuid=uuid)
    course = assignment.course

    # Must be enrolled
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You must be enrolled in this course to submit assignments.')
        return redirect('course_detail', uuid=course.uuid)

    # Already submitted?
    existing = AssignmentSubmission.objects.filter(assignment=assignment, student=request.user).first()

    if request.method == 'POST':
        submission_type = request.POST.get('submission_type', '')
        text_content = request.POST.get('text_content', '').strip()
        pdf_file = request.FILES.get('pdf_file')

        if submission_type == 'pdf' and not pdf_file:
            messages.error(request, 'Please upload a PDF file.')
            return render(request, 'courses/assignment_submit.html', {
                'assignment': assignment, 'existing': existing,
            })
        if submission_type == 'text' and not text_content:
            messages.error(request, 'Please enter your text submission.')
            return render(request, 'courses/assignment_submit.html', {
                'assignment': assignment, 'existing': existing,
            })

        if existing:
            existing.submission_type = submission_type
            existing.text_content = text_content if submission_type == 'text' else None
            if pdf_file:
                existing.pdf_file = pdf_file
            existing.save()
            messages.success(request, 'Submission updated successfully.')
        else:
            AssignmentSubmission.objects.create(
                assignment=assignment,
                student=request.user,
                submission_type=submission_type,
                text_content=text_content if submission_type == 'text' else None,
                pdf_file=pdf_file if submission_type == 'pdf' else None,
            )
            messages.success(request, 'Assignment submitted successfully.')

        return redirect('course_detail', uuid=course.uuid)

    return render(request, 'courses/assignment_submit.html', {'assignment': assignment, 'existing': existing})


@login_required
def assignment_submissions(request, uuid):
    """Teacher views all submissions for an assignment and can assign marks."""
    assignment = get_object_or_404(Assignment, uuid=uuid)
    course = assignment.course

    if not is_course_teacher(request.user, course):
        messages.error(request, 'Only the assigned teacher or admin can view submissions.')
        return redirect('course_detail', uuid=course.uuid)

    submissions = assignment.submissions.select_related('student').all()
    return render(request, 'courses/assignment_submissions.html', {
        'assignment': assignment,
        'course': course,
        'submissions': submissions,
    })


@login_required
def grade_submission(request, uuid):
    """Teacher assigns marks and feedback to a submission."""
    submission = get_object_or_404(AssignmentSubmission, uuid=uuid)
    course = submission.assignment.course

    if not is_course_teacher(request.user, course):
        messages.error(request, 'Not authorised.')
        return redirect('course_list')

    if request.method == 'POST':
        marks = request.POST.get('marks', '').strip()
        feedback = request.POST.get('feedback', '').strip()
        submission.marks = marks if marks else None
        submission.feedback = feedback
        submission.save()
        messages.success(request, f'Marks saved for {submission.student.email}.')
        return redirect('assignment_submissions', uuid=submission.assignment.uuid)

    return render(request, 'courses/grade_submission.html', {'submission': submission})
