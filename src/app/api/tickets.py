from fastapi import APIRouter, HTTPException, Form
from typing import List
from models.ticket import Ticket
from services.ticket_service import TicketService
from fastapi.responses import RedirectResponse

router = APIRouter()
ticket_service = TicketService()

@router.get("/", response_model=List[Ticket])
async def list_tickets():
    """List all tickets"""
    return await ticket_service.list_tickets()

@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    """Get a specific ticket"""
    ticket = await ticket_service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.post("/")
async def create_ticket(message: str = Form(...)):
    """Create a new ticket with initial message"""
    try:
        await ticket_service.create_ticket(message)
        return RedirectResponse(url="/tickets", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{ticket_id}/message")
async def send_message(ticket_id: str, message: str = Form(...)):
    """Send a message to an existing ticket"""
    try:
        ticket = await ticket_service.send_message(ticket_id, message)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found or closed")
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{ticket_id}/close")
async def close_ticket(ticket_id: str):
    """Close a ticket"""
    ticket = await ticket_service.close_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket 