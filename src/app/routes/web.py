from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.order_service import OrderService
from services.ticket_service import TicketService
from services.product_service import ProductService
from core.security import verify_admin

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Serve the home page"""
    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )

@router.get("/tickets", response_class=HTMLResponse)
async def tickets_page(request: Request, ticket_id: str = None):
    """Serve the tickets list page with optional active ticket"""
    ticket_service = TicketService()
    tickets = await ticket_service.list_tickets()
    active_ticket = None
    if ticket_id:
        active_ticket = await ticket_service.get_ticket(ticket_id)
    return templates.TemplateResponse(
        "tickets.html",
        {
            "request": request, 
            "tickets": tickets,
            "active_ticket": active_ticket,
            "active_ticket_id": ticket_id
        }
    )

@router.get("/tickets/new", response_class=HTMLResponse)
async def new_ticket_page(request: Request):
    """Serve the new ticket page"""
    return templates.TemplateResponse(
        "ticket_conversation.html",
        {"request": request, "ticket": None}
    )

@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def ticket_conversation_page(request: Request, ticket_id: str):
    """Redirect to tickets page with active ticket"""
    return RedirectResponse(url=f"/tickets?ticket_id={ticket_id}")

@router.get("/products", response_class=HTMLResponse)
async def products_page(request: Request, username: str = Depends(verify_admin)):
    """Serve the products management page (protected)"""
    product_service = ProductService()
    products = await product_service.list_products()
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": products, "username": username}
    )

@router.get("/orders", response_class=HTMLResponse)
async def orders_page(
    request: Request,
    order_service: OrderService = Depends()
):
    """Serve the orders page"""
    # For demonstration purposes, use a mock user email
    mock_user_email = "demo@example.com"
    user_orders = await order_service.get_user_orders(mock_user_email)
    
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "orders": user_orders
        }
    ) 