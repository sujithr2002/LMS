import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import CustomUser
from courses.models import Course, CourseModule, Enrollment, Assignment, AssignmentSubmission


FIRST_NAMES = [
    "Aarav","Arjun","Vivaan","Aditya","Vihaan","Dhruv","Krishna","Rohan","Ishaan","Kabir",
    "Ananya","Diya","Kavya","Priya","Sneha","Riya","Pooja","Meera","Nisha","Aisha",
    "Liam","Noah","Emma","Olivia","James","Sophia","Lucas","Mia","Ethan","Ava",
    "Oliver","Isabella","Elijah","Charlotte","Logan","Amelia","Mason","Harper","Aiden","Evelyn",
    "Mohammed","Fatima","Omar","Layla","Yusuf","Sara","Ahmed","Zara","Ali","Nour",
    "Wei","Mei","Jun","Lan","Fang","Hao","Xin","Yan","Ling","Tao",
    "Carlos","Sofia","Miguel","Valentina","Diego","Camila","Mateo","Lucia","Sebastian","Gabriela",
    "Raj","Priyanka","Suresh","Kavitha","Ramesh","Deepa","Vijay","Lakshmi","Sanjay","Geetha",
    "Tom","Sarah","Jack","Emily","Harry","Lily","George","Grace","Charlie","Chloe",
    "Joshua","Hannah","Daniel","Abigail","Samuel","Elizabeth","David","Victoria","Joseph","Madison",
]

LAST_NAMES = [
    "Sharma","Singh","Patel","Kumar","Gupta","Verma","Nair","Iyer","Reddy","Mehta",
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Moore",
    "Taylor","Anderson","Thomas","Jackson","White","Harris","Martin","Thompson","Young","Allen",
    "Khan","Ahmed","Hassan","Malik","Ali","Sheikh","Qureshi","Siddiqui","Ansari","Akhtar",
    "Chen","Wang","Li","Zhang","Liu","Huang","Yang","Wu","Zhou","Xu",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Perez","Sanchez","Torres","Ramirez","Flores",
    "Muller","Schmidt","Wagner","Becker","Fischer","Weber","Richter","Hoffmann","Koch","Braun",
    "Dupont","Bernard","Robert","Richard","Durand","Leroy","Moreau","Simon","Laurent","Petit",
    "Nakamura","Tanaka","Watanabe","Suzuki","Yamamoto","Kobayashi","Ito","Sasaki","Kato","Yamaguchi",
    "Osei","Mensah","Kwame","Asante","Boateng","Adjei","Owusu","Ansah","Darko","Twum",
]

COURSE_NAMES = [
    "Introduction to Python Programming",
    "Web Development with Django",
    "Data Science and Machine Learning",
    "UI/UX Design Principles",
    "JavaScript: From Beginner to Advanced",
    "Cloud Computing with AWS",
    "Database Design and SQL",
    "Mobile App Development with Flutter",
    "Cybersecurity Fundamentals",
    "Artificial Intelligence Essentials",
    "React.js and Modern Frontend",
    "DevOps and CI/CD Pipelines",
    "Digital Marketing Strategy",
    "Business Analytics with Excel",
    "Introduction to Blockchain",
    "Computer Networks and Protocols",
    "Algorithms and Data Structures",
    "Machine Learning with TensorFlow",
    "Linux Administration",
    "REST APIs with Django REST Framework",
]

COURSE_DESCRIPTIONS = [
    "A comprehensive course covering all the fundamentals and advanced concepts with hands-on projects.",
    "Learn industry-standard practices through real-world examples and guided exercises.",
    "Master the essentials and go beyond with our project-based learning approach.",
    "From zero to hero - this course is designed for all experience levels.",
    "Dive deep into core concepts and build production-ready applications.",
    "Sharpen your skills with curated exercises and expert-led video content.",
    "A practical, job-ready curriculum that focuses on modern tools and workflows.",
    "Structured learning path with assignments, quizzes, and real-world capstone projects.",
]

