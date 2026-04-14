from django.contrib import admin
from .models import Course, CourseModule, CourseContent, Enrollment, EnrollmentRequest, Assignment, AssignmentSubmission


class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'teacher', 'created_date', 'updated_date')
    search_fields = ('course_name',)
    list_filter = ('teacher',)
    inlines = [CourseModuleInline]


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ('module_name', 'course', 'order', 'created_date')
    list_filter = ('course',)


@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'created_date')
    list_filter = ('content_type', 'module__course')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrollment_date')
    list_filter = ('course',)
    search_fields = ('student__email', 'course__course_name')


@admin.register(EnrollmentRequest)
class EnrollmentRequestAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status', 'created_date', 'note')
    list_filter = ('status', 'course')
    search_fields = ('student__email', 'course__course_name')
    raw_id_fields = ('student', 'course')
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        count = 0
        for req in queryset.filter(status='pending'):
            # Create enrollment
            Enrollment.objects.get_or_create(student=req.student, course=req.course)
            # Update request
            req.status = 'approved'
            req.save()
            count += 1
        self.message_user(request, f"Successfully approved {count} enrollment requests.")
    approve_requests.short_description = "Approve selected pending requests"

    def reject_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f"Successfully rejected {updated} pending requests.")
    reject_requests.short_description = "Reject selected pending requests"


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('assignment_name', 'course', 'due_date', 'created_date')
    list_filter = ('course',)


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'assignment', 'submission_type', 'marks', 'submitted_at')
    list_filter = ('submission_type', 'assignment__course')
    search_fields = ('student__email',)
