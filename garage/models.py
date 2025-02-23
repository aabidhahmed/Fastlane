from django.db import models
from django.utils.timezone import now
from decimal import Decimal

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

    customer_name = models.CharField(max_length=255)
    vehicle_reg = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=[('Completed', 'Completed'), ('In Progress', 'In Progress'), ('Pending', 'Pending')],
        default='Pending'
    )
    date_in = models.DateTimeField(auto_now_add=True)

    # Store the payment status in the database
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default='not_paid'
    )

    def total_amount(self):
        """Calculate total cost of all services in this job."""
        return sum(service.total_cost() for service in self.services.all()) # Make sure 'services' is related_name


    def amount_paid(self):
        """ Sum of all payments made """
        return sum(payment.amount for payment in self.payments.all())

    def update_payment_status(self):
        """ Automatically update payment status based on payments received """
        total = self.total_amount()
        paid = self.amount_paid()
        
        #just a line to debug later ( might need to remove)
        print(f"DEBUG: Updating payment status for Job {self.id} | Total: {total} | Paid: {paid}")  # 🐛 Debugging print
        
        if paid >= total and total > 0:
            self.payment_status = "fully_paid"
        elif 0 < paid < total:
            self.payment_status = "partially_paid"
        else:
            self.payment_status = "not_paid"
        
        self.save(update_fields=["payment_status"])  # ✅ Efficient save



    def __str__(self):
        return f"{self.customer_name} - {self.vehicle_reg}"

class Service(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=255)
    part = models.ForeignKey(InventoryItem, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    labour_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def total_cost(self):
        """Returns total cost for this service (quantity * part price)."""
        if self.part:
            return self.quantity * self.part.price
        return 0
    
    @property
    def part_cost(self):
        """ Auto-calculate part cost based on inventory price and quantity """
        return (self.part.price * self.quantity) if self.part else Decimal('0.00')

    def __str__(self):
        return self.name

class Payment(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=now)

    def __str__(self):
        return f"Payment for {self.job.customer_name}: {self.amount}"
