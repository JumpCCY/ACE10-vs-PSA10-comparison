from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import numpy as np


def main():
    search_query = input("Enter the item you want to search for: ")
    search_query = search_query.strip()
    search_query = search_query.replace(" ", "+")
    url = f"https://www.ebay.co.uk/sch/i.html?_nkw={search_query}+psa+10&_sacat=0&_from=R40&LH_Sold=1&rt=nc&LH_PrefLoc=1"

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
    print(f"Average price for '{search_query}': £{average_price:.2f}")


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
