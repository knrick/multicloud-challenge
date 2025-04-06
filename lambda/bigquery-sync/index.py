import os
import json
from decimal import Decimal
from google.cloud import bigquery
from google.oauth2 import service_account
import tempfile
from datetime import datetime
import logging
import sys

# Force logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger()

def handler(event, context):
    """Handle DynamoDB Stream events and sync to BigQuery"""
    # Immediate logging to verify function is running
    print("Lambda function started")  # Basic print for absolute minimal logging
    logger.info("Lambda function initialized")
    logger.info(f"Python version: {sys.version}")
    
    try:
        # Log the event immediately
        logger.info("Raw event received")
        logger.info(json.dumps(event, default=str))
        
        # Check environment variables are set
        required_env_vars = ['GOOGLE_CLOUD_PROJECT_ID', 'BIGQUERY_DATASET_ID', 'BIGQUERY_TABLE_ID']
        for var in required_env_vars:
            if not os.environ.get(var):
                logger.error(f"Missing required environment variable: {var}")
                raise ValueError(f"Missing required environment variable: {var}")
            logger.info(f"{var}: {os.environ[var]}")
            
        # Check if credentials file exists
        creds_path = '/opt/google_credentials.json'
        if not os.path.exists(creds_path):
            logger.error(f"Credentials file not found at {creds_path}")
            raise FileNotFoundError(f"Credentials file not found at {creds_path}")
        logger.info("Found credentials file")
        
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
        
        logger.info(f"Project ID: {os.environ['GOOGLE_CLOUD_PROJECT_ID']}")
        logger.info(f"Dataset ID: {dataset_id}")
        logger.info(f"Table ID: {table_id}")
        logger.info(f"Full table reference: {table_ref}")
        
        # Process DynamoDB Stream records
        orders_to_load = []
        for record in event['Records']:
            logger.info(f"Processing record: {json.dumps(record)}")
            
            if record['eventName'] == 'INSERT':
                # Get the new order data
                new_order = record['dynamodb']['NewImage']
                logger.info(f"New order data: {json.dumps(new_order)}")
                
                try:
                    # Parse and format the timestamp
                    created_at = new_order.get('createdAt', {}).get('S')
                    if not created_at:
                        logger.error(f"Missing createdAt timestamp in record: {json.dumps(new_order)}")
                        continue
                        
                    # Ensure the timestamp is in the correct format for BigQuery
                    timestamp = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f UTC')
                    
                    # Handle items - parse JSON from DynamoDB
                    items_str = new_order.get('items', {}).get('S', '[]')
                    try:
                        # Parse JSON to validate and format it properly
                        items = json.loads(items_str)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in items field: {items_str}")
                        items = []
                    
                    # Convert DynamoDB format to regular JSON
                    order_data = {
                        'id': new_order.get('id', {}).get('S'),
                        'userEmail': new_order.get('userEmail', {}).get('S'),
                        'total': float(new_order.get('total', {}).get('N', '0')),
                        'status': new_order.get('status', {}).get('S', 'unknown'),
                        'createdAt': formatted_timestamp,
                        'items': items  # Store as parsed JSON, not as string
                    }
                    
                    # Validate required fields
                    if not all([order_data['id'], order_data['userEmail'], order_data['createdAt']]):
                        logger.error(f"Missing required fields in order data: {json.dumps(order_data)}")
                        continue
                        
                    logger.info(f"Transformed order data: {json.dumps(order_data)}")
                    orders_to_load.append(order_data)
                    
                except Exception as e:
                    logger.error(f"Error processing record {new_order.get('id', {}).get('S', 'unknown')}: {str(e)}")
                    continue
        
        if orders_to_load:
            logger.info(f"Preparing to load {len(orders_to_load)} orders")
            
            # Create a temporary file for the batch load
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
                for order in orders_to_load:
                    temp_file.write(json.dumps(order) + '\n')
                temp_file.flush()
                
                logger.info(f"Created temp file at: {temp_file.name}")
                # Debug: print file contents
                with open(temp_file.name, 'r') as f:
                    logger.info(f"File contents: {f.read()}")
            
            # Configure the load job
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                schema=[
                    bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("items", "JSON", mode="REQUIRED"),
                    bigquery.SchemaField("userEmail", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("total", "FLOAT64", mode="REQUIRED"),
                    bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("createdAt", "TIMESTAMP", mode="REQUIRED")
                ]
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
                job.result()  # Waits for job to complete
                logger.info(f"Job finished with state: {job.state}")
                
                if job.errors:
                    logger.error(f"Job errors: {json.dumps(job.errors)}")
                else:
                    # Verify the data was loaded
                    table = client.get_table(table_ref)
                    logger.info(f"Loaded {table.num_rows} rows total.")
                    
                    # Query the recently inserted data
                    query = f"""
                    SELECT id, userEmail, total, status, createdAt
                    FROM `{table_ref}`
                    WHERE createdAt >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
                    """
                    query_job = client.query(query)
                    results = query_job.result()
                    logger.info("Recent records in BigQuery:")
                    for row in results:
                        logger.info(f"  {dict(row.items())}")
                
            except Exception as e:
                logger.error(f"Error during BigQuery load: {str(e)}")
                raise
            finally:
                # Clean up
                os.unlink(temp_file.name)
            
            logger.info(f"Successfully processed {len(orders_to_load)} orders")
        else:
            logger.info("No orders to load")
        
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