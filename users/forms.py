from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.exclude(pk=self.instance.pk).get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError("A user with that username already exists.")

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.exclude(pk=self.instance.pk).get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError("A user with that email address already exists.")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.exclude(pk=self.instance.pk).get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError("A user with that username already exists.")

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.exclude(pk=self.instance.pk).get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError("A user with that email address already exists.")

    class Meta:
        model = User
        fields = ["username", "email"]


class ProfileUpdateForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Profile.objects.all(),
        required=False,
        help_text="These are the courses you are monitoring. Untick any courses that you want to stop getting emails "
        "about.",
    )

    class Meta:
        model = Profile
        fields = ["courses"]

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["courses"].queryset = (
            Profile.objects.filter(user=user).first().courses
        )
