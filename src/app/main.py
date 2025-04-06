from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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

# Import routers
from api import products, orders, tickets, ai
from routes import web

# Include web routes
app.include_router(web.router)

# Include API routers with authentication
app.include_router(
    products.router,
    prefix="/api/products",
    tags=["products"],
    dependencies=[Depends(verify_admin)]  # Protect all product endpoints
)
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 