import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from models.product import Product, ProductCreate
import os
import json

class ProductService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('cloudmart-products')

    async def list_products(self) -> List[Product]:
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            return [Product(**item) for item in items]
        except ClientError as e:
            print(f"Error scanning products: {e.response['Error']['Message']}")
            return []

    async def get_product(self, product_id: str) -> Optional[Product]:
        try:
            response = self.table.get_item(Key={'id': product_id})
            item = response.get('Item')
            return Product(**item) if item else None
        except ClientError as e:
            print(f"Error getting product: {e.response['Error']['Message']}")
            return None

    async def create_product(self, product: ProductCreate) -> Product:
        new_product = Product(**product.model_dump())
        try:
            self.table.put_item(Item=json.loads(new_product.model_dump_json()))
            return new_product
        except ClientError as e:
            print(f"Error creating product: {e.response['Error']['Message']}")
            raise

    async def update_product(self, product_id: str, product: ProductCreate) -> Optional[Product]:
        try:
            # Check if product exists
            if not await self.get_product(product_id):
                return None
            
            updated_product = Product(id=product_id, **product.model_dump())
            self.table.put_item(Item=json.loads(updated_product.model_dump_json()))
            return updated_product
        except ClientError as e:
            print(f"Error updating product: {e.response['Error']['Message']}")
            return None

    async def delete_product(self, product_id: str) -> bool:
        try:
            # Check if product exists
            if not await self.get_product(product_id):
                return False
            
            self.table.delete_item(Key={'id': product_id})
            return True
        except ClientError as e:
            print(f"Error deleting product: {e.response['Error']['Message']}")
            return False 