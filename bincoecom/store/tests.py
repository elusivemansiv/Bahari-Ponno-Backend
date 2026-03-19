from django.test import TestCase
from django.contrib.auth.models import User
from .models import Product, Order, OrderItem, ProductVariation, Category, Size
from accounts.models import UserProfile

class ReturnProcessTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        # self.profile = UserProfile.objects.create(user=self.user) # Handled by signal
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            price=100.00,
            stock=10,
            category=self.category
        )
        self.order = Order.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            phone='123456789',
            address='Test Address',
            city='Test City',
            status='delivered'
        )
        self.item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name='Test Product',
            price=100.00,
            quantity=2
        )

    def test_stock_restoration_on_returned_status(self):
        # Initial stock was 10, but order creation doesn't automatically decrease stock in local model tests 
        # unless specifically called. Let's manually decrease it to simulate order placement.
        self.product.stock -= 2
        self.product.save()
        self.assertEqual(self.product.stock, 8)

        # Update status to returned
        self.order.status = 'returned'
        self.order.save()

        # Refresh from DB
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 10, "Stock should be restored to 10")

    def test_return_requested_status_change(self):
        self.order.status = 'return_requested'
        self.order.return_reason = 'Defective'
        self.order.save()
        
        self.assertEqual(self.order.status, 'return_requested')
        self.assertEqual(self.order.return_reason, 'Defective')

    def test_partial_variation_stock(self):
        # Create a product with only size variations
        size_product = Product.objects.create(
            name='Size only product',
            price=200,
            stock=10,
            category=self.category
        )
        xl_size = Size.objects.create(name='XL')
        variation = ProductVariation.objects.create(
            product=size_product,
            size=xl_size,
            stock=5
        )
        
        # Test finding variation with null color
        from django.db.models import Q
        q = Q(product=size_product) & Q(size__name='XL') & Q(color__isnull=True)
        found_v = ProductVariation.objects.filter(q).first()
        self.assertEqual(found_v, variation)
        
        # Test stock restoration via Order.save
        order = Order.objects.create(user=self.user, status='delivered')
        OrderItem.objects.create(
            order=order, product=size_product, quantity=2, size='XL',
            price=200, product_name='Size only product'
        )
        
        # Manually decrease stock to simulate
        variation.stock -= 2
        variation.save()
        self.assertEqual(variation.stock, 3)
        
        # Restore stock
        order.status = 'returned'
        order.save()
        
        variation.refresh_from_db()
        self.assertEqual(variation.stock, 5)

    def test_no_variation_stock(self):
        # Product with no variations
        simple_product = Product.objects.create(
            name='Simple product',
            price=50,
            stock=10,
            category=self.category
        )
        
        order = Order.objects.create(user=self.user, status='delivered')
        OrderItem.objects.create(
            order=order, product=simple_product, quantity=3,
            price=50, product_name='Simple product'
        )
        
        # Manually decrease
        simple_product.stock -= 3
        simple_product.save()
        
        # Restore
        order.status = 'returned'
        order.save()
        
        simple_product.refresh_from_db()
        self.assertEqual(simple_product.stock, 10)
