import os
import json
import logging
from google.cloud import bigquery
from decimal import Decimal

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize BigQuery client
bigquery_client = bigquery.Client()
dataset_id = os.environ['BIGQUERY_DATASET_ID']
table_id = os.environ['BIGQUERY_TABLE_ID']
table_ref = f"{os.environ['GOOGLE_CLOUD_PROJECT_ID']}.{dataset_id}.{table_id}"

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def handler(event, context):
    """
    Lambda handler to sync DynamoDB orders to BigQuery.
    Processes DynamoDB Stream events and inserts/updates records in BigQuery.
    """
    try:
        logger.info(f"Processing event: {json.dumps(event)}")
        
        rows_to_insert = []
        
        for record in event['Records']:
            # Only process INSERT and MODIFY events
            if record['eventName'] not in ['INSERT', 'MODIFY']:
                continue
                
            # Get the new image of the record
            new_image = record['dynamodb']['NewImage']
            
            # Convert DynamoDB types to Python types
            order = {
                'id': new_image['id']['S'],
                'items': json.dumps(new_image['items']['L'], cls=DecimalEncoder),
                'userEmail': new_image['userEmail']['S'],
                'total': float(new_image['total']['N']),
                'status': new_image['status']['S'],
                'createdAt': new_image['createdAt']['S']
            }
            
            rows_to_insert.append(order)
        
        if rows_to_insert:
            # Insert rows into BigQuery
            table = bigquery_client.get_table(table_ref)
            errors = bigquery_client.insert_rows_json(table, rows_to_insert)
            
            if errors:
                logger.error(f"Encountered errors while inserting rows: {errors}")
                raise Exception("Failed to insert rows into BigQuery")
            
            logger.info(f"Successfully inserted {len(rows_to_insert)} rows into BigQuery")
            
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed DynamoDB stream events')
        }
        
    except Exception as e:
        logger.error(f"Error processing records: {str(e)}")
        raise 