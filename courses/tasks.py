import datetime
import time
import typing
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.utils import timezone

from celery import shared_task
from celery.utils.log import get_task_logger

from .models import Course
from users.models import Profile


logger = get_task_logger(__name__)


@shared_task
def monitor() -> None:
    users = Profile.objects.all()
    to_remove = []
    for course in Course.objects.all():
        if users.filter(courses__course=course).count() > 0:
            if course.last_open is None or course.last_open + settings.OPEN_COURSE_DELAY < timezone.now():
                course_id = course.pk
                check = check_course(course_id, users)
                if check is not None:
                    course.last_open = check
                    course.save()
            time.sleep(settings.POLL_FREQUENCY)
        else:
            to_remove.append(course)
    for course in to_remove:
        course.delete()


def check_course(course_id: int, users: QuerySet) -> datetime.datetime or None:

    course = Course.objects.get(pk=course_id)

    def open_seats(seats: typing.Tuple[int, int, int, int]) -> str:
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
                logger.info(f"{t}: General opening in {course}")
                to_notify = users.filter(courses__course=course)
            else:
                logger.info(f"{t}: Restricted opening in {course}.")
                to_notify = users.filter(courses__course=course, courses__restricted=True)

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
                logger.info(f"{t}: Sent email about {course} to {recipients}.")
            elif notification is None:
                logger.info(f"{t}: Failed to send email about {course} to {recipients}.")
            else:
                logger.info(f"{t}: No users are monitoring {course} for {open_seats} seats.")
                return None

            return next_last_open

        else:
            logger.info(f"{t}: No openings in {course}.")
            return None
    else:
        logger.info(f"{t}: Failed to check for open seats in {course}.")
        return None
