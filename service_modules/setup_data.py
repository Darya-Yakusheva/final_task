class Cities:
    """Class to store city information for work"""

    domain = "https://www.domofond.ru/"
    data = {
        "ekb": {
            "name": "ekaterinburg",
            "search_url": f"{domain}prodazha-kvartiry-ekaterinburg-c2653",
            "center_coordinates": [56.839103, 60.60825],
        },
        "msk": {
            "name": "moscow",
            "search_url": f"{domain}prodazha-kvartiry-moskva-c3584",
            "center_coordinates": [55.751615, 37.618701],
        },
        "spb": {
            "name": "saint_petersburg",
            "search_url": f"{domain}prodazha-kvartiry-sankt_peterburg-c3414",
            "center_coordinates": [59.939366, 30.315363],
        },
    }

    def __init__(self, city):
        self.name = self.data[city]["name"]
        self.search_url = self.data[city]["search_url"]
        self.center_coordinates = self.data[city]["center_coordinates"]
