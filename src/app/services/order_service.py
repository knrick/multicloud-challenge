import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
import json

class OrderService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('cloudmart-orders')

    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get an order by ID"""
        try:
            response = self.table.get_item(Key={'id': order_id})
            return response.get('Item')
        except ClientError as e:
            print(f"Error getting order: {e.response['Error']['Message']}")
            return None

    async def delete_order(self, order_id: str) -> bool:
        """Delete an order"""
        try:
            self.table.delete_item(Key={'id': order_id})
            return True
        except ClientError as e:
            print(f"Error deleting order: {e.response['Error']['Message']}")
            return False

    async def cancel_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Cancel an order by updating its status"""
        try:
            # Get current order
            order = await self.get_order(order_id)
            if not order:
                return None
            
            # Update status to canceled
            order['status'] = 'canceled'
            self.table.put_item(Item=order)
            return order
        except ClientError as e:
            print(f"Error canceling order: {e.response['Error']['Message']}")
            return None 