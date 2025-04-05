import os
import json
import boto3
import logging
from typing import Dict, Any

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PRODUCTS_TABLE'])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to list products from DynamoDB for Bedrock agent integration.
    Can filter by name if provided in the parameters.
    Returns response in format expected by Bedrock agent.
    """
    try:
        # Log the incoming event
        logger.info(f"Received event from Bedrock: {json.dumps(event)}")
        
        # Get name parameter from Bedrock event
        name_filter = None
        if event.get('parameters'):
            for param in event['parameters']:
                if param.get('name') == 'name':
                    name_filter = param.get('value')
                    break
        logger.info(f"Name filter: {name_filter}")

        # Prepare scan parameters
        scan_params = {}
        if name_filter:
            scan_params['FilterExpression'] = 'contains(#name, :name)'
            scan_params['ExpressionAttributeNames'] = {'#name': 'name'}
            scan_params['ExpressionAttributeValues'] = {':name': name_filter}
        logger.info(f"DynamoDB scan parameters: {scan_params}")

        # Scan DynamoDB table
        response = table.scan(**scan_params)
        products = response.get('Items', [])
        logger.info(f"Found {len(products)} products")

        # Format products according to Bedrock agent schema
        formatted_products = [
            {
                'name': product['name'],
                'description': product['description'],
                'price': float(product['price'])  # Convert Decimal to float for JSON serialization
            }
            for product in products
        ]
        
        logger.info(f"Returning {len(formatted_products)} formatted products")
        # Return in format expected by Bedrock
        return {
            'messageVersion': event.get('messageVersion', '1.0'),
            'response': {
                'actionGroup': event.get('actionGroup'),
                'apiPath': event.get('apiPath'),
                'httpMethod': event.get('httpMethod'),
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(formatted_products)
                    }
                },
                'sessionAttributes': {},
                'promptSessionAttributes': {}
            }
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        # Return error in format expected by Bedrock
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', 'Get-Product-Recommendations'),
                'apiPath': event.get('apiPath', '/products'),
                'httpMethod': event.get('httpMethod', 'GET'),
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                },
                'sessionAttributes': {},
                'promptSessionAttributes': {}
            }
        } 