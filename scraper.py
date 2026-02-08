import requests
import base64
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import numpy as np
import datetime
import re


CLIENT_ID = ""
CLIENT_SECRET = ""
BAD_KEYWORDS = {
    "contender",
    "likely",
    "candidate",
    "possible",
    "looks",
    "would grade",
    "raw",
    "psa 9",
    "psa9",
    "equivalent",
    "9.5",
}

with open("top_chase.txt", "r") as file:
    TOP_CHASE = [line.strip() for line in file.readlines() if line.strip()]



class EbayScraper:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.page = self.browser.new_page()

    def stop(self):
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def ebay_search_ace10(self, query: str):
        """
        Docstring for ebay_search

        :param access_token: acess token for eBay API
        :type access_token: str
        :param query: search query which user wants to search for
        :type query: str
        """
        response = requests.get(
            url="https://api.ebay.com/buy/browse/v1/item_summary/search",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB",
            },
            params={"q": query, "limit": "10", "sort": "price"},
        )
        list_of_items = (
            response.json()
        )  # if itemSummaries not in response.json() use empty list instead

        price_list = {}
        for item in list_of_items.get("itemSummaries", []):
            if "JPN" not in query and "Japanaese" not in query:
                if "JPN" in item.get("title") or "Japanese" in item.get("title"):
                    continue
            title = item.get("title")
            price = item.get("price").get("value")
            price_list[title] = price

        # cleaning bad keywords
        for bad in BAD_KEYWORDS:
            for title in list(price_list.keys()):
                if (
                    bad.lower() in title.lower()
                    or "ACE 10" not in title
                    and "ACE10" not in title
                ):
                    del price_list[title]

        res = list(price_list.values())[0]
        return float(res)

    def ebay_average_sold(self, query: str) -> float:
        card_number = re.search(r'\d+$', query).group()
        query = query.replace(" ", "+")
        url = f"https://www.ebay.co.uk/sch/i.html?_nkw={query}+psa+10&_sacat=0&_from=R40&LH_Sold=1&rt=nc&LH_PrefLoc=1"

        self.page.goto(url)
        self.page.wait_for_selector("li.s-card")
        html = self.page.content()

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("li.s-card")

        price_list = {}
        for item in items[:10]:
            price = item.select_one(
                "span.su-styled-text.positive.bold.large-1.s-card__price"
            )
            name = item.select_one("span.su-styled-text.primary.default").text.strip()

            # regex to match card number and make sure it is PSA 10 in the title
            if re.search(rf"(?<!\d)#?\s?{card_number}(?:/\d+)?(?!\d)", name) and re.search(r"\bPSA[-\s]*10\b", name, re.IGNORECASE):
                price = price.get_text(strip=True)
                price = price.replace(",", "")
                price = price.replace("£", "")
                price_list[name] = float(price)

        price_list = remove_outliners(list(price_list.values()))
        average_price = sum(price_list) / len(price_list)
        return round(average_price, 2)



def scrape_all():
    """
    Main function to run the eBay card price comparison tool.
    1. Prompts the user for a card name.
    2. Retrieves an access token for the eBay API.
    3. Searches for ACE 10 and PSA 10 prices for the given card.
    4. Displays the average prices and potential profit.
    """
    access_token = get_access_token()
    search_instance = EbayScraper(access_token)
    search_instance.start()

    
    list_of_cards = []
    for card_name in TOP_CHASE:
        results_ACE10 = search_instance.ebay_search_ace10(f"{card_name} ACE 10")
        results_PSA10 = search_instance.ebay_average_sold(f"{card_name}")
        card = {
            "card_name": card_name,
            "ACE 10": results_ACE10,
            "PSA 10": results_PSA10,
            "Potential Profit": (
                round(results_PSA10 - results_ACE10, 2)
                if results_ACE10 and results_PSA10
                else None
            ),
        }
        list_of_cards.append(card)


        card_prices = {"total_cards": len(TOP_CHASE),
                   "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "cards": list_of_cards}

    search_instance.stop()

    return card_prices


def get_access_token() -> str:
    """
    Docstring for get_access_token

    :return: acess token for eBay API
    :rtype: str
    """
    encoded_credentials = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode()

    response = requests.post(
        url="https://api.ebay.com/identity/v1/oauth2/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}",
        },
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        },
    )
    return response.json()["access_token"]


def remove_outliners(price_list: list) -> list:
    """
    Docstring for remove_outliners

    :param price_list: Remove outliers from the price list using the IQR method
    :type price_list: list
    :return: list without outliers
    :rtype: list
    """
    data = np.array(price_list)
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return [x for x in price_list if lower <= x <= upper]


if __name__ == "__main__":
    print(scrape_all())
