import datetime
import threading
import time
import typing

import requests
from bs4 import BeautifulSoup

from .notifier import Notifier
from django.utils import timezone
from users.models import Profile
from courses.models import Course


class CourseMonitor:
    """A class used to monitor courses for openings on behalf of a list of users."""

    def __init__(self, notifier: Notifier, frequency: float = 30.0) -> None:

        self.users = Profile.objects.all()
        self.courses = Course.objects.all

        self.notifier = notifier

        self.poll_frequency = max(frequency, 1.0)
        self.open_course_delay = datetime.timedelta(hours=24)
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def monitor_loop(self) -> None:
        """Loops through all indexed courses checking for openings, then refreshes list."""
        while True:
            self.users = Profile.objects.all()
            to_remove = []
            for course in self.courses():
                if self.users.filter(courses__course=course).count() > 0:
                    if course.last_open + self.open_course_delay < timezone.now():
                        self.check_course(course)
                        time.sleep(self.poll_frequency)
                else:
                    to_remove.append(course)
            for course in to_remove:
                course.delete()
            time.sleep(self.poll_frequency)

    @staticmethod
    def download_ssc(course: Course) -> BeautifulSoup or None:
        """Downloads the course's SSC page and returns its HTML content."""
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, "
                                 "like Gecko) Chrome/39.0.2171.95 Safari/537.36"}
        try:
            response = requests.get(course.url(), headers=headers)
            return BeautifulSoup(response.text, "html.parser")
        except Exception:
            return None

    def get_seats(self, course: Course) -> typing.Tuple[int] or False:
        """Updates the four seats variables in the course object to match the SSC page. Returns False on failure."""
        soup = self.download_ssc(course)

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

    @staticmethod
    def open_seats(seats: typing.Tuple[int, int, int, int]) -> str:
        """Returns a string based on whether there are general, restricted, or no seats available in the course."""
        if seats[2] != 0:
            return "general"
        elif seats[0] != 0:
            return "restricted"
        else:
            return "none"

    def check_course(self, course: Course) -> bool:
        """Checks an individual course for openings on behalf of a list of users and emails them if there is one."""
        get_seats = self.get_seats(course)

        t = datetime.datetime.now().strftime("%H:%M:%S")

        if get_seats is not False:
            open_seats = self.open_seats(get_seats)
            if open_seats != "none":
                if open_seats == "general":
                    print(f"{t}: General opening in {course}")
                    to_notify = self.users.filter(courses__course=course)
                else:
                    print(f"{t}: Restricted opening in {course}.")
                    to_notify = self.users.filter(courses__course=course, courses__restricted=True)

                staff_in_list = to_notify.filter(user__is_staff=True)
                if staff_in_list.count() > 0:
                    to_notify = staff_in_list

                if to_notify.count() > 0:
                    notification = self.notifier.send_notification(to_notify, course)
                else:
                    notification = None

                if len(to_notify) == 0:
                    recipients = ""
                elif len(to_notify) == 1:
                    recipients = str(to_notify[0])
                elif len(to_notify) == 2:
                    recipients = str(to_notify[0]) + " and " + str(to_notify[1])
                else:
                    recipients = ""
                    for user in to_notify[:(len(to_notify) - 1)]:
                        recipients = recipients + str(user) + ", "
                    recipients = recipients + "and " + str(to_notify[-1])

                if notification:
                    print(f"{t}: Sent email about {course} to {recipients}.\n")
                elif not notification:
                    print(f"{t}: Failed to send email about {course} to {recipients}.\n")
                else:
                    print(f"{t}: No users are monitoring {course}.\n")

                if staff_in_list.count() > 0:
                    course.last_open = timezone.now() - (self.open_course_delay * 3 / 4)
                elif to_notify.filter(is_premium=True).count() > 0:
                    course.last_open = timezone.now() - (self.open_course_delay / 2)
                else:
                    course.last_open = timezone.now()
                course.save()
                return True

            else:
                print(f"{t}: No openings in {course}.\n")
                return False
        else:
            print(f"{t}: Failed to check for open seats in {course}.\n")
            return False
