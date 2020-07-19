import re
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
    campus = models.CharField(
        max_length=4,
        choices=[("UBC", "UBC Vancouver"), ("UBCO", "UBC Okanagan")],
        default="UBC",
    )
    year = models.CharField(max_length=4, validators=[RegexValidator(regex=year_validator)])
    session = models.CharField(max_length=1, choices=[("W", "Winter"), ("S", "Summer")])
    subject = models.CharField(max_length=4, validators=[RegexValidator(regex=subject_validator)])
    number = models.CharField(max_length=5, validators=[RegexValidator(regex=number_validator)])
    section = models.CharField(max_length=5, validators=[RegexValidator(regex=section_validator)])
    last_open = models.DateTimeField(blank=True, null=True, default=None)

    def __str__(self) -> str:
        return f"{self.campus} {self.year}{self.session} {self.subject} {self.number} {self.section}"

    class Meta:
        unique_together = ["campus", "year", "session", "subject", "number", "section"]
        ordering = ["campus", "year", "session", "subject", "number", "section"]

    def sub_num_sec(self) -> str:
        return f"{self.subject} {self.number} {self.section}"

    def url(self) -> str:
        return f"https://courses.students.ubc.ca/cs/courseschedule?pname=subjarea&tname=subj-section&campuscd=" \
               f"{self.campus}&sessyr={self.year}&sesscd={self.session}&dept={self.subject}&course={self.number}" \
               f"&section={self.section}"

    def download_ssc(self) -> BeautifulSoup or None:
        """Downloads the course's SSC page and returns its HTML content."""
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, "
                                 "like Gecko) Chrome/39.0.2171.95 Safari/537.36"}
        try:
            response = requests.get(self.url(), headers=headers)
            return BeautifulSoup(response.text, "html.parser")
        except Exception:
            return None

    def get_seats(self) -> typing.Union[typing.Tuple[int, int, int, int], str,  bool]:
        soup = self.download_ssc()

        if soup is not None:
            try:
                seats = list(map(lambda i: i.text, soup.select("table > tr > td > strong")))
                total_open = int(seats[0])
                registered = int(seats[1])
                general_open = int(seats[2])
                restricted_open = int(seats[3])
                return total_open, registered, general_open, restricted_open
            except IndexError:
                stt_only = r"Note: The remaining seats in this section are only available through a Standard " \
                           r"Timetable \(STT\)"
                stt_string = soup.select("html > body > div.container > div.content.expand > strong")
                if len(stt_string) > 0 and re.search(stt_only, stt_string[0].text):
                    return "stt"

                no_longer_offered = r"The requested section is either no longer offered at UBC (Vancouver|Okanagan) " \
                                    r"or is not being offered this session."
                nlo_string = soup.select("html > body > div.container > div.content.expand")
                if len(nlo_string) > 0 and re.search(no_longer_offered, nlo_string[0].text):
                    return "invalid"

        return False


class CourseTuple(models.Model):
    restricted = models.BooleanField()
    course = models.ForeignKey("Course", on_delete=models.CASCADE)

    class Meta:
        unique_together = ["restricted", "course"]
        ordering = ["course", "restricted"]

    def __str__(self):
        return f"{self.course}" if self.restricted is False else f"{self.course} R"
