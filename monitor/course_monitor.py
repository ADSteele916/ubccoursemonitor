import datetime
import threading
import time
import typing
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from courses.models import Course
from users.models import Profile


class CourseMonitor:
    """A class used to monitor courses for openings on behalf of a list of users."""

    def __init__(self) -> None:

        self.users = Profile.objects.all()

        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def monitor_loop(self) -> None:
        """Loops through all indexed courses checking for openings, then refreshes list."""
        while True:
            self.users = Profile.objects.all()
            to_remove = []
            for course in Course.objects.all().distinct().iterator():
                print(f"Iterated through {course}.")
                if self.users.filter(courses__course=course).count() > 0:
                    if course.last_open is None or course.last_open + settings.OPEN_COURSE_DELAY < timezone.now():
                        check = self.check_course(course)
                        if check is not None:
                            course.last_open = check
                            course.save()
                    time.sleep(settings.POLL_FREQUENCY)
                else:
                    to_remove.append(course)
            for course in to_remove:
                course.delete()
            time.sleep(settings.POLL_FREQUENCY * 2.0)

    def check_course(self, course: Course) -> datetime.datetime or None:
        """Checks an individual course for openings on behalf of a list of users and emails them if there is one."""

        def open_seats(seats: typing.Tuple[int, int, int, int]) -> str:
            """Returns a string based on whether there are general, restricted, or no seats available in the course."""
            if seats[2] != 0:
                return "general"
            elif seats[0] != 0:
                return "restricted"
            else:
                return "none"

        get_seats = course.get_seats()

        t = datetime.datetime.now().strftime("%H:%M:%S")

        if get_seats is not False:
            open_seats = open_seats(get_seats)
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
                    next_last_open = timezone.now() - (settings.OPEN_COURSE_DELAY * 3 / 4)
                elif to_notify.filter(is_premium=True).count() > 0:
                    next_last_open = timezone.now() - (settings.OPEN_COURSE_DELAY / 2)
                else:
                    next_last_open = timezone.now()

                try:
                    subject = f"Check the SSC! Opening in {course}!"
                    message = f"There is an opening in {course.subject} {course.number}, " \
                              f"section {course.section}.\n\n{course.url()}"
                    to_addresses = list(map(lambda profile: profile.user.email, to_notify))
                    notification = send_mail(subject, message, settings.EMAIL_HOST_USER, to_addresses)
                except SMTPException:
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

                if notification is not None and notification > 0:
                    print(f"{t}: Sent email about {course} to {recipients}.")
                elif notification is None:
                    print(f"{t}: Failed to send email about {course} to {recipients}.")
                else:
                    print(f"{t}: No users are monitoring {course} for {open_seats} seats.")
                    return None

                return next_last_open

            else:
                print(f"{t}: No openings in {course}.")
                return None
        else:
            print(f"{t}: Failed to check for open seats in {course}.")
            return None
