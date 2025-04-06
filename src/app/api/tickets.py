from fastapi import APIRouter, HTTPException, Form
from typing import List
from models.ticket import Ticket
from services.ticket_service import TicketService
from services.ai_service import AIService
from fastapi.responses import RedirectResponse

router = APIRouter()
ticket_service = TicketService()
ai_service = AIService()

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
        ticket = await ticket_service.create_ticket(message)
        return RedirectResponse(url=f"/tickets?ticket_id={ticket.id}", status_code=303)
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
    """Close a ticket and analyze sentiment"""
    try:
        # First, get the ticket to analyze
        ticket = await ticket_service.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Analyze sentiment
        sentiment_result = await ai_service.analyze_sentiment_and_save({
            "id": ticket.id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                } for msg in ticket.messages
            ]
        })

        # Update ticket with sentiment data
        updated_ticket = await ticket_service.update_ticket_sentiment(ticket_id, sentiment_result)
        if not updated_ticket:
            raise HTTPException(status_code=400, detail="Failed to update ticket sentiment")

        # Close the ticket
        closed_ticket = await ticket_service.close_ticket(ticket_id)
        if not closed_ticket:
            raise HTTPException(status_code=400, detail="Failed to close ticket")

        # Redirect back to the ticket page
        return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: str):
    """Delete a ticket"""
    try:
        # First check if ticket exists
        ticket = await ticket_service.get_ticket(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Delete the ticket
        success = await ticket_service.delete_ticket(ticket_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete ticket")

        return {"message": "Ticket deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 