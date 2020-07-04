from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Course, CourseTuple
from users.models import Profile
from .forms import CourseRegisterForm, CourseTupleRegisterForm
import ubccoursemonitor.urls


def home(request):
    return render(request, 'courses/home.html', context())


def faq(request):
    return render(request, 'courses/faq.html', context(title='FAQ'))


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
        else:
            message = 'Sorry! We are still Beta testing and are not ready for public use yet. ' \
                              'Message Alex with your username to get your account approved.'
            messages.warning(request, message)
        return redirect('courses-list')

    else:
        c_form = CourseRegisterForm()
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
