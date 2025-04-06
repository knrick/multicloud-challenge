import os
import json
from decimal import Decimal
from google.cloud import bigquery
from google.oauth2 import service_account
import tempfile

def handler(event, context):
    """Handle DynamoDB Stream events and sync to BigQuery"""
    try:
        # Initialize BigQuery client with credentials from the layer
        credentials = service_account.Credentials.from_service_account_file(
            '/opt/google_credentials.json'
        )
        client = bigquery.Client(
            credentials=credentials,
            project=os.environ['GOOGLE_CLOUD_PROJECT_ID']
        )
        
        dataset_id = os.environ['BIGQUERY_DATASET_ID']
        table_id = os.environ['BIGQUERY_TABLE_ID']
        table_ref = f"{os.environ['GOOGLE_CLOUD_PROJECT_ID']}.{dataset_id}.{table_id}"
        
        # Process DynamoDB Stream records
        orders_to_load = []
        for record in event['Records']:
            if record['eventName'] == 'INSERT':
                # Get the new order data
                new_order = record['dynamodb']['NewImage']
                
                # Convert DynamoDB format to regular JSON
                order_data = {
                    'id': new_order['id']['S'],
                    'userEmail': new_order['userEmail']['S'],
                    'total': float(new_order['total']['N']),
                    'status': new_order['status']['S'],
                    'createdAt': new_order['createdAt']['S'],
                    'items': new_order.get('items', {}).get('S', '[]')  # Handle items as JSON string
                }
                orders_to_load.append(order_data)
        
        if orders_to_load:
            # Create a temporary file for the batch load
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                for order in orders_to_load:
                    temp_file.write(json.dumps(order) + '\n')
                temp_file.flush()
            
            # Configure the load job
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                schema=[
                    bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("items", "JSON", mode="REQUIRED"),
                    bigquery.SchemaField("userEmail", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("total", "FLOAT", mode="REQUIRED"),
                    bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("createdAt", "TIMESTAMP", mode="REQUIRED")
                ]
            )
            
            # Load the data
            with open(temp_file.name, 'rb') as source_file:
                job = client.load_table_from_file(
                    source_file,
                    table_ref,
                    job_config=job_config
                )
            
            # Wait for the job to complete
            job.result()
            
            # Clean up
            os.unlink(temp_file.name)
            
            print(f"Successfully loaded {len(orders_to_load)} orders to BigQuery")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed records')
        }
        
    except Exception as e:
        print(f"Error: {e}")
        raise

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj) 