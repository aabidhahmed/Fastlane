from django.utils.html import format_html
from django.contrib import admin, messages  # ✅ Import messages properly
from django.shortcuts import redirect  # ✅ Needed for filtering action redirects

from .models import Job, Service, Payment, InventoryItem


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1  
    readonly_fields = ('date',)


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 1
    fields = ('name', 'part', 'quantity', 'available_stock')  
    readonly_fields = ('available_stock',)

    def available_stock(self, obj):
        """Display available stock for the selected inventory item."""
        if obj.part:
            return format_html(
                '<span style="color:{};">{}</span>',
                "green" if obj.part.quantity > 5 else "red",
                f"{obj.part.quantity} left"
            )
        return "N/A"

    available_stock.short_description = "Stock Available"


class PaymentStatusFilter(admin.SimpleListFilter):
    """✅ Add a filter to make payment status filtering work properly"""
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
    list_display = (
        "customer_name", "vehicle_reg", "total_amount_display",
        "amount_paid_display", "payment_status_colored"  # ✅ Added colored status
    )
    list_filter = ('status', PaymentStatusFilter)  # ✅ Proper filtering
    search_fields = ('customer_name', 'vehicle_reg')
    ordering = ('-date_in',)
    inlines = [ServiceInline, PaymentInline]
    actions = ['mark_completed', 'mark_not_completed']

    def total_amount_display(self, obj):
        return f"${obj.total_amount():.2f}"
    total_amount_display.short_description = "Total Amount"

    def amount_paid_display(self, obj):
        return f"${obj.amount_paid():.2f}"
    amount_paid_display.short_description = "Amount Paid"

    def payment_status_colored(self, obj):
        """✅ Show colored status in the admin list"""
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


# ✅ Remove broken filtering actions (Use PaymentStatusFilter instead)


@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'price', 'last_updated')
    list_filter = ('category',)
    search_fields = ('name',)  # ✅ Removed 'supplier' (doesn't exist)
    ordering = ('-last_updated',)
