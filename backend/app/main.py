from scraper import scrape_all
from fastapi import FastAPI
from fastapi.responses import FileResponse
import threading
from contextlib import asynccontextmanager
import logging

mem = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start scraper in background thread"""
    thread = threading.Thread(target=run_scraper, daemon=True)
    thread.start()
    logger.info("Hello World")
    yield


def run_scraper():
    """Run scraper in a separate thread"""
    global mem
    mem = scrape_all()


app = FastAPI(lifespan=lifespan)


@app.get("/api/cards")
def get_cards():
    """returns the current card prices stored in memory"""
    if mem is None:
        return {"message": "Scraping in progress, please wait..."}
    return mem


@app.get("/")
def serve_frontend():
    """Serve the frontend index.html file"""
    return FileResponse("../../frontend/index.html")
