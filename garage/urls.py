from django.urls import path
from .views import home, print_jobsheet

urlpatterns = [
    path("", home, name="home"),
    path("print-jobsheet/<int:job_id>/", print_jobsheet, name="print_jobsheet"),  # Fix the name to match reverse()
]
#http://127.0.0.1:8000/print-jobsheet/1/