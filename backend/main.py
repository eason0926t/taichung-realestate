# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import listings, prices, scraper as scraper_router
from backend.services.scheduler import create_scheduler

scheduler = create_scheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="台中房地產資訊網 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings.router, prefix="/api")
app.include_router(prices.router, prefix="/api")
app.include_router(scraper_router.router, prefix="/api")
