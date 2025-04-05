from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.order_service import OrderService

router = APIRouter()
order_service = OrderService()

@router.get("/orders/{order_id}")
async def get_order(order_id: str) -> Dict[str, Any]:
    """Get an order by ID"""
    order = await order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.delete("/orders/{order_id}")
async def delete_order(order_id: str) -> Dict[str, str]:
    """Delete an order"""
    success = await order_service.delete_order(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found or could not be deleted")
    return {"message": "Order deleted successfully"}

@router.put("/orders/{order_id}/cancel")
async def cancel_order(order_id: str) -> Dict[str, Any]:
    """Cancel an order"""
    order = await order_service.cancel_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found or could not be canceled")
    return order

@router.get("/")
async def list_orders():
    """List all orders - To be implemented"""
    return {"message": "Orders endpoint - Coming soon"} 