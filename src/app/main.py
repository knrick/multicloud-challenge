from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.product_service import ProductService
from core.security import verify_admin

app = FastAPI(
    title="CloudMart",
    description="MultiCloud E-commerce Platform",
    version="0.1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Public routes
@app.get("/")
async def home_page(request: Request):
    """Serve the home page"""
    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )

# Protected routes
@app.get("/products")
async def products_page(request: Request, username: str = Depends(verify_admin)):
    """Serve the products management page (protected)"""
    product_service = ProductService()
    products = await product_service.list_products()
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": products, "username": username}
    )

# Import routers
from api import products, orders, tickets

# Include routers with authentication
app.include_router(
    products.router,
    prefix="/api/products",
    tags=["products"],
    dependencies=[Depends(verify_admin)]  # Protect all product endpoints
)
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 