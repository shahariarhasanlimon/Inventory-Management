from django.db.models import Sum
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Customer, Invoice, Product
from .permissions import IsOwnerOrStaff, IsStaffOrReadOnly
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    InvoiceSerializer,
    ProductSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsStaffOrReadOnly]


class CustomerViewSet(viewsets.ModelViewSet):
    """
    Customers can be read by any authenticated user, but only staff can
    create/update/delete them (part of "authorized users can modify" --
    customers feed directly into invoices/sales).
    """

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsStaffOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    Any authenticated user can create an invoice (it's tied to them via
    created_by); editing/deleting is restricted to the creator or staff
    by IsOwnerOrStaff.
    """

    queryset = Invoice.objects.select_related("customer", "product", "created_by").all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsOwnerOrStaff]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class InvoiceReportView(APIView):
    """
    GET /api/inventory/reports/summary/
    Read-only summary: total number of invoices, total sales revenue,
    and total number of product units sold.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Invoice.objects.all()
        total_invoices = queryset.count()
        totals = queryset.aggregate(total_units=Sum("quantity"))
        total_products_sold = totals["total_units"] or 0
        total_sales = sum((invoice.total_price for invoice in queryset), start=0)

        return Response(
            {
                "total_invoices": total_invoices,
                "total_sales": total_sales,
                "total_products_sold": total_products_sold,
            }
        )
