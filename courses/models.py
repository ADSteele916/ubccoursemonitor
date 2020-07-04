from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Course(models.Model):
    year = models.CharField(max_length=4, validators=[RegexValidator(regex="^\d{4}$")])
    session = models.CharField(max_length=1, choices=[("W", "Winter"), ("S", "Summer")])
    subject = models.CharField(max_length=4, validators=[RegexValidator(regex="^[A-Z]{4}$")])
    number = models.CharField(max_length=5, validators=[RegexValidator(regex="^[A-Z0-9]{3,4}$")])
    section = models.CharField(max_length=5, validators=[RegexValidator(regex="^[A-Z0-9]{3,5}$")])
    last_open = models.DateTimeField(blank=True, default=timezone.now)

    def __str__(self):
        return f"{self.year}{self.session} {self.subject} {self.number} {self.section}"

    def url(self):
        return f"https://courses.students.ubc.ca/cs/courseschedule?sesscd={self.session}&pname=subjarea&tname=subj" \
               f"-section&course={self.number}&sessyr={self.year}&section={self.section}&dept={self.subject}"

    class Meta:
        unique_together = ["year", "session", "subject", "number", "section"]
        ordering = ["year", "session", "subject", "number", "section"]


class CourseTuple(models.Model):
    restricted = models.BooleanField()
    course = models.ForeignKey("Course", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.course}" if self.restricted is False else f"{self.course} R"

    class Meta:
        unique_together = ["restricted", "course"]
        ordering = ["course", "restricted"]
