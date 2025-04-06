from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from models.order import Order
from services.order_service import OrderService
from core.security import verify_admin
from fastapi.responses import RedirectResponse

router = APIRouter()
order_service = OrderService()

@router.post("/", response_model=Order)
async def create_order(order: Order):
    """Create a new order"""
    try:
        return await order_service.create_order(order)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[Order])
async def get_user_orders(user_email: str):
    """Get all orders for a user"""
    return await order_service.get_user_orders(user_email)

@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Get an order by ID"""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.put("/{order_id}/status", response_model=Order)
async def update_order_status(order_id: str, status: str, _: str = Depends(verify_admin)):
    """Update order status (admin only)"""
    order = await order_service.update_order_status(order_id, status)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.delete("/{order_id}")
async def delete_order(order_id: str, _: str = Depends(verify_admin)):
    """Delete an order (admin only)"""
    success = await order_service.delete_order(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}

@router.post("/{order_id}/cancel", response_model=Order)
async def cancel_order(order_id: str):
    """Cancel an order"""
    order = await order_service.cancel_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.get("/")
async def list_orders():
    """List all orders - To be implemented"""
    return {"message": "Orders endpoint - Coming soon"} 