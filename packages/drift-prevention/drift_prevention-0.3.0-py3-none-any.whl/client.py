import requests

class Client:
    def __init__(self, api_key: str, base_url="https://api.twojaapp.com"):
        self.api_key = api_key
        self.base_url = base_url

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt: str):
        res = requests.post(
            f"{self.base_url}/v1/generate",
            headers=self._headers(),
            json={"prompt": prompt},
            timeout=10
        )

        if res.status_code != 200:
            raise Exception(res.text)

        return res.json()
