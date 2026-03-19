from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Product, Category, Color, Size, ProductVariation, ProductImage, 
    ProductReview, Cart, CartItem, Order, OrderItem, HomeSlider, PromotionCard, ShippingConfig
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = '__all__'

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'color']

class ProductVariationSerializer(serializers.ModelSerializer):
    color = ColorSerializer(read_only=True)
    size = SizeSerializer(read_only=True)
    class Meta:
        model = ProductVariation
        fields = ['id', 'color', 'size', 'stock']

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = ProductReview
        fields = ['id', 'user_name', 'rating', 'comment', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    extra_images = ProductImageSerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    available_colors = serializers.SerializerMethodField()
    available_sizes = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('seller',)

    def get_available_colors(self, obj):
        colors = Color.objects.filter(productvariation__product=obj).distinct()
        return ColorSerializer(colors, many=True).data

    def get_available_sizes(self, obj):
        sizes = Size.objects.filter(productvariation__product=obj).distinct()
        return SizeSerializer(sizes, many=True).data

    def create(self, validated_data):
        # Handle many-to-many fields if they come as IDs
        colors_data = self.context['request'].data.getlist('colors')
        sizes_data = self.context['request'].data.getlist('sizes')
        
        # Remove them from validated_data if they are there as objects (DRF might have tried to parse them)
        validated_data.pop('colors', None)
        validated_data.pop('sizes', None)
        
        product = Product.objects.create(**validated_data)
        
        if colors_data:
            product.colors.set(colors_data)
        if sizes_data:
            product.sizes.set(sizes_data)

        # Handle Variations (JSON string)
        import json
        variations_json = self.context['request'].data.get('variations_data')
        if variations_json:
            try:
                variations_data = json.loads(variations_json)
                for var in variations_data:
                    ProductVariation.objects.create(
                        product=product,
                        color_id=var.get('color'),
                        size_id=var.get('size'),
                        stock=var.get('stock', 0)
                    )
            except Exception as e:
                print(f"Error parsing variations: {e}")

        # Handle Extra Images (Multiple files)
        extra_images = self.context['request'].FILES.getlist('extra_images')
        for img in extra_images:
            ProductImage.objects.create(product=product, image=img)

        # Handle Color-specific images
        for key, file in self.context['request'].FILES.items():
            if key.startswith('color_image_'):
                try:
                    color_id = int(key.replace('color_image_', ''))
                    ProductImage.objects.create(product=product, image=file, color_id=color_id)
                except:
                    pass

        return product

    def update(self, instance, validated_data):
        colors_data = self.context['request'].data.getlist('colors')
        sizes_data = self.context['request'].data.getlist('sizes')
        
        # Standard fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if colors_data:
            instance.colors.set(colors_data)
        if sizes_data:
            instance.sizes.set(sizes_data)

        # Handle Variations
        import json
        variations_json = self.context['request'].data.get('variations_data')
        if variations_json:
            try:
                variations_data = json.loads(variations_json)
                # For simplicity in this demo, we'll clear and recreate variations
                # A more robust solution would match by ID
                instance.variations.all().delete()
                for var in variations_data:
                    ProductVariation.objects.create(
                        product=instance,
                        color_id=var.get('color'),
                        size_id=var.get('size'),
                        stock=var.get('stock', 0)
                    )
            except Exception as e:
                print(f"Error parsing variations: {e}")

        # Handle Extra Images
        extra_images = self.context['request'].FILES.getlist('extra_images')
        if extra_images:
            # We add new ones, but maybe we should clear if needed. 
            # In a real app we'd have a separate endpoint for gallery management.
            for img in extra_images:
                ProductImage.objects.create(product=instance, image=img)

        # Handle Color-specific images
        for key, file in self.context['request'].FILES.items():
            if key.startswith('color_image_'):
                try:
                    color_id = int(key.replace('color_image_', ''))
                    # Replace old ones for this color if they exist
                    instance.extra_images.filter(color_id=color_id).delete()
                    ProductImage.objects.create(product=instance, image=file, color_id=color_id)
                except:
                    pass

        return instance

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    selected_image = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'color', 'size', 'subtotal', 'selected_image']

    def get_selected_image(self, obj):
        return obj.selected_image.url if obj.selected_image else None

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    selected_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'price', 'quantity', 'color', 'size', 'subtotal', 'selected_image']

    def get_selected_image(self, obj):
        return obj.selected_image.url if obj.selected_image else None

class SellerOrderItemSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='order.full_name', read_only=True)
    customer_email = serializers.CharField(source='order.email', read_only=True)
    customer_phone = serializers.CharField(source='order.phone', read_only=True)
    customer_address = serializers.CharField(source='order.address', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)
    created_at = serializers.DateTimeField(source='order.created_at', read_only=True)
    return_reason = serializers.CharField(source='order.return_reason', read_only=True)
    selected_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_name', 'price', 'quantity', 
            'color', 'size', 'subtotal', 'customer_name', 'customer_email', 
            'customer_phone', 'customer_address', 'order_status', 'return_reason', 'created_at',
            'selected_image'
        ]

    def get_selected_image(self, obj):
        return obj.selected_image.url if obj.selected_image else None

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    final_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'

class HomeSliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeSlider
        fields = '__all__'

class PromotionCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionCard
        fields = '__all__'

class ShippingConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingConfig
        fields = '__all__'
