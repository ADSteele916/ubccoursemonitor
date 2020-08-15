from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="courses-home"),
    path("faq/", views.faq, name="courses-faq"),
    path("about/", views.about, name="courses-about"),
    path("courses/", views.courses, name="courses-list"),
]
