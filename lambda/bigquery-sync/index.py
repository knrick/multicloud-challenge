import os
import json
from decimal import Decimal
from google.cloud import bigquery
from google.oauth2 import service_account
import tempfile
from datetime import datetime
import logging

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """Handle DynamoDB Stream events and sync to BigQuery"""
    try:
        # Check environment variables are set
        required_env_vars = ['GOOGLE_CLOUD_PROJECT_ID', 'BIGQUERY_DATASET_ID', 'BIGQUERY_TABLE_ID']
        for var in required_env_vars:
            if not os.environ.get(var):
                error_msg = f"Missing required environment variable: {var}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
        # Check if credentials file exists
        creds_path = '/opt/google_credentials.json'
        if not os.path.exists(creds_path):
            logger.error(f"Credentials file not found at {creds_path}")
            raise FileNotFoundError(f"Credentials file not found at {creds_path}")
        
        # Initialize BigQuery client with credentials from the layer
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        client = bigquery.Client(
            credentials=credentials,
            project=os.environ['GOOGLE_CLOUD_PROJECT_ID']
        )
        
        table_ref = f"{os.environ['GOOGLE_CLOUD_PROJECT_ID']}.{os.environ['BIGQUERY_DATASET_ID']}.{os.environ['BIGQUERY_TABLE_ID']}"
        
        # Process DynamoDB Stream records
        orders_to_load = []
        for record in event['Records']:
            if record['eventName'] == 'INSERT':
                # Get the new order data
                new_order = record['dynamodb']['NewImage']
                
                try:
                    # Parse and format the timestamp
                    created_at = new_order.get('createdAt', {}).get('S')
                    if not created_at:
                        logger.error(f"Missing createdAt timestamp in record: {json.dumps(new_order)}")
                        continue
                        
                    # Ensure the timestamp is in the correct format for BigQuery
                    timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f UTC')
                    
                    # Handle items - parse DynamoDB List type
                    items_data = new_order.get('items', {}).get('L', [])
                    items = []
                    for item in items_data:
                        if 'M' in item:  # It's a map type
                            item_map = item['M']
                            items.append({
                                'quantity': int(item_map.get('quantity', {}).get('N', '0')),
                                'productId': item_map.get('productId', {}).get('S', ''),
                                'price': float(item_map.get('price', {}).get('N', '0'))
                            })
                    
                    # Convert DynamoDB format to regular JSON
                    order_data = {
                        'id': new_order.get('id', {}).get('S'),
                        'userEmail': new_order.get('userEmail', {}).get('S'),
                        'total': float(new_order.get('total', {}).get('N', '0')),
                        'status': new_order.get('status', {}).get('S', 'unknown'),
                        'createdAt': formatted_timestamp,
                        'items': json.dumps(items)  # Convert items list to JSON string
                    }
                    
                    # Validate required fields
                    if not all([order_data['id'], order_data['userEmail'], order_data['createdAt']]):
                        logger.error(f"Missing required fields in order data: {json.dumps(order_data)}")
                        continue
                    
                    orders_to_load.append(order_data)
                    
                except Exception as e:
                    logger.error(f"Error processing record {new_order.get('id', {}).get('S', 'unknown')}: {str(e)}")
                    continue
        
        if orders_to_load:
            # Create a temporary file for the batch load and process it
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as temp_file:
                # Write the data
                for order in orders_to_load:
                    temp_file.write(json.dumps(order) + '\n')
                temp_file.flush()
                
                # Configure the load job
                job_config = bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
                )
                
                try:
                    # Load the data
                    with open(temp_file.name, 'rb') as source_file:
                        job = client.load_table_from_file(
                            source_file,
                            table_ref,
                            job_config=job_config
                        )
                    
                    # Wait for the job to complete
                    job.result()
                    
                    if job.errors:
                        logger.error(f"Job errors: {json.dumps(job.errors)}")
                    else:
                        table = client.get_table(table_ref)
                        logger.info(f"Successfully loaded {len(orders_to_load)} orders. Total rows in table: {table.num_rows}")
                    
                except Exception as e:
                    logger.error(f"Error during BigQuery load: {str(e)}")
                    raise
        
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed records')
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj) 