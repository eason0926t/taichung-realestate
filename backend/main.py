from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import listings, prices, scraper as scraper_router

app = FastAPI(title="台中房地產資訊網 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router, prefix="/api")
app.include_router(prices.router, prefix="/api")
app.include_router(scraper_router.router, prefix="/api")
