import os
import tempfile
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Job
from django.shortcuts import render



def home(request):
    return render(request, "index.html")




WEASYPRINT_TEMP_DIR = getattr(settings, 'WEASYPRINT_TEMP_DIR', tempfile.gettempdir())

def print_jobsheet(request, job_id):
    job = Job.objects.get(id=job_id)
    html_string = render_to_string('jobsheet.html', {'job': job})

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=WEASYPRINT_TEMP_DIR, mode='wb') as temp_pdf:
        pdf_path = temp_pdf.name

    try:
        HTML(string=html_string).write_pdf(pdf_path)
        os.chmod(pdf_path, 0o644)

        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="jobsheet_{job_id}.pdf"'
        return response

    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
