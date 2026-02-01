import requests
import base64

CLIENT_ID = "[EBAY-CLIENT-ID]"
CLIENT_SECRET = "[EBAY-CLIENT-SECRET]"
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
    "9.5"
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
    if not card_name:
        print("Please provide a card name.")
        return
    access_token = get_access_token()
    results_ACE10 = ebay_search(access_token, f"{card_name} ACE 10")
    results_PSA10 = ebay_search(access_token, f"{card_name} PSA 10")
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
    encoded_credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    response = requests.post(url="https://api.ebay.com/identity/v1/oauth2/token", headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    },
    data={
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    })
    return response.json()["access_token"]

def ebay_search(access_token:str, query: str):
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
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_GB"
        },
        params={
            "q": query,
            "limit": "10",
            "sort": "price"
        }
    )
    list_of_items = response.json() # if itemSummaries not in response.json() use empty list instead

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
    elif query.endswith("PSA 10"):
        return float(average_price)

    return price_list
if __name__ == "__main__":
    main()