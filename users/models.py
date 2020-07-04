from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    courses = models.ManyToManyField("courses.CourseTuple", blank=True)
    is_premium = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}"

    def number_of_courses(self) -> int:
        return self.courses.count()
    number_of_courses.short_description = "Number of monitored courses"

    class Meta:
        ordering = ["user"]


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
