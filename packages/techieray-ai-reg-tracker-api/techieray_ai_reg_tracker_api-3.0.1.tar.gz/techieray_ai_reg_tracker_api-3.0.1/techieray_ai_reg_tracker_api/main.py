import requests
import json

class GlobalAIRegulationTrackerClient:
    """
    A client library for interacting with a Firebase HTTPS function.
    """

    def __init__(self, api_key=None):
        self.function_url = "https://globalairegtrackerapi-j66zxhj6dq-uc.a.run.app"
        self.api_key = api_key

    def call(self, market, target_news, target_date, lang_code):
        payload = {    
            "countryCode": market,
            "targetNews": target_news,
            "targetDate": target_date,
            "apiKey": self.api_key,
            "langCode": lang_code
        }

        try:
            response = requests.post(
                self.function_url, 
                json = payload
            )
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            try:
                return response.json()
            except ValueError:
                return response.text #return the text if it is not json.

        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Error calling API: {e}")
