from rest_framework.routers import DefaultRouter
from .api_views import (
    ProductViewSet, CategoryViewSet, CartViewSet, OrderViewSet,
    HomeSliderViewSet, PromotionCardViewSet, ShippingConfigViewSet,
    ColorViewSet, QuantityViewSet, SiteSettingViewSet
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='api-products')
router.register(r'categories', CategoryViewSet, basename='api-categories')
router.register(r'colors', ColorViewSet, basename='api-colors')
router.register(r'quantities', QuantityViewSet, basename='api-quantities')
router.register(r'cart', CartViewSet, basename='api-cart')
router.register(r'orders', OrderViewSet, basename='api-orders')
router.register(r'sliders', HomeSliderViewSet, basename='api-sliders')
router.register(r'promotions', PromotionCardViewSet, basename='api-promotions')
router.register(r'shipping-config', ShippingConfigViewSet, basename='api-shipping-config')
router.register(r'site-settings', SiteSettingViewSet, basename='api-site-settings')

urlpatterns = router.urls
