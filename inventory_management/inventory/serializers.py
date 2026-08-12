from rest_framework import serializers

from .models import Category, Customer, Invoice, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Category name must be at least 2 characters long."
            )
        return value.strip()


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone_number", "address", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Customer name must be at least 2 characters long."
            )
        return value.strip()

    def validate_phone_number(self, value):
        if value and not value.replace("+", "").replace(" ", "").isdigit():
            raise serializers.ValidationError(
                "Phone number may only contain digits, spaces, and a leading +."
            )
        return value


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "sku",
            "price",
            "stock_quantity",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative.")
        return value

    def validate_sku(self, value):
        if not value.strip():
            raise serializers.ValidationError("SKU cannot be blank.")
        return value.strip().upper()


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    created_by = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = Invoice
        fields = [
            "id",
            "customer",
            "customer_name",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "total_price",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than zero.")
        return value

    def validate(self, attrs):
        # On create, make sure there's enough stock for the sale.
        product = attrs.get("product") or getattr(self.instance, "product", None)
        quantity = attrs.get("quantity") or getattr(self.instance, "quantity", None)
        if product is not None and quantity is not None:
            available = product.stock_quantity
            if self.instance is not None and self.instance.product_id == product.id:
                # Editing an existing invoice for the same product: add
                # back the quantity it already reserved before comparing.
                available += self.instance.quantity
            if quantity > available:
                raise serializers.ValidationError(
                    {
                        "quantity": (
                            f"Only {available} unit(s) of "
                            f"'{product.name}' are in stock."
                        )
                    }
                )
        return attrs

    def create(self, validated_data):
        product = validated_data["product"]
        quantity = validated_data["quantity"]
        invoice = super().create(validated_data)
        product.stock_quantity -= quantity
        product.save(update_fields=["stock_quantity"])
        return invoice

    def update(self, instance, validated_data):
        old_product, old_quantity = instance.product, instance.quantity
        invoice = super().update(instance, validated_data)

        new_product = invoice.product
        new_quantity = invoice.quantity
        if old_product.id != new_product.id:
            old_product.stock_quantity += old_quantity
            old_product.save(update_fields=["stock_quantity"])
            new_product.stock_quantity -= new_quantity
            new_product.save(update_fields=["stock_quantity"])
        elif old_quantity != new_quantity:
            diff = new_quantity - old_quantity
            new_product.stock_quantity -= diff
            new_product.save(update_fields=["stock_quantity"])
        return invoice
