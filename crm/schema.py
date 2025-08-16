from typing_extensions import Required
import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from django.db import transaction
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


# ==============================
# GraphQL Types
# ==============================
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# ==============================
# Mutations
# ==============================
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists")

        if phone:
            validator = RegexValidator(
            regex=r"^\+?\d{7,15}$|^\d{3}-\d{3}-\d{4}$",
            message="Invalid phone format. Use +1234567890 or 123-456-7890."
            )
            validator(phone)

        customer = Customer(name=name, email=email, phone=phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(graphene.JSONString, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, customers):
        created_customers = []
        errors = []

        for entry in customers:
            try:
                name = entry.get("name")
                email = entry.get("email")
                phone = entry.get("phone")

                if not name or not email:
                    raise ValidationError("Name and email are required.")

                if Customer.objects.filter(email=email).exists():
                    raise ValidationError(f"Email already exists: {email}")

                if phone:
                    validator = RegexValidator(
                        regex=r"^\+?\d{7,15}$|^\d{3}-\d{3}-\d{4}$",
                        message="Invalid phone format."
                    )
                    validator(phone)

                customer = Customer(name=name, email=email, phone=phone)
                customer.save()
                created_customers.append(customer)

            except Exception as e:
                errors.append(str(e))

        return BulkCreateCustomers(customers=created_customers, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be positive")
        if stock < 0:
            raise Exception("stock cannot be negative")

        product = Product(name=name, price=price, stock=stock)
        product.save()
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):

    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID.")

        if not product_ids:
            raise Exception("At least one product must be selected.")

        products = Products.objects.filter(id__in=product_ids)
        if products.count() != len(product_ids):
            raise Exception("One or more product IDs are invalid.")

        total_amount = sum([p.price for p in products])

        order = Order(customer=customer, total_amount=total_amount)
        order.save()
        order.products.set(products)
        return CreateOrder(order=order)


# ###############
# ROOT TYPES
# ##############

class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)

    def resolve_all_customers(self, info):
        return Customer.objects.all()

    def resolve_all_products(self, info):
        return Product.objects.all()

    def resolve_all_orders(self, info):
        return Order.objects.all()


class Mutation(graphene.ObjectType):
    create_cutomers = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
