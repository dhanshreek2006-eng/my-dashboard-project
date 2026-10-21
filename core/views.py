from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView

from .models import Category, Supplier, Product, Purchase, PurchaseItem
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Sale, SaleItem

from django.utils import timezone
from django.db.models import Sum
from .models import Product, Sale, SaleItem

import pandas as pd
import numpy as np

# Home page
def home(request):
    return render(request, "home.html")


# Base page
def base(request):
    return render(request, "base.html")


# Dashboard
def dashboard(request):
    today = timezone.localdate()

    total_products = Product.objects.count()

    total_stock = Product.objects.aggregate(
        total=Sum("current_stock")
    )["total"] or 0

    today_sales = Sale.objects.filter(
        sale_date__date=today
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    total_revenue = Sale.objects.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    low_stock_products = Product.objects.filter(
        current_stock__lte=models.F("minimum_stock")
    )

    top_selling_products = (
        SaleItem.objects.values("product__name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    return render(request, "dashboard.html", {
        "total_products": total_products,
        "total_stock": total_stock,
        "today_sales": today_sales,
        "total_revenue": total_revenue,
        "low_stock_products": low_stock_products,
        "top_selling_products": top_selling_products,
    })


# User registration
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


# User login
class UserLoginView(LoginView):
    template_name = "login.html"


# User logout
def logout_view(request):
    logout(request)
    return redirect("home")


# Categories
def categories(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if name:
            Category.objects.get_or_create(name=name)

        return redirect("categories")

    category_list = Category.objects.all()

    return render(request, "categories.html", {
        "categories": category_list
    })


# Suppliers
def suppliers(request):
    if request.method == "POST":
        Supplier.objects.create(
            name=request.POST.get("name", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            email=request.POST.get("email", "").strip(),
            address=request.POST.get("address", "").strip(),
        )
        return redirect("suppliers")

    supplier_list = Supplier.objects.all()

    return render(request, "suppliers.html", {
        "suppliers": supplier_list
    })


# Products
def products(request):
    if request.method == "POST":
        Product.objects.create(
            name=request.POST.get("name", "").strip(),
            Category_id=request.POST.get("category"),
            Supplier_id=request.POST.get("supplier"),
            purchase_price=request.POST.get("purchase_price"),
            selling_price=request.POST.get("selling_price"),
            current_stock=request.POST.get("current_stock", 0),
            minimum_stock=request.POST.get("minimum_stock", 5),
        )
        return redirect("products")

    product_list = Product.objects.select_related(
        "Category", "Supplier"
    ).all()

    return render(request, "products.html", {
        "products": product_list,
        "categories": Category.objects.all(),
        "suppliers": Supplier.objects.all(),
    })


# Purchases
def purchases(request):
    if request.method == "POST":
        product_id = request.POST.get("product")
        quantity = int(request.POST.get("quantity", 0))

        if quantity > 0:
            product = get_object_or_404(Product, id=product_id)
            purchase_price = product.purchase_price
            subtotal = purchase_price * quantity

            purchase = Purchase.objects.create(
                supplier=product.Supplier,
                total_amount=subtotal
            )

            PurchaseItem.objects.create(
                purchase=purchase,
                product=product,
                quantity=quantity,
                purchase_price=purchase_price,
                subtotal=subtotal
            )

            product.current_stock += quantity
            product.save()

        return redirect("purchases")

    return render(request, "purchases.html", {
        "products": Product.objects.all()
    })


# Sales
@login_required
def sales(request):
    if request.method == "POST":
        product_id = request.POST.get("product")
        quantity_text = request.POST.get("quantity", "0")

        try:
            quantity = int(quantity_text)
        except (ValueError, TypeError):
            messages.error(request, "Enter a valid quantity.")
            return redirect("sales")

        product = get_object_or_404(Product, id=product_id)

        if quantity <= 0:
            messages.error(request, "Quantity must be greater than zero.")

        elif quantity > product.current_stock:
            messages.error(request, "Not enough stock available.")

        else:
            with transaction.atomic():
                subtotal = product.selling_price * quantity

                sale = Sale.objects.create(
                    sold_by=request.user,
                    total_amount=subtotal
                )

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    selling_price=product.selling_price,
                    subtotal=subtotal
                )

                product.current_stock -= quantity
                product.save()

            messages.success(request, "Sale recorded successfully!")

        return redirect("sales")

    return render(request, "sales.html", {
        "products": Product.objects.all()
    })




def analytics(request):
    products = Product.objects.all().values(
        "name",
        "current_stock",
        "minimum_stock",
        "purchase_price",
        "selling_price"
    )

    df = pd.DataFrame(list(products))

    # Convert numeric columns to proper numeric types
    numeric_columns = [
        "current_stock",
        "minimum_stock",
        "purchase_price",
        "selling_price"
    ]

    if not df.empty:
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Default values
    total_products = len(df)
    inventory_value = 0
    low_stock_count = 0
    top_inventory = []
    average_profit = 0
    restock_products = []
    chart_products = []
    best_sellers = []
    total_revenue = 0
    sales_chart = []

    if not df.empty:
        # Calculate stock value and profit per unit
        df["stock_value"] = (
            df["current_stock"] * df["purchase_price"]
        )

        df["profit_per_unit"] = (
            df["selling_price"] - df["purchase_price"]
        )

        df["restock_quantity"] = (
            df["minimum_stock"] - df["current_stock"]
        ).clip(lower=0)

        # Inventory summary
        inventory_value = df["stock_value"].sum()

        low_stock_count = int(
            np.sum(df["current_stock"] <= df["minimum_stock"])
        )

        # Top 5 inventory investments
        top_inventory = (
            df.nlargest(5, "stock_value")[
                ["name", "stock_value"]
            ].to_dict("records")
        )

        # Average profit per unit
        average_profit = float(df["profit_per_unit"].mean())

        # Restocking recommendations
        restock_products = (
            df[df["restock_quantity"] > 0].to_dict("records")
        )

        # Data for stock chart
        chart_products = df[
            ["name", "current_stock"]
        ].to_dict("records")

    # Sales analysis
    sales = SaleItem.objects.all().values(
        "product__name",
        "quantity",
        "subtotal"
    )

    sales_df = pd.DataFrame(list(sales))

    if not sales_df.empty:
        sales_df["quantity"] = pd.to_numeric(
            sales_df["quantity"], errors="coerce"
        ).fillna(0)

        sales_df["subtotal"] = pd.to_numeric(
            sales_df["subtotal"], errors="coerce"
        ).fillna(0)

        total_revenue = float(sales_df["subtotal"].sum())

        best_sellers = list(
            sales_df.groupby("product__name")["quantity"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .items()
        )

        sales_chart = [
            {"name": name, "quantity": int(quantity)}
            for name, quantity in best_sellers
        ]

    return render(request, "analytics.html", {
        "total_products": total_products,
        "inventory_value": round(float(inventory_value), 2),
        "low_stock_count": low_stock_count,
        "total_revenue": round(float(total_revenue), 2),
        "best_sellers": best_sellers,
        "top_inventory": top_inventory,
        "average_profit": round(float(average_profit), 2),
        "restock_products": restock_products,
        "chart_products": chart_products,
        "sales_chart": sales_chart,
    })


def smart_insights(request):
    products = Product.objects.all().values(
        "name",
        "current_stock",
        "minimum_stock",
        "purchase_price",
        "selling_price"
    )

    df = pd.DataFrame(list(products))

    # Default values: they always exist, whatever happens below
    insights = []
    total_products = len(df)
    inventory_value = 0
    low_stock_count = 0

    if df.empty:
        insights.append("No products yet. Add products to see insights.")
    else:
        # Convert columns to numbers (only safe when columns exist)
        for col in ["current_stock", "minimum_stock", "purchase_price", "selling_price"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Low-stock products
        low_stock = df[df["current_stock"] <= df["minimum_stock"]]
        low_stock_count = len(low_stock)

        for _, product in low_stock.iterrows():
            insights.append(
                f"Restock {product['name']}: only "
                f"{int(product['current_stock'])} units remain."
            )

        # Out-of-stock products
        out_of_stock = df[df["current_stock"] == 0]

        for _, product in out_of_stock.iterrows():
            insights.append(f"URGENT: {product['name']} is out of stock.")

        # Highest inventory investment
        df["stock_value"] = df["current_stock"] * df["purchase_price"]
        inventory_value = float(df["stock_value"].sum())

        highest_value = df.loc[df["stock_value"].idxmax()]
        insights.append(
            f"Highest inventory investment: {highest_value['name']} "
            f"(₹{highest_value['stock_value']:.2f})."
        )

        # Low profit margins
        df["profit_per_unit"] = df["selling_price"] - df["purchase_price"]
        low_margin = df[df["profit_per_unit"] <= 0]

        for _, product in low_margin.iterrows():
            insights.append(
                f"Review pricing for {product['name']}: "
                "selling price is not above purchase price."
            )

        if not insights:
            insights.append("Inventory looks healthy. No immediate stock alerts found.")

    return render(request, "smart_insights.html", {
        "insights": insights,
        "total_products": total_products,
        "inventory_value": round(inventory_value, 2),
        "low_stock_count": low_stock_count,
    })

def update_product(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.Category_id = request.POST.get("category")
        product.Supplier_id = request.POST.get("supplier")
        product.purchase_price = request.POST.get("purchase_price")
        product.selling_price = request.POST.get("selling_price")
        product.current_stock = request.POST.get("current_stock")
        product.minimum_stock = request.POST.get("minimum_stock")
        product.save()

        return redirect("products")

    return render(request, "update_product.html", {
        "product": product,
        "categories": Category.objects.all(),
        "suppliers": Supplier.objects.all(),
    })
