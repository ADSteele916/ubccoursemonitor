import smtplib
import socket
import typing

from users.models import Profile
from courses.models import Course, CourseTuple
from users.models import Profile


class Notifier:
    """A class that is used t send notification emails to a list of users."""

    def __init__(self, from_address: str, password: str, server: str = "smtp.gmail.com", port: int = 587) -> None:
        self.from_address = from_address
        self.password = password

        self.server_address = server
        self.port = port

    def send_notification(self, to: typing.List[Profile], course: Course) -> bool:
        """Sends a notification to the given users about the given course from the class' email address."""
        subject = "CHECK THE SSC!"
        msg = f"There is an opening in {course.subject} {course.number}, section {course.section}.\n\n{course.url()}"
        message = f"Subject: {subject}\n\n{msg}"

        to_addresses = list(map(lambda profile: profile.user.email, to))

        try:
            server = smtplib.SMTP(self.server_address, self.port)
        except socket.gaierror:
            return False

        try:
            server.starttls()
            server.login(self.from_address, self.password)
            server.sendmail(self.from_address, to_addresses, message)
            server.quit()
            return True
        except Exception:
            return False
