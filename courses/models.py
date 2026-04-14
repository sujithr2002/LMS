import uuid
from django.db import models
from django.conf import settings


class Course(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    course_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_courses',
        limit_choices_to={'is_teacher': True},
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.course_name


class CourseModule(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    module_name = models.CharField(max_length=255)
    module_description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_date']

    def __str__(self):
        return f"{self.course.course_name} - {self.module_name}"


class CourseContent(models.Model):
    CONTENT_TYPES = [
        ('video', 'Video'),
        ('pdf', 'PDF'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    content_file = models.FileField(upload_to='courses/content/')
    order = models.PositiveIntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_date']

    def __str__(self):
        return f"{self.module.module_name} - {self.title}"

    def is_video(self):
        return self.content_type == 'video'

    def is_pdf(self):
        return self.content_type == 'pdf'


# ─── Enrollment Request ───────────────────────────────────────────────────────

class EnrollmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollment_requests',
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollment_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True, null=True)          # optional rejection note
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.student.email} -> {self.course.course_name} [{self.status}]"


# ─── Enrollment ───────────────────────────────────────────────────────────────

class Enrollment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(auto_now_add=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-enrollment_date']

    def __str__(self):
        return f"{self.student.email} → {self.course.course_name}"


# ─── Assignments ──────────────────────────────────────────────────────────────

class Assignment(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    assignment_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.course.course_name} - {self.assignment_name}"


class AssignmentSubmission(models.Model):
    SUBMISSION_TYPES = [
        ('pdf', 'PDF Upload'),
        ('text', 'Text Submission'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    submission_type = models.CharField(max_length=10, choices=SUBMISSION_TYPES)
    text_content = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(upload_to='assignments/submissions/', blank=True, null=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('assignment', 'student')
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.email} → {self.assignment.assignment_name}"
