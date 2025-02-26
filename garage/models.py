from django.db import models
from django.utils.timezone import now
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re


class InventoryItem(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price per unit
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('fully_paid', 'Fully Paid'),
        ('partially_paid', 'Partially Paid'),
        ('not_paid', 'Not Paid'),
    ]

    vehicle_reg = models.CharField(
        max_length=13,  # Length of "XX-00-XX-0000" = 13
        validators=[
            RegexValidator(
                regex=r"^[A-Z]{2}-[0-7][0-9]-[A-Z]{2}-\d{4}$",
                message="Enter a valid vehicle registration number (e.g., KA-05-AJ-6807).",
                code="invalid_vehicle_reg"
            )
        ],
        help_text="Format: XX-00-XX-0000 (e.g., KA-05-AJ-6807)"
    )

    customer_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=[('Completed', 'Completed'), ('In Progress', 'In Progress'), ('Pending', 'Pending')],
        default='Pending'
    )
    job_date = models.DateField(default=now)
    date_in = models.DateTimeField(default=now)

    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='not_paid'
    )

    def clean(self):
        """Auto-format vehicle registration before saving."""
        raw_value = self.vehicle_reg.upper().replace(" ", "").replace("-", "")
        pattern = r"^([A-Z]{2})([0-7][0-9])([A-Z]{2})(\d{4})$"
        match = re.match(pattern, raw_value)

        if match:
            self.vehicle_reg = f"{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}"
        else:
            raise ValidationError("Invalid vehicle registration format. Expected format: KA-05-AJ-6807")

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure validation runs before saving
        super().save(*args, **kwargs)

    def total_amount(self):
        """Calculate total cost of all services in this job."""
        if not self.pk:  # If the Job is not saved yet
            return Decimal('0.00')

        return sum(service.total_cost() for service in self.services.all())

    def amount_paid(self):
        """Sum of all payments made."""
        if not self.pk:
            return Decimal('0.00')

        return sum(payment.amount for payment in self.payments.all())

    def update_payment_status(self):
        total = self.total_amount()
        paid = self.amount_paid()

        new_status = (
            "fully_paid" if paid >= total and total > 0 else
            "partially_paid" if 0 < paid < total else
            "not_paid"
        )

        if self.payment_status != new_status:
            self.payment_status = new_status
            self.save(update_fields=["payment_status"])

    def __str__(self):
        return f"{self.customer_name} - {self.vehicle_reg}"


class Service(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='services')  
    name = models.CharField(max_length=255)
    part = models.ForeignKey(InventoryItem, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    labour_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def total_cost(self):
        """Returns total cost for this service (labour cost + (quantity * part price))."""
        return (self.part.price * self.quantity if self.part else Decimal('0.00')) + self.labour_cost

    def __str__(self):
        return self.name


class Payment(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='payments')  
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=now)

    def clean(self):
        """Ensure the customer doesn't overpay"""
        if not self.job.pk:
            return

        total_due = self.job.total_amount() - self.job.amount_paid()
        
        if total_due <= 0:
            raise ValidationError("Cannot add payment when no amount is due.")

        if self.amount > total_due:
            raise ValidationError(f"Payment exceeds total due: {total_due}")

    def __str__(self):
        return f"Payment for {self.job.customer_name}: {self.amount}"
