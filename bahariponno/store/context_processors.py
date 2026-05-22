from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from .models import Cart, Category, ShippingConfig, Order, OrderItem, Product, SiteSetting


def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.items.count()
        except Cart.DoesNotExist:
            count = 0
    return {'cart_count': count}


def categories(request):
    return {'all_categories': Category.objects.all()}


def shipping_config(request):
    return {'shipping_conf': ShippingConfig.get_config()}


def admin_dashboard_stats(request):
    if not request.path.startswith('/admin/'):
        return {}
    if not request.user or not request.user.is_authenticated or not request.user.is_staff:
        return {}
    
    try:
        # Calculate stats
        total_orders = Order.objects.count()
        total_sales = Order.objects.filter(status='delivered').aggregate(total=Sum('total_price'))['total'] or 0
        total_revenue = Order.objects.exclude(status='cancelled').aggregate(total=Sum('total_price'))['total'] or 0
        pending_orders_count = Order.objects.filter(status='pending').count()
        
        # Top Selling Products (ordered by sum of quantity sold)
        top_selling_items = OrderItem.objects.filter(order__status='delivered').values(
            'product__id', 'product_name', 'product__image', 'price'
        ).annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        ).order_by('-total_qty')[:5]
        
        # Format top selling items with image url
        top_selling = []
        for item in top_selling_items:
            img_url = ''
            if item['product__image']:
                img_url = f"/media/{item['product__image']}"
            top_selling.append({
                'id': item['product__id'],
                'name': item['product_name'],
                'image': img_url,
                'price': float(item['price']),
                'total_qty': item['total_qty'],
                'total_revenue': float(item['total_revenue'])
            })
        
        # Recent pending orders
        recent_pending = Order.objects.filter(status='pending').order_by('-created_at')[:5]
        
        # Graph data: last 7 days sales
        today = timezone.now().date()
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        chart_labels = [day.strftime('%b %d') for day in days]
        
        chart_sales = []
        for day in days:
            sales_sum = Order.objects.filter(
                created_at__date=day,
                status='delivered'
            ).aggregate(total=Sum('total_price'))['total'] or 0
            chart_sales.append(float(sales_sum))
            
        return {
            'admin_stats': {
                'total_orders': total_orders,
                'total_sales': float(total_sales),
                'total_revenue': float(total_revenue),
                'pending_orders': pending_orders_count,
                'top_selling': top_selling,
                'recent_pending': recent_pending,
                'chart_labels': chart_labels,
                'chart_sales': chart_sales,
            }
        }
    except Exception as e:
        # Prevent admin from crashing if models/tables aren't fully migrated or setup
        return {
            'admin_stats': {
                'error': str(e),
                'total_orders': 0,
                'total_sales': 0.0,
                'total_revenue': 0.0,
                'pending_orders': 0,
                'top_selling': [],
                'recent_pending': [],
                'chart_labels': [],
                'chart_sales': [],
            }
        }


def site_settings(request):
    try:
        return {'site_settings': SiteSetting.get_setting()}
    except Exception:
        return {'site_settings': None}

