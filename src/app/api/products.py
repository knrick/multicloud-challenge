from fastapi import APIRouter, HTTPException
from typing import List
from models.product import Product, ProductCreate
from services.product_service import ProductService

router = APIRouter()
product_service = ProductService()

@router.get("/", response_model=List[Product])
async def list_products():
    """List all products"""
    return await product_service.list_products()

@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get a specific product by ID"""
    product = await product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=Product)
async def create_product(product: ProductCreate):
    """Create a new product"""
    return await product_service.create_product(product)

@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: str, product: ProductCreate):
    """Update an existing product"""
    updated_product = await product_service.update_product(product_id, product)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.delete("/{product_id}")
async def delete_product(product_id: str):
    """Delete a product"""
    success = await product_service.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"} 