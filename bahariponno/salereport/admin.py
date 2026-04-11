from django.contrib import admin
from django.db.models import Sum, F, Count, Q, Avg
from django.template.response import TemplateResponse
from .models import PlatformSalesReport, ProductSalesReport

@admin.register(PlatformSalesReport)
class PlatformSalesReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'full_name', 'total_price', 'status', 'payment_method')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('full_name', 'email')
    date_hierarchy = 'created_at'
    change_list_template = 'admin/salereport/change_list.html'
    
    def has_add_permission(self, request):
        return False

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
            
        metrics = {
            'total_sales_value': qs.filter(status='delivered').aggregate(total=Sum('total_price'))['total'] or 0,
            'delivered_orders_count': qs.filter(status='delivered').count(),
            'avg_order_value': qs.filter(status='delivered').aggregate(avg=Avg('total_price'))['avg'] or 0,
        }
        
        response.context_data['summary_metrics'] = metrics
        return response


@admin.register(ProductSalesReport)
class ProductSalesReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'get_sales_count', 'get_total_revenue', 'total_stock')
    list_filter = ('category',)
    search_fields = ('name',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            _sales_count=Sum('orderitem__quantity', filter=Q(orderitem__order__status='delivered')),
            _total_revenue=Sum(F('orderitem__quantity') * F('orderitem__price'), filter=Q(orderitem__order__status='delivered'))
        )
        return qs

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

    def get_sales_count(self, obj):
        return obj._sales_count or 0
    get_sales_count.short_description = 'Sales Count'
    get_sales_count.admin_order_field = '_sales_count'

    def get_total_revenue(self, obj):
        return f"৳ {obj._total_revenue or 0}"
    get_total_revenue.short_description = 'Revenue Generated'
    get_total_revenue.admin_order_field = '_total_revenue'
