import requests
import base64
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import numpy as np


CLIENT_ID = "[Client ID here]"
CLIENT_SECRET = "[Client secret here]"
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


def main():
    """
    Main function to run the eBay card price comparison tool.
    1. Prompts the user for a card name.
    2. Retrieves an access token for the eBay API.
    3. Searches for ACE 10 and PSA 10 prices for the given card.
    4. Displays the average prices and potential profit.
    """
    card_name = input("Card name: ")
    card_name = card_name.strip()
    if not card_name:
        print("Please provide a card name.")
        return
    access_token = get_access_token()
    results_ACE10 = ebay_search(access_token, f"{card_name} ACE 10")
    results_PSA10 = ebay_average_sold(f"{card_name} PSA 10")
    if results_ACE10 == 0:
        print(f"Average listing price for {card_name}")
        print(f"ACE 10: No results found")
        print(f"PSA 10: £{results_PSA10:.2f}")
    elif results_PSA10 == 0:
        print(f"Average listing price for {card_name}")
        print(f"ACE 10: £{results_ACE10:.2f}")
        print(f"PSA 10: No results found")
    else:
        print(f"Average listing price for {card_name}")
        print(f"ACE 10: £{results_ACE10:.2f}")
        print(f"PSA 10: £{results_PSA10:.2f}")
        print(f"Potential Profit: £{results_PSA10 - results_ACE10:.2f}")


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


def ebay_search(access_token: str, query: str):
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
            "Authorization": f"Bearer {access_token}",
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
            if bad.lower() in title.lower():
                del price_list[title]

    sum = 0
    for price in price_list.values():
        sum += float(price)
    average_price = sum / len(price_list) if price_list else 0

    if query.endswith("ACE 10"):
        res = list(price_list.values())[0]
        return float(res)


def ebay_average_sold(query: str) -> float:
    """
    Docstring for ebay_average_sold

    :param query: search for recently sold item on eBay and return the average price
    :type query: str
    :return: Average price of recently 10 sold items
    :rtype: float
    """

    query = query.replace(" ", "+")
    url = f"https://www.ebay.co.uk/sch/i.html?_nkw={query}+psa+10&_sacat=0&_from=R40&LH_Sold=1&rt=nc&LH_PrefLoc=1"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector("li.s-card")
        html = page.content()

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("li.s-card")

    price_list = []
    for item in items[:10]:
        price = item.select_one(
            "span.su-styled-text.positive.bold.large-1.s-card__price"
        )
        if price is not None:
            price = price.get_text(strip=True)
            price = price.replace(",", "")
            price = price.replace("£", "")
            price_list.append(float(price))

    price_list = remove_outliners(price_list)
    average_price = sum(price_list) / len(price_list)
    return average_price


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
    main()
