from scraper import scrape_all
from fastapi import FastAPI
from fastapi.responses import FileResponse
import threading
from contextlib import asynccontextmanager
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.staticfiles import StaticFiles

mem = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")


def run_scraper():
    """Run scraper in a separate thread"""
    global mem
    logger.info("Starting scrape...")
    mem = scrape_all()
    logger.info("Scrape complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start scraper immediately, then schedule it 3x/week"""
    thread = threading.Thread(target=run_scraper, daemon=True)
    thread.start()

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_scraper, "cron", day_of_week="mon,wed,fri", hour=2, minute=0)
    scheduler.start()
    logger.info("Scheduler started — scraping Mon, Wed, Fri at 02:00")

    yield

    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/api/cards")
def get_cards():
    """Returns the current card prices stored in memory"""
    if mem is None:
        return {"message": "Scraping in progress, please wait..."}
    return mem

app.mount("/", StaticFiles(directory="../../frontend", html=True), name="static")