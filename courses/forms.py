from django import forms

from .models import Course, CourseTuple


class CourseRegisterForm(forms.ModelForm):

    def clean(self):
        return self.cleaned_data

    class Meta:
        model = Course
        fields = ['year', 'session', 'subject', 'number', 'section']


class CourseTupleRegisterForm(forms.ModelForm):

    def clean(self):
        return self.cleaned_data

    class Meta:
        model = CourseTuple
        fields = ['restricted']
        labels = {
            'restricted': 'Monitor for all seat openings (including restricted ones). Leave unchecked for general '
                          'seats only.',
        }
