import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from models.order import Order
import json
import logging
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self):
        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.table = self.dynamodb.Table('cloudmart-orders')
            logger.info("OrderService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OrderService: {str(e)}")
            raise

    async def create_order(self, order: Order) -> Order:
        """Create a new order"""
        try:
            order_data = json.loads(order.model_dump_json())
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.table.put_item(Item=order_data)
            )
            return order
        except ClientError as e:
            logger.error(f"Error creating order: {e.response['Error']['Message']}")
            raise

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.table.get_item(Key={'id': order_id})
            )
            item = response.get('Item')
            return Order(**item) if item else None
        except ClientError as e:
            logger.error(f"Error getting order: {e.response['Error']['Message']}")
            return None

    async def get_user_orders(self, user_email: str) -> List[Order]:
        """Get all orders for a user"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.table.scan(
                    FilterExpression='userEmail = :email',
                    ExpressionAttributeValues={':email': user_email}
                )
            )
            items = response.get('Items', [])
            return [Order(**item) for item in items]
        except ClientError as e:
            logger.error(f"Error getting user orders: {e.response['Error']['Message']}")
            return []

    async def update_order_status(self, order_id: str, status: str) -> Optional[Order]:
        """Update order status"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.table.update_item(
                    Key={'id': order_id},
                    UpdateExpression='set #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': status},
                    ReturnValues='ALL_NEW'
                )
            )
            updated_item = response.get('Attributes')
            return Order(**updated_item) if updated_item else None
        except ClientError as e:
            logger.error(f"Error updating order: {e.response['Error']['Message']}")
            return None

    async def delete_order(self, order_id: str) -> bool:
        """Delete an order"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.table.delete_item(Key={'id': order_id})
            )
            return True
        except ClientError as e:
            logger.error(f"Error deleting order: {e.response['Error']['Message']}")
            return False

    async def cancel_order(self, order_id: str) -> Optional[Order]:
        """Cancel an order"""
        return await self.update_order_status(order_id, 'Canceled') 