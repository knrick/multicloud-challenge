from fastapi import APIRouter, HTTPException, Form
from typing import List
from models.ticket import Ticket, TicketCreate
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
async def create_ticket(
    title: str = Form(...),
    description: str = Form(...)
):
    """Create a new ticket"""
    try:
        ticket_data = TicketCreate(
            title=title,
            description=description
        )
        await ticket_service.create_ticket(ticket_data)
        return RedirectResponse(url="/tickets", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{ticket_id}/message")
async def send_message(
    ticket_id: str,
    message: str = Form(...)
):
    """Send a message to an existing ticket"""
    try:
        ticket = await ticket_service.continue_conversation(ticket_id, message)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return RedirectResponse(url="/tickets", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{ticket_id}", response_model=Ticket)
async def update_ticket(ticket_id: str, status: str):
    """Update ticket status"""
    updated_ticket = await ticket_service.update_ticket(ticket_id, status)
    if not updated_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return updated_ticket 