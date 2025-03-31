import os
import json
import boto3
from typing import Dict, List, Any

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['PRODUCTS_TABLE'])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to list products from DynamoDB.
    Can filter by name if provided in the query parameters.
    """
    try:
        # Get query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        name_filter = query_params.get('name')

        # Prepare scan parameters
        scan_params = {}
        if name_filter:
            scan_params['FilterExpression'] = 'contains(#name, :name)'
            scan_params['ExpressionAttributeNames'] = {'#name': 'name'}
            scan_params['ExpressionAttributeValues'] = {':name': name_filter}

        # Scan DynamoDB table
        response = table.scan(**scan_params)
        products = response.get('Items', [])

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'products': products,
                'count': len(products)
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e)
            })
        } 