import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_backend_graphql_crm.settings")
django.setup()

from crm.models import Customer, Product

def run():
    Customer.objects.all().delete()
    Product.objects.all().delete()

    customers = [
        {"name": "Alice", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob", "email": "bob@example.com", "phone": "123-456-7890"},
    ]
    for c in customers:
        Customer.objects.create(**c)

    products = [
        {"name": "Laptop", "price": 1200.00, "stock": 5},
        {"name": "Phone", "price": 500.00, "stock": 15},
    ]
    for p in products:
        Product.objects.create(**p)

    print("Database seeded successfully!")

if __name__ == "__main__":
    run()
