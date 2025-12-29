from .base import ScrapperBase


class CostcoScrapper(ScrapperBase):
    domain: str = 'costco.com'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expected_columns = [
            'brand_name',
            'brand_image',
            'short_name',
            'brand_description',
        ]
        # self.url: str = 'https://www.costco.com/special-events.html'
        self.url: str = None
        self.use_proxy = True
        self.us_proxy = True
        self._free_proxy = False
        # self.use_edge = True
        # self.use_firefox = True
        self.headless = False
        # self._browser_binary = '/opt/google/chrome/chrome'
        # self._driver_binary = '/home/jesuslara/.cache/selenium/geckodriver/linux64/0.33.0/geckodriver'

    async def connect(self):
        """Creates the Driver and Connects to the Site.
        """
        self._driver = await self.get_driver()
        await self.start()

    async def disconnect(self):
        """Disconnects the Driver and closes the Connection.
        """
        if self._driver:
            self.close_driver()

    async def special_events(self, response: object, idx: int, row: dict) -> tuple:
        """
        Get the special events from Costco.
        """
        try:
            document = self.get_bs(response)
            category_header = document.find('div', {'id': 'category-name-header'})
            print('category_header > ', category_header)
            return idx, row
        except Exception as err:
            self._logger.error(f'Error getting special events from Costco: {err}')
            return None

    async def product_information(self, response: object, idx: int, row: dict) -> tuple:
        """
        Get the product information from Costco.
        """
        try:
            document = self.get_bs(response)
            search_results_div = document.find('div', {'id': 'search-results'})
            if search_results_div:
                # 1. Get the brand name: find the <div> with class "search-results-tile", then the first <h1>
                search_results_tile = search_results_div.find('div', class_="search-results-tile")
                brand_name = None
                if search_results_tile:
                    h1_tag = search_results_tile.find('h1')
                    if h1_tag:
                        brand_name = h1_tag.get_text(strip=True)
                        row['brand_name'] = brand_name
                # 2. Get the brand image: find the <div> with class "dual-row", then find the <img> with class "img-responsive"
                dual_row_div = search_results_div.find('div', class_="dual-row")
                brand_image = None
                if dual_row_div:
                    img_tag = dual_row_div.find('img', class_="img-responsive")
                    if img_tag and img_tag.has_attr('src'):
                        brand_image = img_tag['src']
                        row['brand_image'] = brand_image
                # 3. Get the brand description: find the <div> with class "sp-event-product-copy" then its first <p>
                copy_div = search_results_div.find('div', class_="sp-event-product-copy")
                brand_description = None
                if copy_div:
                    p_tag = copy_div.find('p')
                    if p_tag:
                        brand_description = p_tag.get_text(strip=True)
                        row['brand_description'] = brand_description
                # 4. Get the short name: find the <div> with class "search-results-tile",
                _div = search_results_div.find('div', class_="sp-event-product-title")
                short_name = None
                if _div:
                    short_name = _div.get_text(strip=True)
                    row['short_name'] = short_name
            return idx, row
        except Exception as err:
            self._logger.error(f'Error getting product information from Costco: {err}')
            return None
