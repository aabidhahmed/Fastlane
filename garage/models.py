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
        max_length=13,
        validators=[
            RegexValidator(
                regex=r"^[A-Z]{2}-[0-7][0-9]-[A-Z]{2}-\d{4}₹",
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

    def total_amount(self):
        return sum(service.total_cost() for service in self.services.all())

    def amount_paid(self):
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
        return (self.part.price * self.quantity if self.part else Decimal('0.00')) + self.labour_cost

    def __str__(self):
        return self.name


class Payment(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='payments')  
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=now)

    def __str__(self):
        return f"Payment for {self.job.customer_name}: {self.amount}"
