from django.utils.html import format_html
from django.contrib import admin
from django.utils import timezone
from django import forms
from django.forms.widgets import DateTimeInput
from django.urls import reverse
from django.shortcuts import redirect

from .models import Job, Service, Payment, InventoryItem


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1  
    readonly_fields = ('date', 'total_amount_due')

    def total_amount_due(self, obj):
        """Show total amount due below the payment field."""
        if obj and obj.job:
            total_due = obj.job.total_amount() - obj.job.amount_paid()
            return format_html(
                '<span style="color: blue; font-weight: bold;">Total amount due: ${:.2f}</span>',
                total_due
            )
        return "N/A"
    
    total_amount_due.short_description = "Total Amount Due"


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    fields = ('name', 'part', 'quantity', 'available_stock')  
    readonly_fields = ('available_stock',)

    def available_stock(self, obj):
        """Display available stock for the selected inventory item."""
        if obj.part:
            color = "green" if obj.part.quantity > 5 else "red"
            return format_html('<span style="color:{};">{} left</span>', color, obj.part.quantity)
        return "N/A"

    available_stock.short_description = "Stock Available"


def print_jobsheet(obj):
    """Generate a print button in the admin panel."""
    return format_html(
        '<a href="{}" class="button" target="_blank">🖨 Print Job Sheet</a>',
        reverse('print_jobsheet', args=[obj.pk])
    )
print_jobsheet.short_description = "Print Jobsheet"


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name", "vehicle_reg", "date_in", "status", "payment_status_colored", 
        "total_amount_display", "amount_paid_display", print_jobsheet
    )
    search_fields = ('customer_name', 'vehicle_reg')
    ordering = ('-date_in',)
    list_filter = ('status', 'payment_status')  # Filters for completion & payment status
    inlines = [ServiceInline, PaymentInline]

    def print_job(self, obj):
        url = reverse('print_jobsheet', args=[obj.id])
        return format_html('<a href="{}" target="_blank" class="button">🖨️ Print</a>', url)

    print_job.short_description = "Print Job Sheet"
    
    def total_amount_display(self, obj):
        return f"${obj.total_amount():.2f}"
    total_amount_display.short_description = "Total Amount"

    def amount_paid_display(self, obj):
        return f"${obj.amount_paid():.2f}"
    amount_paid_display.short_description = "Amount Paid"

    def payment_status_colored(self, obj):
        colors = {"fully_paid": "green", "partially_paid": "orange", "not_paid": "red"}
        return format_html('<span style="color:{}; font-weight: bold;">{}</span>', colors.get(obj.payment_status, "black"), obj.get_payment_status_display())
    payment_status_colored.short_description = "Payment Status"


@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'price', 'last_updated')
    search_fields = ('name', 'category')
    ordering = ('-last_updated',)
