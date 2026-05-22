from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Category, Product, ProductImage, ProductReview,
    Cart, CartItem, Coupon, Order, OrderItem, Wishlist,
    Color, Size, ProductVariation, HomeSlider, PromotionCard,
    ShippingConfig, SiteSetting
)


@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')


@admin.register(PromotionCard)
class PromotionCardAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 6px; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);" />', obj.image.url)
        return mark_safe('<div style="width: 48px; height: 48px; background-color: #f3f4f6; border-radius: 6px; border: 1px dashed #d1d5db; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size: 10px; font-weight: 500; text-transform: uppercase;">No Img</div>')
    image_preview.short_description = 'Image'


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')


@admin.register(Size)
class QuantityAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1
    fields = ('size', 'color', 'price', 'stock')
    verbose_name = "Quantity Variation"
    verbose_name_plural = "Quantity Variations (Price & Stock per quantity)"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'name', 'category', 'price', 'total_stock', 'is_featured', 'is_active', 'created_at')
    list_filter = ('is_featured', 'is_active', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariationInline]
    readonly_fields = ('stock', 'total_stock')
    list_editable = ('is_featured', 'is_active')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 6px; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1);" />', obj.image.url)
        return mark_safe('<div style="width: 48px; height: 48px; background-color: #f3f4f6; border-radius: 6px; border: 1px dashed #d1d5db; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size: 10px; font-weight: 500; text-transform: uppercase;">No Img</div>')
    image_preview.short_description = 'Image'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'category', 'description', 'image', 'is_featured', 'is_active')
        }),
        ('Base Price (default price shown if no quantity selected)', {
            'fields': ('price', 'discount_price'),
            'description': 'This is the default price shown on the product card. Actual prices per quantity are set in the "Quantity Variations" section below.'
        }),
        ('Stock (auto-calculated from variations)', {
            'fields': ('stock', 'total_stock'),
        }),
        ('Advanced (optional)', {
            'classes': ('collapse',),
            'fields': ('colors', 'sizes'),
            'description': 'Colors and Quantities linked to this product. Quantities are managed via the Variations section below.'
        }),
    )


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating',)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    inlines = [CartItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from', 'valid_to', 'is_active', 'used_count', 'max_uses')
    list_editable = ('is_active',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'items_preview', 'user_link', 'full_name', 'total_price', 'discount_amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('user__username', 'full_name', 'email')
    list_editable = ('status',)
    inlines = [OrderItemInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user').prefetch_related('items', 'items__product')

    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}" style="font-weight: 600; color: #47bac1; text-decoration: none;">{}</a>', url, obj.user.username)
        return mark_safe('<span style="color: #9ca3af; font-style: italic;">Guest</span>')
    user_link.short_description = 'User'

    def items_preview(self, obj):
        items = obj.items.all()
        if not items.exists():
            return mark_safe('<span style="color: #9ca3af; font-style: italic;">No items</span>')
        
        html_parts = ['<div style="display: flex; flex-direction: column; gap: 6px; min-width: 320px; padding: 4px 0;">']
        for item in items:
            img_url = None
            if item.product and item.product.image:
                color_img = item.product.get_image_for_color(item.color)
                if color_img:
                    img_url = color_img.url
                else:
                    img_url = item.product.image.url
            
            if img_url:
                img_html = format_html('<img src="{}" style="width: 28px; height: 28px; object-fit: cover; border-radius: 4px; border: 1px solid #e5e7eb; flex-shrink: 0;" />', img_url)
            else:
                img_html = mark_safe('<div style="width: 28px; height: 28px; background-color: #f3f4f6; border-radius: 4px; border: 1px dashed #d1d5db; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size: 8px; font-weight: bold; flex-shrink: 0;">N/A</div>')
            
            # Variations text
            var_parts = []
            if item.color:
                var_parts.append(item.color)
            if item.size:
                var_parts.append(item.size)
            var_str = f" ({', '.join(var_parts)})" if var_parts else ""

            html_parts.append(
                format_html(
                    '<div style="display: flex; align-items: center; gap: 8px; font-size: 12px; line-height: 1.2;">'
                    '{}'
                    '<div style="display: flex; flex-direction: column; flex-grow: 1; min-width: 0;">'
                    '<span style="font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{}{}">{}{}</span>'
                    '<span style="font-size: 11px; color: #64748b;">{} × {}</span>'
                    '</div>'
                    '<span style="font-weight: 700; color: #0f172a; text-align: right; min-width: 60px;">{}</span>'
                    '</div>',
                    img_html,
                    item.product_name, var_str,
                    item.product_name, var_str,
                    item.quantity, item.price,
                    item.subtotal
                )
            )
            
        html_parts.append('</div>')
        return mark_safe(''.join(html_parts))
    items_preview.short_description = 'Items Detail'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('products',)


@admin.register(ShippingConfig)
class ShippingConfigAdmin(admin.ModelAdmin):
    list_display = ('shipping_charge', 'free_shipping_threshold', 'is_active', 'updated_at')
    
    def has_add_permission(self, request):
        # Prevent adding more than one config
        return not ShippingConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the config
        return False


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'logo_preview', 'favicon_preview', 'updated_at')
    readonly_fields = ('logo_preview_field', 'favicon_preview_field')

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 40px; border-radius: 4px;" />', obj.logo.url)
        return mark_safe('<span style="color: #9ca3af; font-style: italic;">No Logo</span>')
    logo_preview.short_description = 'Logo'

    def favicon_preview(self, obj):
        if obj.favicon:
            return format_html('<img src="{}" style="max-height: 32px; width: 32px; object-fit: contain;" />', obj.favicon.url)
        return mark_safe('<span style="color: #9ca3af; font-style: italic;">No Favicon</span>')
    favicon_preview.short_description = 'Favicon'

    def logo_preview_field(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 100px; border-radius: 6px; border: 1px solid #ddd; padding: 4px;" />', obj.logo.url)
        return "No logo uploaded yet."
    logo_preview_field.short_description = 'Logo Preview'

    def favicon_preview_field(self, obj):
        if obj.favicon:
            return format_html('<img src="{}" style="max-height: 48px; width: 48px; object-fit: contain; border: 1px solid #ddd; padding: 4px;" />', obj.favicon.url)
        return "No favicon uploaded yet."
    favicon_preview_field.short_description = 'Favicon Preview'

    fieldsets = (
        ('General Settings', {
            'fields': ('site_name',)
        }),
        ('Branding Assets', {
            'fields': ('logo', 'logo_preview_field', 'favicon', 'favicon_preview_field')
        }),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# Global Admin Customizations for Bahari Ponno Portal
admin.site.site_header = "Bahari Ponno"
admin.site.site_title = "Bahari Ponno Admin Portal"
admin.site.index_title = "Manage your products, orders, and promotions"

