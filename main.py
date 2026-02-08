from scraper import scrape_all
from fastapi import FastAPI

app = FastAPI()

def routine_refresh():
    """
    Routine function to refresh the card prices every 24 hours.
    This function can be scheduled using a task scheduler like cron or APScheduler.
    """
    pass

@app.get("/api/cards")
def get_cards():
    pass