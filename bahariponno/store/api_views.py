from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, F, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    Product, Category, Color, Size, Cart, CartItem, Order, OrderItem, 
    HomeSlider, PromotionCard, ShippingConfig, ProductVariation, ProductImage
)
from .serializers import (
    ProductSerializer, CategorySerializer, ColorSerializer, QuantitySerializer,
    CartSerializer, CartItemSerializer, OrderSerializer, HomeSliderSerializer,
    PromotionCardSerializer, ShippingConfigSerializer
)




class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        query = self.request.query_params.get('q', None)
        is_featured = self.request.query_params.get('featured', None)
        is_deal = self.request.query_params.get('deal', None)

        if category:
            queryset = queryset.filter(category__slug=category)
        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if is_featured:
            queryset = queryset.filter(is_featured=True)
        if is_deal:
            queryset = queryset.filter(discount_price__isnull=False)

        return queryset


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        color = request.data.get('color', '')
        size = request.data.get('size', '')

        product = get_object_or_404(Product, id=product_id)
        
        # Stock Check Logic
        requested_total = quantity
        existing_item = CartItem.objects.filter(cart=cart, product=product, color=color, size=size).first()
        if existing_item:
            requested_total += existing_item.quantity

        if product.variations.exists():
            q = Q(product=product)
            if color:
                q &= Q(color__name=color)
            else:
                q &= Q(color__isnull=True)
            if size:
                q &= Q(size__name=size)
            else:
                q &= Q(size__isnull=True)
            variation = product.variations.filter(q).first()
            if not variation:
                return Response({'error': 'Selected variation does not exist'}, status=status.HTTP_400_BAD_REQUEST)
            if variation.stock < requested_total:
                return Response({'error': 'stock out for that particular item'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            if product.stock < requested_total:
                return Response({'error': 'stock out for that particular item'}, status=status.HTTP_400_BAD_REQUEST)

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, color=color, size=size
        )
        if created:
            item.quantity = quantity
        else:
            item.quantity += quantity
        item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        cart = self.get_object()
        item_id = request.data.get('item_id')
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def update_item(self, request):
        cart = self.get_object()
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))
        
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        if quantity <= 0:
            item.delete()
        else:
            # Stock Check
            product = item.product
            if product.variations.exists():
                q = Q(product=product)
                if item.color:
                    q &= Q(color__name=item.color)
                else:
                    q &= Q(color__isnull=True)
                if item.size:
                    q &= Q(size__name=item.size)
                else:
                    q &= Q(size__isnull=True)
                variation = product.variations.filter(q).first()
                if variation and variation.stock < quantity:
                    return Response({'error': 'stock out for that particular item'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if product.stock < quantity:
                    return Response({'error': 'stock out for that particular item'}, status=status.HTTP_400_BAD_REQUEST)

            item.quantity = quantity
            item.save()
            
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        if not items.exists():
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        order_data = request.data
        order = Order.objects.create(
            user=request.user,
            full_name=order_data.get('full_name'),
            email=order_data.get('email'),
            phone=order_data.get('phone'),
            address=order_data.get('address'),
            city=order_data.get('city'),
            postal_code=order_data.get('postal_code', ''),
            total_price=cart.total,
            payment_method=order_data.get('payment_method', 'cod')
        )

        for item in items:
            OrderItem.objects.create(
                order=order, product=item.product, product_name=item.product.name,
                price=item.effective_price, quantity=item.quantity,
                color=item.color, size=item.size
            )
            # Update stock correctly (with variations)
            q = Q(product=item.product)
            if item.color:
                q &= Q(color__name=item.color)
            else:
                q &= Q(color__isnull=True)
            if item.size:
                q &= Q(size__name=item.size)
            else:
                q &= Q(size__isnull=True)
            
            variation = ProductVariation.objects.filter(q).first()
            
            if variation:
                variation.stock -= item.quantity
                variation.save(update_fields=['stock'])
            else:
                item.product.stock -= item.quantity
                item.product.save(update_fields=['stock'])

        cart.items.all().delete()
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def request_return(self, request, pk=None):
        order = self.get_object()
        if order.status not in ['shipped', 'delivered']:
            return Response({'error': 'Only shipped or delivered orders can be returned'}, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason')
        if not reason:
            return Response({'error': 'Reason is required for return request'}, status=status.HTTP_400_BAD_REQUEST)
            
        order.status = 'return_requested'
        order.return_reason = reason
        order.save()
        
        return Response({'status': 'Return requested successfully'})


class HomeSliderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HomeSlider.objects.filter(is_active=True).order_by('order')
    serializer_class = HomeSliderSerializer
    permission_classes = [permissions.AllowAny]


class PromotionCardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PromotionCard.objects.filter(is_active=True).order_by('order')
    serializer_class = PromotionCardSerializer
    permission_classes = [permissions.AllowAny]


class ShippingConfigViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShippingConfig.objects.all()
    serializer_class = ShippingConfigSerializer
    permission_classes = [permissions.AllowAny]


class ColorViewSet(viewsets.ModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [permissions.AllowAny]


class QuantityViewSet(viewsets.ModelViewSet):
    queryset = Size.objects.all()
    serializer_class = QuantitySerializer
    permission_classes = [permissions.AllowAny]
