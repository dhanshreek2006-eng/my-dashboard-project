from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name    
     
class Supplier(models.Model):
     name=models.CharField(max_length=100)
     phone=models.BigIntegerField(max_length=10)
     email=models.EmailField()
     address=models.CharField()

     def __str__(self):
         return self.name

class Product(models.Model):
    name=models.CharField(max_length=100)
    Category=models.ForeignKey(Category,on_delete=models.CASCADE)
    Supplier=models.ForeignKey(Supplier,on_delete=models.CASCADE)
    purchase_price=models.DecimalField(max_digits=10,decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_stock=models.IntegerField(default=0)
    minimum_stock=models.IntegerField(default=5)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Purchase #{self.id}"

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    
class Sale(models.Model):
    sold_by = models.ForeignKey(User, on_delete=models.CASCADE)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Sale #{self.id}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"    


class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return self.user.username    