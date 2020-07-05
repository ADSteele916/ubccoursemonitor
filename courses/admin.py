from django.contrib import admin

from .models import Course, CourseTuple


@admin.register(CourseTuple)
class CourseTupleAdmin(admin.ModelAdmin):
    pass


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    pass
