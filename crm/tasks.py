import os
from datetime import datetime
from celery import shared_task
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
import requests

# Define the GraphQL endpoint
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
LOG_FILE_PATH = "/tmp/crm_report_log.txt"

@shared_task
def generate_crm_report():
    """
    Generates a weekly CRM report by querying GraphQL for total customers, orders, and revenue,
    then logs the report to a file.
    """
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        transport = RequestsHTTPTransport(url=GRAPHQL_ENDPOINT, verify=False, retries=3)
        client = Client(transport=transport, fetch_schema_from_transport=True)

        # GraphQL query to fetch report data
        # Assuming you have fields like `customerCount`, `orderCount`, `totalRevenue`
        # in your GraphQL schema's Query type.
        # If not, you'll need to create resolvers for these in crm/schema.py.
        query = gql(
            """
            query CrmReport {
                allCustomers {
                    totalCount
                }
                allOrders {
                    totalCount
                    edges {
                        node {
                            totalAmount
                        }
                    }
                }
            }
            """
        )

        result = client.execute(query)

        customer_count = result.get('allCustomers', {}).get('totalCount', 0)
        order_count = result.get('allOrders', {}).get('totalCount', 0)

        total_revenue = 0
        order_edges = result.get('allOrders', {}).get('edges', [])
        for edge in order_edges:
            total_revenue += edge.get('node', {}).get('totalAmount', 0)

        report_message = (
            f"{current_timestamp} - Report: {customer_count} customers, "
            f"{order_count} orders, {total_revenue:.2f} revenue.\n"
        )

        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(report_message)

        print(f"CRM report generated: {report_message.strip()}")

    except Exception as e:
        error_message = f"[{current_timestamp}] Error generating CRM report: {e}\n"
        with open(LOG_FILE_PATH, "a") as log_file:
            log_file.write(error_message)
        print(f"Error generating CRM report: {e}", file=os.sys.stderr)
