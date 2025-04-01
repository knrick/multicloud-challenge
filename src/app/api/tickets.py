from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_tickets():
    """List all tickets - To be implemented"""
    return {"message": "Tickets endpoint - Coming soon"} 