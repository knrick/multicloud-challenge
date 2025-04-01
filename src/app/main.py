from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.product_service import ProductService

app = FastAPI(
    title="CloudMart",
    description="MultiCloud E-commerce Platform",
    version="0.1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Template routes
@app.get("/products")
async def products_page(request: Request):
    """Serve the products page"""
    product_service = ProductService()
    products = await product_service.list_products()
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": products}
    )

# Import routers
from api import products, orders, tickets

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 