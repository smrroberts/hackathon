from bs4 import BeautifulSoup
import requests

class EbayScraper:
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"

    def search_item(self, item_name):
        params = {
            "_nkw": item_name
        }
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text

    def parse_prices(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='s-item__info')
        prices = []

        for item in items:
            title = item.find('h3', class_='s-item__title')
            price = item.find('span', class_='s-item__price')

            if title and price:
                prices.append({
                    'title': title.get_text(),
                    'price': price.get_text()
                })

        return prices

    def get_prices(self, item_name):
        html = self.search_item(item_name)
        return self.parse_prices(html)