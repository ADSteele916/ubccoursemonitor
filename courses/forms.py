import re

from django import forms

from .models import Course, CourseTuple, year_validator, subject_validator, number_validator, section_validator


class CourseRegisterForm(forms.ModelForm):

    def clean(self):
        return self.cleaned_data

    def clean_year(self):
        year = self.cleaned_data['year']
        if re.match(year_validator, year):
            return year
        else:
            raise forms.ValidationError(
                'Please enter the year of the session of the course you are monitoring (e.g. 2020W)'
            )

    def clean_subject(self):
        subject = self.cleaned_data['subject']
        if re.match(subject_validator, subject):
            return subject
        else:
            raise forms.ValidationError(
                'Please enter the subject of the course you are monitoring (e.g. PHYS)'
            )

    def clean_number(self):
        number = self.cleaned_data['number']
        if re.match(number_validator, number):
            return number
        else:
            raise forms.ValidationError(
                "Please enter the number of the course you are monitoring (e.g. '409B' in 'PHYS 409B 201')"
            )

    def clean_section(self):
        section = self.cleaned_data['section']
        if re.match(section_validator, section):
            return section
        else:
            raise forms.ValidationError(
                "Please enter the section of the course you are monitoring (e.g. '201' in 'PHYS 409B 201')"
            )

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
