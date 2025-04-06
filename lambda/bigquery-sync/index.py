import os
import json
from decimal import Decimal
from google.cloud import bigquery
from google.oauth2 import service_account

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
        for record in event['Records']:
            if record['eventName'] == 'INSERT':
                # Get the new order data
                new_order = record['dynamodb']['NewImage']
                
                # Convert DynamoDB format to regular JSON
                order_data = {
                    'order_id': new_order['id']['S'],
                    'user_email': new_order['userEmail']['S'],
                    'total': float(new_order['total']['N']),
                    'status': new_order['status']['S'],
                    'created_at': new_order['createdAt']['S']
                }
                
                # Insert into BigQuery
                errors = client.insert_rows_json(table_ref, [order_data])
                if errors:
                    print(f"Errors inserting order {order_data['order_id']}: {errors}")
                else:
                    print(f"Successfully synced order {order_data['order_id']} to BigQuery")
        
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