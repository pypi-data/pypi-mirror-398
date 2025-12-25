import requests
from .errors import OpenOpusError

BASE_URL = "https://api.openopus.org"
PERIODS = {"Medieval", "Renaissance", "Baroque", "Classical", "Early Romantic",
           "Romantic", "Late Romantic", "20th Century", "Post-War", "21st Century"}


class OpenOpusClient:
    def __init__(self, timeout=5):
        self.timeout = timeout

    def get(self, path, params=None):
        r = requests.get(BASE_URL + path, params=params, timeout=self.timeout)
        if r.status_code != 200:
            raise OpenOpusError(r.status_code)
        return r.json()

    def list_composers(self):
        return self.get("/composer/list/search/.json")

    def search_composers(self, name):
        return self.get(f"/composer/list/search/{name}.json")

    def composers_by_period(self, period):
        if period not in PERIODS:
            raise OpenOpusError(f"Invalid period; must be one of {PERIODS}")
        return self.get(f"/composer/list/epoch/{period}.json")

    def get_composer(self, composer_id):
        return self.get(f"/composer/list/id/{composer_id}.json")

    def works_by_composer(self, composer_id):
        return self.get(f"/work/list/composer/{composer_id}/genre/all.json")

    def work_detail(self, work_id):
        return self.get(f"/work/detail/{work_id}.json")
