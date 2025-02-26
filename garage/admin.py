from django.utils.html import format_html
from django.contrib import admin
from django.utils import timezone
from django import forms
from django.forms.widgets import DateTimeInput

from .models import Job, Service, Payment, InventoryItem
from datetime import datetime

class CustomDateTimeInput(DateTimeInput):
    input_type = 'datetime-local'
    def __init__(self, **kwargs):
        kwargs.setdefault('format', '%Y-%m-%dT%H:%M')
        super().__init__(**kwargs)

    def format_value(self, value):
        if value is None:
            return ''
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime(self.attrs.get('format', '%Y-%m-%dT%H:%M'))


class JobAdminForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = '__all__'

    def clean_date_in(self):
        date_in = self.cleaned_data.get('date_in')

        if isinstance(date_in, str):  
            try:
                date_in = datetime.fromisoformat(date_in)
            except ValueError:
                raise forms.ValidationError("Invalid date format. Please enter a valid date.")

        if date_in and timezone.is_naive(date_in):
            date_in = timezone.make_aware(date_in, timezone.get_current_timezone())

        return date_in


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1  
    readonly_fields = ('date', 'total_amount_due')

    def total_amount_due(self, obj):
        """Displays the total amount still due for the job."""
        if obj and obj.job:
            total_due = obj.job.total_amount() - obj.job.amount_paid()
            return f"${total_due:.2f}" if total_due > 0 else "$0.00"
        return "-"

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
            return format_html(
                '<span style="color:{};">{} left</span>',
                color,
                obj.part.quantity
            )
        return "N/A"

    available_stock.short_description = "Stock Available"


class PaymentStatusFilter(admin.SimpleListFilter):
    title = 'Payment Status'
    parameter_name = 'payment_status'

    def lookups(self, request, model_admin):
        return [
            ('fully_paid', 'Fully Paid'),
            ('partially_paid', 'Partially Paid'),
            ('not_paid', 'Not Paid'),
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(payment_status=self.value())
        return queryset


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    form = JobAdminForm
    list_display = ("customer_name", "vehicle_reg", "date_in", "total_amount_display", "amount_paid_display", "payment_status_colored")
    list_filter = ('status', PaymentStatusFilter)
    search_fields = ('customer_name', 'vehicle_reg')
    ordering = ('-date_in',)
    inlines = [ServiceInline, PaymentInline]
    fields = ('customer_name', 'vehicle_reg', 'status', 'date_in')

    def total_amount_display(self, obj):
        return f"${obj.total_amount():.2f}"
    total_amount_display.short_description = "Total Amount"

    def amount_paid_display(self, obj):
        return f"${obj.amount_paid():.2f}"
    amount_paid_display.short_description = "Amount Paid"

    def payment_status_colored(self, obj):
        colors = {
            "fully_paid": "green",
            "partially_paid": "orange",
            "not_paid": "red",
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.payment_status, "black"),
            obj.get_payment_status_display()
        )
    payment_status_colored.short_description = "Payment Status"


@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'price', 'last_updated')
    list_filter = ('category',)
    search_fields = ('name',)
    ordering = ('-last_updated',)
