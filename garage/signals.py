import os
import tempfile
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.db.models.signals import pre_delete, pre_save,post_save,post_delete
from django.dispatch import receiver
from .models import Job, Service,Payment

def print_jobsheet(request, job_id):
    """
    Generate a PDF jobsheet for a given job.
    """
    job = Job.objects.get(id=job_id)
    html_string = render_to_string('jobsheet.html', {'job': job})
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
        pdf_path = temp_pdf.name  
    
    try:
        HTML(string=html_string).write_pdf(pdf_path)
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="jobsheet_{job_id}.pdf"'
        return response
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


@receiver(pre_save, sender=Service)
def update_inventory_on_save(sender, instance, **kwargs):
    if instance.pk:
        old_service = Service.objects.get(pk=instance.pk)
        if old_service.part and old_service.part != instance.part:
            old_service.part.quantity += old_service.quantity
            old_service.part.save()

    if instance.part:
        if instance.quantity > instance.part.quantity:
            print(f"⚠ Warning: Not enough stock for '{instance.part.name}'. Requested: {instance.quantity}, Available: {instance.part.quantity}.")
            instance.quantity = instance.part.quantity  # ✅ Set it to max available stock
        
        instance.part.quantity -= instance.quantity
        instance.part.save()

@receiver(pre_delete, sender=Service)
def restore_inventory_on_delete(sender, instance, **kwargs):
    if instance.part:
        instance.part.quantity += instance.quantity
        instance.part.save()


@receiver(post_save, sender=Payment)
@receiver(post_delete, sender=Payment)
def update_job_payment_status(sender, instance, **kwargs):
    """ Update the payment status of a job when payments are added or deleted. """
    print(f"DEBUG: Payment signal triggered for Job {instance.job.id}")  # 🐛 Debugging print
    job = instance.job
    job.update_payment_status()
