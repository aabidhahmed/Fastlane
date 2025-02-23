from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
import tempfile
import os
from .models import Job  

def home(request):
    return render(request, "index.html")


#This part is confirmed yet, we can remove it later

WEASYPRINT_TEMP_DIR = getattr(settings, 'WEASYPRINT_TEMP_DIR', tempfile.gettempdir())


def print_jobsheet(request, job_id):
    """
    Generate a PDF jobsheet for a given job.
    """
    # Fetch job data from the database (assuming Job model exists)
    job = Job.objects.get(id=job_id)
    
    # Render the HTML template
    html_string = render_to_string('jobsheet.html', {'job': job})
    
    # Use a temporary file with proper permissions
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=WEASYPRINT_TEMP_DIR, mode='wb') as temp_pdf:
        pdf_path = temp_pdf.name  # Get the temp file path

    try:
        # Generate PDF and write to temp file
        HTML(string=html_string).write_pdf(pdf_path)
        
        # Ensure file is readable
        os.chmod(pdf_path, 0o644)  # Read & write for owner, read for others

        # Read the generated PDF
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Create response with the PDF
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="jobsheet_{job_id}.pdf"'
        return response

    finally:
        # Clean up temp file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)