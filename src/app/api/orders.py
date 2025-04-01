from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_orders():
    """List all orders - To be implemented"""
    return {"message": "Orders endpoint - Coming soon"} 