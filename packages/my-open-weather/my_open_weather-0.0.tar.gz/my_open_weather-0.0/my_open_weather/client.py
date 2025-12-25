import requests


class OpenWeatherClient:
    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenWeather API key is empty or not provided")
        self.api_key = api_key

    def current_weather(self, city: str, units: str = "metric"):
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units,
        }
        response = requests.get(f"{self.BASE_URL}/weather", params=params)
        response.raise_for_status()
        return response.json()
