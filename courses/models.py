import typing

import requests
from bs4 import BeautifulSoup

from django.core.validators import RegexValidator
from django.db import models


year_validator = r"^20\d{2}$"
subject_validator = r"^[A-Z]{2,4}$"
number_validator = r"^[A-Z0-9]{3,4}$"
section_validator = r"^[A-Z0-9]{3,5}$"


class Course(models.Model):
    year = models.CharField(max_length=4, validators=[RegexValidator(regex=year_validator)])
    session = models.CharField(max_length=1, choices=[("W", "Winter"), ("S", "Summer")])
    subject = models.CharField(max_length=4, validators=[RegexValidator(regex=subject_validator)])
    number = models.CharField(max_length=5, validators=[RegexValidator(regex=number_validator)])
    section = models.CharField(max_length=5, validators=[RegexValidator(regex=section_validator)])
    last_open = models.DateTimeField(blank=True, null=True, default=None)

    def __str__(self):
        return f"{self.year}{self.session} {self.subject} {self.number} {self.section}"

    class Meta:
        unique_together = ["year", "session", "subject", "number", "section"]
        ordering = ["year", "session", "subject", "number", "section"]

    def url(self):
        return f"https://courses.students.ubc.ca/cs/courseschedule?sesscd={self.session}&pname=subjarea&tname=subj" \
               f"-section&course={self.number}&sessyr={self.year}&section={self.section}&dept={self.subject}"

    def download_ssc(self) -> BeautifulSoup or None:
        """Downloads the course's SSC page and returns its HTML content."""
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, "
                                 "like Gecko) Chrome/39.0.2171.95 Safari/537.36"}
        try:
            response = requests.get(self.url(), headers=headers)
            return BeautifulSoup(response.text, "html.parser")
        except Exception:
            return None

    def get_seats(self) -> typing.Tuple[int] or False:
        """Updates the four seats variables in the course object to match the SSC page. Returns False on failure."""
        soup = self.download_ssc()

        try:
            if soup is not None:
                seats = list(map(lambda i: i.text, soup.select("table > tr > td > strong")))
                total_open = int(seats[0])
                registered = int(seats[1])
                general_open = int(seats[2])
                restricted_open = int(seats[3])
                return total_open, registered, general_open, restricted_open
            else:
                return False
        except IndexError:
            return False


class CourseTuple(models.Model):
    restricted = models.BooleanField()
    course = models.ForeignKey("Course", on_delete=models.CASCADE)

    class Meta:
        unique_together = ["restricted", "course"]
        ordering = ["course", "restricted"]

    def __str__(self):
        return f"{self.course}" if self.restricted is False else f"{self.course} R"
