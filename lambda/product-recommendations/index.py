import os
import json
import boto3
import logging
from typing import Dict, List, Any

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PRODUCTS_TABLE'])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to list products from DynamoDB.
    Can filter by name if provided in the query parameters.
    Returns a properly formatted HTTP response as expected by Bedrock agent.
    """
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        name_filter = query_params.get('name')
        logger.info(f"Query parameters: {query_params}, name filter: {name_filter}")

        # Prepare scan parameters
        scan_params = {}
        if name_filter:
            scan_params['FilterExpression'] = 'contains(#name, :name)'
            scan_params['ExpressionAttributeNames'] = {'#name': 'name'}
            scan_params['ExpressionAttributeValues'] = {':name': name_filter}
        logger.info(f"DynamoDB scan parameters: {scan_params}")

        # Log table name being accessed
        logger.info(f"Accessing DynamoDB table: {os.environ['PRODUCTS_TABLE']}")

        # Scan DynamoDB table
        response = table.scan(**scan_params)
        products = response.get('Items', [])
        logger.info(f"Found {len(products)} products")

        # Format products according to the API schema
        formatted_products = [
            {
                'name': product['name'],
                'description': product['description'],
                'price': float(product['price'])  # Convert Decimal to float for JSON serialization
            }
            for product in products
        ]
        
        logger.info(f"Returning {len(formatted_products)} formatted products")
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'products': formatted_products
            })
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        } 