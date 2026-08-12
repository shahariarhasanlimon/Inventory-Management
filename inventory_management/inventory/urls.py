from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CustomerViewSet,
    InvoiceReportView,
    InvoiceViewSet,
    ProductViewSet,
)

app_name = "inventory"

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("customers", CustomerViewSet, basename="customer")
router.register("products", ProductViewSet, basename="product")
router.register("invoices", InvoiceViewSet, basename="invoice")

urlpatterns = [
    path("reports/summary/", InvoiceReportView.as_view(), name="invoice-summary"),
    path("", include(router.urls)),
]