MODULE_NAMES_OPTIONS = [
    ["Getting Started", "Core Concepts", "Advanced Topics", "Projects and Practice"],
    ["Foundations", "Building Blocks", "Real World Applications", "Final Assessment"],
    ["Introduction", "Deep Dive", "Best Practices", "Capstone Project"],
    ["Setup and Installation", "Fundamentals", "Advanced Features", "Deployment"],
    ["Overview", "Key Techniques", "Industry Applications", "Review and Exam"],
]

ASSIGNMENT_NAMES = [
    "Homework: Fundamentals Quiz",
    "Project: Build a Demo Application",
    "Assignment: Code Review Exercise",
    "Lab: Hands-On Implementation",
    "Assessment: Mid-Module Test",
    "Project: Final Capstone",
    "Exercise: Problem Solving Set",
    "Task: Research Report Submission",
]

ASSIGNMENT_DESCRIPTIONS = [
    "Complete the given tasks and submit your answers in the text box below or as a PDF.",
    "Build the project as described in the module and submit your work.",
    "Review the provided code snippet, identify issues, and write your findings.",
    "Complete the lab exercise following the step-by-step guide in the module.",
    "Answer all questions and show your working where applicable.",
]

TEXT_SUBMISSIONS = [
    "I have completed the assignment as required. The main challenge was understanding the core concept but after reviewing the lecture, I was able to implement it successfully.",
    "Here is my solution: I followed the module instructions step by step and achieved the expected output. I tested edge cases and everything works correctly.",
    "After careful study, I have completed the assignment. My approach was to break the problem into smaller parts and solve each one individually.",
    "I completed this exercise by applying the techniques taught in the module. The output matched the expected results and I documented my approach thoroughly.",
    "This was a challenging but rewarding assignment. I researched additional resources to supplement the module content and produced the attached solution.",
    "I have submitted my work for review. I followed best practices and included comments in my code to explain my reasoning.",
    "Assignment completed. I faced some difficulty with the advanced section but was able to resolve it after reviewing the video lectures.",
    "Here is my completed submission. I tested all edge cases and the implementation is working as expected with the given requirements.",
]

FEEDBACK_OPTIONS = [
    "Well done! Good understanding of the topic.",
    "Good effort. Work on improving your explanation.",
    "Excellent work! Keep it up.",
    "Needs improvement in some areas but overall decent.",
    "Great submission! Very detailed and well-structured.",
    "Satisfactory. Review the module notes for better understanding.",
]


