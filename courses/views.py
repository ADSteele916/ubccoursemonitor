from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render

from .forms import CourseRegisterForm, CourseTupleRegisterForm
from .models import Course, CourseTuple
from users.models import Profile


def home(request):
    return render(request, 'courses/home.html', context())


def faq(request):
    faq_elements = {
        "Why do I need to create an account?":
            "We made the design decision to use accounts for three main reasons. First, it allows you to easily see "
            "and change which sections you are currently monitoring at any given time. This way, you won't receive an "
            "email about a section that you were briefly interested in joining and then forgot about months after the "
            "fact. Second, it simplifies the process of monitoring multiple sections. Instead of entering and "
            "confirming your email for every section, you only need to log in. Finally, if someone else nabs the "
            "opening we just emailed you about, you won't have to come back here and re-add it. You will continue to "
            "get emails about openings until you remove the section from your profile.",
        "What information do you store?":
            "We only store your username, email, and any sections you are currently monitoring. Passwords are "
            "encrypted using industry-standard practices and cannot be accessed by anyone once set.",
        "Why can't I add any more sections?":
            "We are currently working with rather limited resources. We are using free or budget plans for our web "
            "hosting, databases, and emails. In order to help the most students possible, we are limiting the number "
            "of sections that each user can monitor. We know that this is a less-than-optimal solution and are "
            "looking into other ways to improve our capabilities.",
        "What is the 'Year' field in the 'Add A Course' menu for?":
            "It's for the year of the session (e.g. 2020W) of the section you want to monitor. The form should "
            "autofill the correct value for you.",
        "How often do you poll the SSC?":
            "We send one request every few seconds. While a few more requests could theoretically improve chances of "
            "finding a seat opening, we don't want the SSC to think that it's getting DDoSed and block our IP. "
            "Besides, checking a section that often should be more than enough to catch at least 90% of seat "
            "openings.",
        "I haven't been receiving any emails even though I know there have been openings in sections I'm monitoring.":
            "Check your Spam/Junk folder and whitelist notifier@ubccoursemonitor.email to make sure that you receive "
            "any future notifications.",
        "I got an email but the section was full when I checked.":
            "Unfortunately, someone else like got the open seat before you did. To maximize your chances of getting "
            "into a section that you are monitoring, be sure to check the SSC as soon as you receive an email from us.",
        "I didn't act fast enough after receiving an email. Do I need to add the section again?":
            "No, you don't. After an email is sent out for a section, there will be a brief cooldown period of about "
            "twelve hours or so (so we don't spam you if a section stays open for a while), after which we will "
            "resume polling.",
        "I got a seat in the section I was monitoring. What should I do next?":
            "Great! Now you'll likely want to remove the section from your profile, so you don't get any more emails. "
            "You can do so by unticking the boxes next to them on your Profile page.",
        "The section I want to get into has a waitlist. Should I use the UBC Course Monitor or just add the waitlist "
        "section?":
            "Ideally, both. Some waitlists are managed manually by a given department. This means that there is "
            "sometimes a window of opportunity in which there is an opening in the section you want but the first "
            "person on the waitlist hasn't been moved into it yet, during which you can snag the open seat. However, "
            "you shouldn't count on this. Register for the waitlist section, just to be safe.",
    }
    return render(request, 'courses/faq.html', context(title='FAQ', faq_elements=faq_elements))


def about(request):
    return render(request, 'courses/about.html', context(title='About'))


