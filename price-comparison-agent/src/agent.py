class PriceComparisonAgent:
    def __init__(self):
        self.scrapers = {
            'amazon': AmazonScraper(),
            'ebay': EbayScraper(),
            'currys': CurrysScraper()
        }

    def search_item(self, item_name):
        results = {}
        for site, scraper in self.scrapers.items():
            prices = scraper.search(item_name)
            results[site] = prices
        return results

    def find_cheapest(self, item_name):
        results = self.search_item(item_name)
        cheapest_price = float('inf')
        cheapest_site = None

        for site, prices in results.items():
            for price in prices:
                if price < cheapest_price:
                    cheapest_price = price
                    cheapest_site = site

        return cheapest_site, cheapest_price

# Note: AmazonScraper, EbayScraper, and CurrysScraper classes should be defined in their respective modules.