import graphene
from graphene_django.types import DjangoObjectType
from .models import Customer, Product, Order
from django.db import transaction
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from graphene_django.filter import DjangoFilterConnectionField
from crm.filters import CustomerFilter, ProductFilter, OrderFilter


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


class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)
        # fields = ("id", "name", "email", "phone")


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)
        # fields = ("id", "name", "price", "stock")


class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)
        # fields = ("id", "customer", "products", "total_amount", "order_date")


# ==============================
# Mutations
# ==============================
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerNode)
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

    customers = graphene.List(CustomerNode)
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

    product = graphene.Field(ProductNode)

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

    order = graphene.Field(OrderNode)

    def mutate(self, info, customer_id, product_ids):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID.")

        if not product_ids:
            raise Exception("At least one product must be selected.")

        products = Product.objects.filter(id__in=product_ids)
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
    customer = graphene.relay.Node.Field(CustomerNode)
    all_customers = DjangoFilterConnectionField(CustomerNode, order_by=graphene.List(of_type=graphene.String))

    product = graphene.relay.Node.Field(ProductNode)
    all_products = DjangoFilterConnectionField(ProductNode, order_by=graphene.List(of_type=graphene.String))

    order = graphene.relay.Node.Field(OrderNode)
    all_orders = DjangoFilterConnectionField(OrderNode, order_by=graphene.List(of_type=graphene.String))

    # Add ordering logic
    def resolve_all_customers(self, info, order_by=None, **kwargs):
        qs = Customer.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_products(self, info, order_by=None, **kwargs):
        qs = Product.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_orders(self, info, order_by=None, **kwargs):
        qs = Order.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
