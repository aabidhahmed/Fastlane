from django.urls import path
from .views import home, print_jobsheet

urlpatterns = [
    path("", home, name="home"),
    path("print-jobsheet/<int:job_id>/", print_jobsheet, name="print-jobsheet"),
]
