from django.contrib import admin
from .models import(
    Category,
    Supplier,
    Product,
    Purchase,
    PurchaseItem,
    Sale,
    SaleItem, 
    Profile
)
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(Purchase)
admin.site.register(PurchaseItem)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(Profile)