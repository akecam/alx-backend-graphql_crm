import os
from datetime import datetime
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

# Define the GraphQL endpoint
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
LOG_FILE_PATH = "/tmp/crmheart_heartbeat_log.txt"

def log_crm_heartbeat():
    """
    Logs a heartbeat message to a file and optionally queries the GraphQL endpoint
    to verify its responsiveness.
    """
    current_timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    heartbeat_message = f"{current_timestamp} CRM is alive\n"

    try:
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(heartbeat_message)

        # Optional: Query the GraphQL endpoint to verify responsiveness
        try:
            transport = RequestsHTTPTransport(url=GRAPHQL_ENDPOINT, verify=False, retries=3)
            client = Client(transport=transport, fetch_schema_from_transport=True)

            # Assuming there's a simple 'hello' query in your GraphQL schema
            # If not, you might need to adjust this query to something that exists,
            # e.g., a simple 'customer' query if it takes no arguments or a specific ID.
            query = gql(
                """
                query {
                    hello
                }
                """
            )
            result = client.execute(query)
            graphql_status = f"GraphQL endpoint responsive. Hello: {result.get('hello', 'N/A')}\n"
        except Exception as e:
            graphql_status = f"GraphQL endpoint not responsive or query failed: {e}\n"

        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(graphql_status)

    except Exception as e:
        error_message = f"{current_timestamp} Error logging CRM heartbeat or checking GraphQL: {e}\n"
        # If the primary log file can't be opened, try to print to stderr or a different log
        try:
            with open("/tmp/crm_heartbeat_error.log", "a") as error_log:
                error_log.write(error_message)
        except:
            print(f"FATAL ERROR: Could not write to any log file: {error_message}", file=os.sys.stderr)

def update_low_stock():
    """
    Executes a GraphQL mutation to update low-stock products and logs the updates.
    """
    LOW_STOCK_LOG_FILE = "/tmp/low_stock_updates_log.txt"
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        transport = RequestsHTTPTransport(url=GRAPHQL_ENDPOINT, verify=False, retries=3)
        client = Client(transport=transport, fetch_schema_from_transport=True)

        mutation = gql(
            """
            mutation {
                updateLowStockProducts {
                    products {
                        id
                        name
                        stock
                    }
                    message
                }
            }
            """
        )

        result = client.execute(mutation)
        updated_products_info = result.get('updateLowStockProducts', {})
        products = updated_products_info.get('products', [])
        message = updated_products_info.get('message', 'No message from mutation.')

        with open(LOW_STOCK_LOG_FILE, "a") as log_file:
            log_file.write(f"[{current_timestamp}] {message}\n")
            if products:
                for product in products:
                    log_file.write(f"  - Product ID: {product['id']}, Name: {product['name']}, New Stock: {product['stock']}\n")
            else:
                log_file.write(f"[{current_timestamp}] No products updated.\n")

    except Exception as e:
        error_message = f"[{current_timestamp}] Error updating low stock products: {e}\n"
        with open(LOW_STOCK_LOG_FILE, "a") as log_file:
            log_file.write(error_message)
        print(f"Error updating low stock products: {e}", file=os.sys.stderr)
