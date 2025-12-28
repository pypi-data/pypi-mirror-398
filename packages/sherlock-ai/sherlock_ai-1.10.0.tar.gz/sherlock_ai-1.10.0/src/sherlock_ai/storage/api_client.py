import requests
import os
from sherlock_ai.config import SHERLOCK_AI_API_BASE_URL, INJEST_LOGS_ENDPOINT, INJEST_PERFORMANCE_INSIGHTS_ENDPOINT

class ApiClient:
    def __init__(self):
        self.api_key = os.getenv("SHERLOCK_AI_API_KEY")
        if not self.api_key:
            raise ValueError("SHERLOCK_AI_API_KEY is not set")
        self.client = requests.Session()

    def post_error_insights(self, data: dict):
        data["api_key"] = self.api_key
        response = self.client.post(
            url=SHERLOCK_AI_API_BASE_URL + "/" + INJEST_LOGS_ENDPOINT,
            json=data
        )
        return response.json()

    def post_performance_insights(self, data: dict):
        data["api_key"] = self.api_key
        response = self.client.post(
            url=SHERLOCK_AI_API_BASE_URL + "/" + INJEST_PERFORMANCE_INSIGHTS_ENDPOINT,
            json=data
        )
        return response.json()