from django.urls import path
from .import views

urlpatterns = [
        path("register/", views.register, name="register"),
    path("", views.home, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("",views.base,name=""),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("categories/", views.categories, name="categories"),
    path("suppliers/", views.suppliers, name="suppliers"),
    path("products/", views.products, name="products"),
    path("purchases/", views.purchases, name="purchases"),
    path("sales/", views.sales, name="sales"),
    path("analytics/", views.analytics, name="analytics"),
    path("smart-insights/", views.smart_insights, name="smart_insights"),
    path("products/update/<int:id>/", views.update_product, name="update_product"),
]