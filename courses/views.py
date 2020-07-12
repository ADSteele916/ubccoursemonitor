from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

import ubccoursemonitor.urls
from .forms import CourseRegisterForm, CourseTupleRegisterForm
from .models import Course, CourseTuple
from users.models import Profile


def home(request):
    return render(request, 'courses/home.html', context())


def faq(request):
    faq_elements = {
        "Why can't I add any courses?":
            "This site is still in what I would consider to be a closed beta. There are some lingering issues that "
            "I'd like to sort out before releasing it for general use. The site still works, of course, but it does "
            "need content for the Home and About pages, a couple of bug fixes, some more features, and a more robust "
            "host. If you're one of the people I told about the site, please just message me with your username and "
            "I'll enable your account if I haven't already.",
        "What is the 'Year' field in the 'Add A Course' menu for?":
            "It's for the year of the session (e.g. 2020W) of the section you want to monitor. The form should "
            "autofill the correct value for you.",
        "How often do you poll the SSC?":
            "We send one request every few seconds. While more requests (or even multiple monitoring threads) could "
            "theoretically improve chances of finding a seat opening, I don't want the SSC to think that it's getting "
            "DDoSed and block our IP. Besides, checking a course every minute should be more than enough to catch at "
            "least 90% of seat openings.",
        "I got an email but the section was full when I checked.":
            "Unfortunately, someone else like got the open seat before you did. To maximize your chances of getting "
            "into a course that you are monitoring, be sure to check the SSC as soon as you receive an email from us.",
        "I didn't act fast enough after receiving an email. Do I need to add the course again?":
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
        if request.user.is_staff or request.user.profile.is_premium or request.user.profile.number_of_courses() < 0:
            c_form = CourseRegisterForm(request.POST)
            ct_form = CourseTupleRegisterForm(request.POST)

            if c_form.is_valid() and ct_form.is_valid():
                c, new_c = Course.objects.get_or_create(year=c_form.instance.year,
                                                        session=c_form.instance.session,
                                                        subject=c_form.instance.subject,
                                                        number=c_form.instance.number,
                                                        section=c_form.instance.section)

                ct_form.instance.course = c

                ct, new_ct = CourseTuple.objects.get_or_create(course=ct_form.instance.course,
                                                               restricted=ct_form.instance.restricted)

                if ct not in request.user.profile.courses.all():
                    request.user.profile.courses.add(ct)
                    message = f'Your are now monitoring {c} '
                    message += 'for any seat openings.' if ct.restricted else 'for general seat openings.'
                    messages.success(request, message)
                else:
                    message = f'You are already monitoring {c} '
                    message += 'for any seat openings.' if ct.restricted else 'for general seat openings.'
                    messages.warning(request, message)
                return redirect('courses-list')
        else:
            message = 'Sorry! We are still Beta testing and are not ready for public use yet. ' \
                              'Message Alex with your username to get your account approved.'
            messages.warning(request, message)
            return redirect('courses-list')

    else:
        default_year = str(datetime.now().year) if datetime.now().month >= 3 else str(datetime.now().year - 1)
        c_form = CourseRegisterForm(initial={'year': default_year})
        ct_form = CourseTupleRegisterForm()

    user_courses = request.user.profile.courses.all()

    view_context = context(title='Add Course', c_form=c_form, ct_form=ct_form, courses=user_courses)

    return render(request, 'courses/courses.html', view_context)


def context(title=None, **kwargs):
    output = {}
    if title is not None:
        output['title'] = title
    output['courses_total'] = Course.objects.count()
    output['users_total'] = Profile.objects.count()
    output['running'] = ubccoursemonitor.urls.monitor.monitor_thread.is_alive()
    output.update(kwargs)
    return output
