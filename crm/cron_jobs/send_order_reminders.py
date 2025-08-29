#!/usr/bin/env python3
import sys
import os
from datetime import datetime, timedelta, timezone # Use standard library timezone

# Ensure gql and its dependencies are installed: pip install "gql[requests]"
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

# Define the GraphQL endpoint
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
LOG_FILE_PATH = "/tmp/order_reminders_log.txt"

def send_order_reminders():
    """
    Queries the GraphQL endpoint for orders placed within the last 7 days
    and logs reminders to a file.
    """
    try:
        # Create a GraphQL client
        # verify=False is generally not recommended for production but might be necessary
        # for local self-signed certificates or development setups.
        # For localhost, it's typically fine.
        transport = RequestsHTTPTransport(url=GRAPHQL_ENDPOINT, verify=False, retries=3)
        client = Client(transport=transport, fetch_schema_from_transport=True)

        # Define the GraphQL query
        # Assuming the schema has an 'allOrders' query with a 'orderDate_Gte' filter
        # and 'id', 'customer.email' fields.
        query = gql(
            """
            query GetRecentOrders($date_gte: DateTime!) {
                allOrders(orderDate_Gte: $date_gte) {
                    id
                    customer {
                        email
                    }
                    orderDate # Including orderDate to verify the filter if needed
                }
            }
            """
        )

        # Calculate the date 7 days ago, in UTC timezone.
        # GraphQL DateTime types usually expect ISO 8601 format with timezone.
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        date_gte_str = seven_days_ago.isoformat()

        # Execute the query with variables
        variables = {"date_gte": date_gte_str}
        result = client.execute(query, variables=variables)

        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reminded_count = 0

        with open(LOG_FILE_PATH, "a") as log_file:
            if result and 'allOrders' in result and result['allOrders']:
                for order in result['allOrders']:
                    order_id = order.get('id', 'N/A')
                    customer_email = order.get('customer', {}).get('email', 'N/A')

                    if order_id != 'N/A' and customer_email != 'N/A': # Only log if details are present
                        log_entry = f"[{current_timestamp}] Reminder for Order ID: {order_id}, Customer Email: {customer_email}\n"
                        log_file.write(log_entry)
                        reminded_count += 1

                if reminded_count > 0:
                    log_file.write(f"[{current_timestamp}] Processed {reminded_count} order reminders.\n")
                else:
                    log_file.write(f"[{current_timestamp}] No recent orders found to send reminders for.\n")
            else:
                log_file.write(f"[{current_timestamp}] No orders data received from GraphQL endpoint or query returned empty list.\n")

        print("Order reminders processed!")

    except Exception as e:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_log_entry = f"[{current_timestamp}] Error sending order reminders: {e}\n"
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(error_log_entry)
        print(f"Error processing order reminders: {e}")
        sys.exit(1)

if __name__ == "__main__":
    send_order_reminders()
