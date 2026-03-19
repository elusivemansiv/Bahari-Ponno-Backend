from rest_framework.routers import DefaultRouter
from .api_views import (
    ProductViewSet, CategoryViewSet, CartViewSet, OrderViewSet,
    HomeSliderViewSet, PromotionCardViewSet, ShippingConfigViewSet,
    ColorViewSet, SizeViewSet,
    SellerProductViewSet, SellerOrderViewSet, SellerStatsAPIView
)
from django.urls import path

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='api-products')
router.register(r'categories', CategoryViewSet, basename='api-categories')
router.register(r'colors', ColorViewSet, basename='api-colors')
router.register(r'sizes', SizeViewSet, basename='api-sizes')
router.register(r'cart', CartViewSet, basename='api-cart')
router.register(r'orders', OrderViewSet, basename='api-orders')
router.register(r'sliders', HomeSliderViewSet, basename='api-sliders')
router.register(r'promotions', PromotionCardViewSet, basename='api-promotions')
router.register(r'shipping-config', ShippingConfigViewSet, basename='api-shipping-config')
router.register(r'seller/products', SellerProductViewSet, basename='api-seller-products')
router.register(r'seller/orders', SellerOrderViewSet, basename='api-seller-orders')

urlpatterns = [
    path('seller/stats/', SellerStatsAPIView.as_view(), name='api-seller-stats'),
]
urlpatterns += router.urls