class Command(BaseCommand):
    help = 'Seeds the database with 100 students, 20 teachers, 20 courses, modules, assignments, enrollments, and submissions.'

    @transaction.atomic
    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.MIGRATE_HEADING('\n[SEED] Starting database seed...'))

        # -- Step 1: Teachers --------------------------------------------------
        self.stdout.write('  Creating 20 teachers...')
        teachers = []
        for i in range(1, 21):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            email = f"teacher{i}@lms.edu"
            if CustomUser.objects.filter(email=email).exists():
                teachers.append(CustomUser.objects.get(email=email))
                continue
            user = CustomUser.objects.create_user(
                email=email,
                password="Teacher@123",
                first_name=fn,
                last_name=ln,
                phone=f"+91 9{random.randint(100000000, 999999999)}",
                is_active=True,
                is_teacher=True,
            )
            teachers.append(user)
        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(teachers)} teachers ready'))

        # -- Step 2: Students --------------------------------------------------
        self.stdout.write('  Creating 100 students...')
        students = []
        for i in range(1, 101):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            email = f"student{i}@lms.edu"
            if CustomUser.objects.filter(email=email).exists():
                students.append(CustomUser.objects.get(email=email))
                continue
            user = CustomUser.objects.create_user(
                email=email,
                password="Student@123",
                first_name=fn,
                last_name=ln,
                phone=f"+91 8{random.randint(100000000, 999999999)}",
                is_active=True,
            )
            students.append(user)
        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(students)} students ready'))

        # -- Step 3: Courses ---------------------------------------------------
        self.stdout.write('  Creating 20 courses...')
        courses = []
        for i, name in enumerate(COURSE_NAMES):
            teacher = teachers[i % len(teachers)]
            course, created = Course.objects.get_or_create(
                course_name=name,
                defaults={
                    'description': random.choice(COURSE_DESCRIPTIONS),
                    'teacher': teacher,
                }
            )
            if not created:
                course.teacher = teacher
                course.save()
            courses.append(course)
        self.stdout.write(self.style.SUCCESS(f'  [OK] {len(courses)} courses ready'))

        # -- Step 4: Modules & Assignments -------------------------------------
        self.stdout.write('  Creating modules and assignments...')
        all_assignments = []
        for course in courses:
            module_set = random.choice(MODULE_NAMES_OPTIONS)
            for order, mod_name in enumerate(module_set):
                CourseModule.objects.get_or_create(
                    course=course,
                    module_name=mod_name,
                    defaults={
                        'module_description': f"This module covers {mod_name.lower()} for {course.course_name}.",
                        'order': order,
                    }
                )

            num_assignments = random.randint(2, 3)
            assignment_pool = random.sample(ASSIGNMENT_NAMES, num_assignments)
            for a_name in assignment_pool:
                due = date.today() + timedelta(days=random.randint(7, 60))
                assignment, _ = Assignment.objects.get_or_create(
                    course=course,
                    assignment_name=a_name,
                    defaults={
                        'description': random.choice(ASSIGNMENT_DESCRIPTIONS),
                        'due_date': due,
                    }
                )
                all_assignments.append(assignment)
        self.stdout.write(self.style.SUCCESS(f'  [OK] Modules and {len(all_assignments)} assignments ready'))

        # -- Step 5: Enrollments -----------------------------------------------
        self.stdout.write('  Enrolling students into courses...')
        total_enrollments = 0
        for student in students:
            enrolled_courses = random.sample(courses, random.randint(4, 8))
            for course in enrolled_courses:
                _, created = Enrollment.objects.get_or_create(student=student, course=course)
                if created:
                    total_enrollments += 1
        self.stdout.write(self.style.SUCCESS(f'  [OK] {total_enrollments} enrollments created'))

        # -- Step 6: Submissions -----------------------------------------------
        self.stdout.write('  Creating assignment submissions and grades...')
        total_submissions = 0
        graded_count = 0
        for assignment in all_assignments:
            enrolled_students = list(
                Enrollment.objects.filter(course=assignment.course).values_list('student', flat=True)
            )
            if not enrolled_students:
                continue
            submitters_count = max(1, int(len(enrolled_students) * random.uniform(0.4, 0.8)))
            submitter_ids = random.sample(enrolled_students, min(submitters_count, len(enrolled_students)))

            for sid in submitter_ids:
                try:
                    student_obj = CustomUser.objects.get(id=sid)
                except CustomUser.DoesNotExist:
                    continue

                sub, created = AssignmentSubmission.objects.get_or_create(
                    assignment=assignment,
                    student=student_obj,
                    defaults={
                        'submission_type': 'text',
                        'text_content': random.choice(TEXT_SUBMISSIONS),
                    }
                )
                if created:
                    total_submissions += 1
                    if random.random() < 0.6:
                        sub.marks = round(random.uniform(45, 100), 1)
                        sub.feedback = random.choice(FEEDBACK_OPTIONS)
                        sub.save()
                        graded_count += 1

        self.stdout.write(self.style.SUCCESS(f'  [OK] {total_submissions} submissions ({graded_count} graded)'))

        # -- Summary -----------------------------------------------------------
        self.stdout.write('\n' + '-' * 50)
        self.stdout.write(self.style.SUCCESS('[DONE] Seed complete! Summary:'))
        self.stdout.write(f'   Teachers   : {CustomUser.objects.filter(is_teacher=True).count()}')
        self.stdout.write(f'   Students   : {CustomUser.objects.filter(is_admin=False, is_teacher=False).count()}')
        self.stdout.write(f'   Courses    : {Course.objects.count()}')
        self.stdout.write(f'   Modules    : {CourseModule.objects.count()}')
        self.stdout.write(f'   Assignments: {Assignment.objects.count()}')
        self.stdout.write(f'   Enrollments: {Enrollment.objects.count()}')
        self.stdout.write(f'   Submissions: {AssignmentSubmission.objects.count()}')
        self.stdout.write('\n  Default Passwords:')
        self.stdout.write('   Teachers -> Teacher@123')
        self.stdout.write('   Students -> Student@123')
        self.stdout.write('-' * 50 + '\n')
