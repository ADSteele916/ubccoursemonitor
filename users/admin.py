from django.contrib import admin

from .models import Profile


class CourseTupleInline(admin.StackedInline):
    model = Profile.courses.through


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    inlines = [CourseTupleInline]
    list_display = ("__str__", "is_premium", "number_of_courses")