@login_required()
def courses(request):
    if request.method == 'POST':
        if (
            request.user.is_staff
            or request.user.profile.is_premium
            or request.user.profile.number_of_courses()
            < settings.MAX_NON_PREMIUM_SECTIONS
        ):
            c_form = CourseRegisterForm(request.POST)
            ct_form = CourseTupleRegisterForm(request.POST)

            if c_form.is_valid() and ct_form.is_valid():
                c, new_c = Course.objects.get_or_create(campus=c_form.instance.campus,
                                                        year=c_form.instance.year,
                                                        session=c_form.instance.session,
                                                        subject=c_form.instance.subject,
                                                        number=c_form.instance.number,
                                                        section=c_form.instance.section)
                c_name = c.sub_num_sec()

                ct_form.instance.course = c
                ct, new_ct = CourseTuple.objects.get_or_create(course=ct_form.instance.course,
                                                               restricted=ct_form.instance.restricted)

                get_seats = c.get_seats()
                if new_c:
                    if get_seats is False:
                        fail_message = f"We were unable to download {c_name}'s page from the SSC. This could be " \
                                       f"because of the SSC being down for maintenance or a database update (this " \
                                       f"usually occurs in the early morning, Pacific time). It could also be caused " \
                                       f"by high SSC traffic, usually around registration or grade releases. Please " \
                                       f"try again in a couple hours."
                        messages.warning(request, fail_message)
                        c.delete()
                        return redirect('courses-list')
                    elif get_seats == "invalid":
                        invalid_message = f"This section does not appear to exist. Please check your form entry for " \
                                          f"errors and try again. If the course does, in fact, exist, please contact " \
                                          f"us at contact@ubccoursemonitor.email."
                        messages.warning(request, invalid_message)
                        c.delete()
                        return redirect('courses-list')

                if ct not in request.user.profile.courses.all():
                    if get_seats == "stt":
                        stt_message = "The remaining seats in this section appear to only be available through an " \
                                      "STT. You will be notified if any non-STT seats open up in this section."
                        messages.warning(request, stt_message)
                    elif isinstance(get_seats, tuple) and get_seats[4]:
                        blocked_message = "This section is currently blocked for registration. You will be notified " \
                                          "if the section is unblocked and there is an opening."
                        messages.warning(request, blocked_message)

                    try:
                        ct_opposite_restricted = CourseTuple.objects.get(course=ct_form.instance.course,
                                                                         restricted=(not ct_form.instance.restricted))
                        if ct_opposite_restricted in request.user.profile.courses.all():
                            request.user.profile.courses.remove(ct_opposite_restricted)
                    except ObjectDoesNotExist:
                        pass
                    finally:
                        request.user.profile.courses.add(ct)
                        message = f'Your are now monitoring {c_name} '
                        message += 'for any seat openings.' if ct.restricted else 'for general seat openings.'
                        messages.success(request, message)
                else:
                    message = f'You are already monitoring {c_name} '
                    message += 'for any seat openings.' if ct.restricted else 'for general seat openings.'
                    messages.warning(request, message)
                return redirect('courses-list')

        else:
            message = f"Sorry! Due to limited resources, you can only monitor {settings.MAX_NON_PREMIUM_SECTIONS} " \
                      f"sections at once. We are working on expanding this limit in the future. For now, go to your " \
                      f"profile and deselect any sections that you do not need."
            messages.warning(request, message)
            return redirect('courses-list')

    else:
        default_year = str(datetime.now().year) if datetime.now().month >= 3 else str(datetime.now().year - 1)
        default_session = "W" if datetime.now().month >= 7 or datetime.now().month <= 2 else "S"
        c_form = CourseRegisterForm(initial={'campus': 'UBC', 'year': default_year, 'session': default_session})
        ct_form = CourseTupleRegisterForm()

    user_courses = request.user.profile.courses.all()

    view_context = context(title='Add Course', c_form=c_form, ct_form=ct_form, courses=user_courses)

    return render(request, 'courses/courses.html', view_context)


def context(title=None, **kwargs):
    output = {}

    if title is not None:
        output['title'] = title

    users = Profile.objects.all()
    courses_list = []
    for course in Course.objects.all():
        if users.filter(courses__course=course).count() > 0:
            courses_list.append(course)
    if len(courses_list) > 0:
        output['courses_total'] = len(courses_list)
        output['users_total'] = Profile.objects.count()

    output.update(kwargs)

    return output
