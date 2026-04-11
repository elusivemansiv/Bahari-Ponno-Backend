from django.db import models
from store.models import Order, Product
from django.contrib.auth.models import User

class PlatformSalesReport(Order):
    class Meta:
        proxy = True
        app_label = 'salereport'
        verbose_name = 'Overall Sale'
        verbose_name_plural = 'Overall Sales Reports'


class ProductSalesReport(Product):
    class Meta:
        proxy = True
        app_label = 'salereport'
        verbose_name = 'Product Sale'
        verbose_name_plural = 'Product Sales Reports'
