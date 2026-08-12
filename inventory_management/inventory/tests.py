from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Customer, Product

User = get_user_model()


class AccountsTests(APITestCase):
    def test_register_and_profile_flow(self):
        resp = self.client.post(
            "/api/accounts/register/",
            {
                "username": "alice",
                "email": "alice@example.com",
                "password": "S3curePass!23",
                "password_confirm": "S3curePass!23",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

        user = User.objects.get(username="alice")
        self.client.force_authenticate(user=user)

        resp = self.client.get("/api/accounts/profile/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], "alice@example.com")

        resp = self.client.patch(
            "/api/accounts/profile/", {"phone_number": "+8801234567"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["phone_number"], "+8801234567")

    def test_profile_requires_auth(self):
        resp = self.client.get("/api/accounts/profile/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class ProductPermissionTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staffuser", email="staff@example.com", password="pass1234", is_staff=True
        )
        self.regular = User.objects.create_user(
            username="regular", email="regular@example.com", password="pass1234"
        )
        self.category = Category.objects.create(name="Electronics")

    def test_regular_user_can_read_but_not_create_product(self):
        self.client.force_authenticate(user=self.regular)

        resp = self.client.get("/api/inventory/products/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post(
            "/api/inventory/products/",
            {
                "name": "Laptop",
                "category": self.category.id,
                "sku": "SKU-001",
                "price": "1000.00",
                "stock_quantity": 5,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_user_can_create_product(self):
        self.client.force_authenticate(user=self.staff)
        resp = self.client.post(
            "/api/inventory/products/",
            {
                "name": "Laptop",
                "category": self.category.id,
                "sku": "SKU-001",
                "price": "1000.00",
                "stock_quantity": 5,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)

    def test_invalid_price_rejected(self):
        self.client.force_authenticate(user=self.staff)
        resp = self.client.post(
            "/api/inventory/products/",
            {
                "name": "Free Item",
                "category": self.category.id,
                "sku": "SKU-002",
                "price": "0.00",
                "stock_quantity": 5,
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", resp.data)


class InvoiceTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staffuser", email="staff@example.com", password="pass1234", is_staff=True
        )
        self.regular = User.objects.create_user(
            username="regular", email="regular@example.com", password="pass1234"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="pass1234"
        )
        category = Category.objects.create(name="Electronics")
        self.customer = Customer.objects.create(name="John Doe", email="john@example.com")
        self.product = Product.objects.create(
            name="Mouse", category=category, sku="SKU-100", price="20.00", stock_quantity=10
        )

    def test_any_authenticated_user_can_create_invoice_and_stock_is_reduced(self):
        self.client.force_authenticate(user=self.regular)
        resp = self.client.post(
            "/api/inventory/invoices/",
            {
                "customer": self.customer.id,
                "product": self.product.id,
                "quantity": 3,
                "unit_price": "20.00",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["created_by"], "regular")

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 7)

    def test_cannot_invoice_more_than_stock(self):
        self.client.force_authenticate(user=self.regular)
        resp = self.client.post(
            "/api/inventory/invoices/",
            {
                "customer": self.customer.id,
                "product": self.product.id,
                "quantity": 999,
                "unit_price": "20.00",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_owner_non_staff_cannot_edit_others_invoice(self):
        self.client.force_authenticate(user=self.regular)
        resp = self.client.post(
            "/api/inventory/invoices/",
            {
                "customer": self.customer.id,
                "product": self.product.id,
                "quantity": 1,
                "unit_price": "20.00",
            },
        )
        invoice_id = resp.data["id"]

        self.client.force_authenticate(user=self.other)
        resp = self.client.patch(
            f"/api/inventory/invoices/{invoice_id}/", {"quantity": 2}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.staff)
        resp = self.client.patch(
            f"/api/inventory/invoices/{invoice_id}/", {"quantity": 2}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)

    def test_report_summary(self):
        self.client.force_authenticate(user=self.regular)
        self.client.post(
            "/api/inventory/invoices/",
            {
                "customer": self.customer.id,
                "product": self.product.id,
                "quantity": 2,
                "unit_price": "20.00",
            },
        )
        self.client.post(
            "/api/inventory/invoices/",
            {
                "customer": self.customer.id,
                "product": self.product.id,
                "quantity": 1,
                "unit_price": "20.00",
            },
        )

        resp = self.client.get("/api/inventory/reports/summary/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total_invoices"], 2)
        self.assertEqual(resp.data["total_products_sold"], 3)
        self.assertEqual(str(resp.data["total_sales"]), "60.00")
