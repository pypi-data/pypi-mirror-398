from .client import OpenOpusClient
from .cache import TTLCache
from .models import Composer, Work


class OpenOpus:
    def __init__(self, cache=None):
        self.client = OpenOpusClient()
        self.cache = cache or TTLCache(3600)

    def list_composers(self) -> list[Composer]:
        """Returns all composeres as normalized Composer objects"""
        key = "composers"
        cached = self.cache.get(key)
        if cached: return cached

        data = self.client.list_composers()
        composers = [
            Composer(
                id=int(c["id"]),
                name=c["complete_name"],
                birth=c["birth"] if c["birth"] else None,
                death=c["death"] if c["death"] else None,
                epoch=c["epoch"],
                portrait=c["portrait"] if c["portrait"] else None,
            )
            for c in data["composers"]
        ]

        self.cache.set(key, composers)
        return composers

    def get_composer(self, composer_id: int) -> Composer | None:
        """Returns a single Composer by ID"""
        key = f"composer:{composer_id}"
        cached = self.cache.get(key)
        if cached: return cached

        data = self.client.get_composer(composer_id)
        composer = Composer(
            id=int(data["composers"]["id"]),
            name=data["composers"]["name"],
            birth=data["composers"]["birth"] if data["composers"]["birth"] else None,
            death=data["composers"]["death"] if data["composers"]["death"] else None,
            epoch=data["composers"]["epoch"],
            portrait=data["composers"]["portrait"] if data["composers"]["portrait"] else None,
        )

        return composer

    def search_composers(self, name: str) -> list[Composer]:
        """Returns all composers matching the given name"""
        key = f"composers:{name}"
        cached = self.cache.get(key)
        if cached: return cached

        data = self.client.search_composers(name)
        composers = [
            Composer(
                id=int(c["id"]),
                name=c["complete_name"],
                birth=c["birth"] if c["birth"] else None,
                death=c["death"] if c["death"] else None,
                epoch=c["epoch"],
                portrait=c["portrait"] if c["portrait"] else None,
            )
            for c in data["composers"]
        ]

        self.cache.set(key, composers)
        return composers

    def composers_by_period(self, period: str) -> list[Composer]:
        """
        Returns composers matching the specific classical period
        
        Valid Periods:
        - Medieval
        - Renaissance
        - Baroque
        - Classical
        - Early Romantic
        - Romantic
        - Late Romantic
        - 20th Century
        - Post-War
        - 21st Century
        """
        key = f"composers:{period}"
        cached = self.cache.get(key)
        if cached: return cached

        data = self.client.composers_by_period(period)
        composers = [
            Composer(
                id=int(c["id"]),
                name=c["complete_name"],
                birth=c["birth"] if c["birth"] else None,
                death=c["death"] if c["death"] else None,
                epoch=c["epoch"],
                portrait=c["portrait"] if c["portrait"] else None,
            )
            for c in data["composers"]
        ]

        self.cache.set(key, composers)
        return composers

    def works_by_composer(self, composer_id: int) -> list[Work]:
        """Returns all works by a composer based on their composer ID"""
        key = f"works:{composer_id}"
        cached = self.cache.get(key)
        if cached: return cached

        data = self.client.works_by_composer(composer_id)
        works = [
            Work(
                id=w["id"],
                title=w["title"],
                genre=w["genre"],
            )
            for w in data["works"]
        ]

        self.cache.set(key, works)
        return works
