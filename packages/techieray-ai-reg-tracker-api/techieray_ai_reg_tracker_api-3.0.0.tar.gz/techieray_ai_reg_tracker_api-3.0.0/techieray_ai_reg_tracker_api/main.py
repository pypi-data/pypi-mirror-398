import requests
import json

class GlobalAIRegulationTrackerClient:
    """
    A client library for interacting with a Firebase HTTPS function.
    """

    def __init__(self, api_key=None):
        self.function_url = "https://globalairegtrackerapi-j66zxhj6dq-uc.a.run.app"
        self.api_key = api_key
        print("NOTE: The following terms apply to your access and use of the API service to the Global AI Regulation Tracker, which was developed by Raymond Sun (techie_ray) (Developer)), during the free trial period (as indicated within the relevant API key provided by Developer). Developer retains all intellectual property rights in the API service, including the implementation code, the API key, and the outputs returned by the API (subject to any third party rights). Outputs returned by the API may contain links to third party sources (i.e. the \"href\" attribute in the output). Your access to those third party sources are at your own risk. The Developer does not claim copyright to those third party sources, but owns the copyright in the summary relating to the third party source (i.e. the \"desc\" attribute). You may use the API service (and its outputs), free of charge, solely for personal use or internal business use throughout the free trial period. At this stage, the API service is not designed (and therefore not allowed) for commercial use (such as use of the API service in your own services to your customers). API service is provided on 'as is' basis, without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and warranties of merchantability, fitness for a particular purpose and non-infringement. In no event will the Developer be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the API service. The Developer may modify or cancel any part of the API service without notice. Any feedback you provide to Developer about the API service will become the intellectual property of Developer. These terms are governed by the laws of New South Wales, Australia.")

    def call(self, market, target_news, target_date):
        payload = {    
            "countryCode": market,
            "targetNews": target_news,
            "targetDate": target_date,
            "apiKey": self.api_key 
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
