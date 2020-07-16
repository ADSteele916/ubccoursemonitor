from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.shortcuts import redirect, render


from .forms import ProfileUpdateForm, UserRegisterForm, UserUpdateForm
from courses.views import context


class ExtraLoginView(LoginView):

    def get_context_data(self, **kwargs):
        view_context = super().get_context_data(**kwargs)
        view_context.update(context(title="Log In"))
        return view_context


class ExtraLogoutView(LogoutView):

    def get_context_data(self, **kwargs):
        view_context = super().get_context_data(**kwargs)
        view_context.update(context(title="Log Out"))
        return view_context


class ExtraPasswordResetView(PasswordResetView):

    def get_context_data(self, **kwargs):
        view_context = super().get_context_data(**kwargs)
        view_context.update(context(title="Reset Password"))
        return view_context


class ExtraPasswordResetDoneView(PasswordResetDoneView):

    def get_context_data(self, **kwargs):
        view_context = super().get_context_data(**kwargs)
        view_context.update(context(title="Reset Password"))
        return view_context


class ExtraPasswordResetConfirmView(PasswordResetConfirmView):

    def get_context_data(self, **kwargs):
        view_context = super().get_context_data(**kwargs)
        view_context.update(context(title="Confirm Password Reset"))
        return view_context


class ExtraPasswordResetCompleteView(PasswordResetCompleteView):

    def get_context_data(self, **kwargs):
        view_context = super().get_context_data(**kwargs)
        view_context.update(context(title="Password Reset!"))
        return view_context


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')

            new_user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
            login(request, new_user)

            message = "Your account is now good to go! Now click on 'Courses' to start adding sections to monitor."
            messages.success(request, message)

            return redirect('courses-home')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', context(title='Register', form=form))


@login_required()
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.user, request.POST, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated.')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(request.user, instance=request.user.profile)

    return render(request, 'users/profile.html', context(title='Profile', u_form=u_form, p_form=p_form))
