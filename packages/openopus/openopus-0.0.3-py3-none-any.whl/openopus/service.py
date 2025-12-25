from .client import OpenOpusClient
from .cache import TTLCache
from .models import Composer, Work


class OpenOpus:
    """
    Open Opus Service

    :param cache: TTLCache instance, defaults to None
    :type cache: TTLCache, optional
    """
    def __init__(self, cache=None):
        """Constructor method"""
        self.client = OpenOpusClient()
        self.cache = cache or TTLCache(3600)

    def composers(self) -> list[Composer]:
        """
        Returns all composers

        :return: A list of Composer objects
        :rtype: list[Composer]
        """
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

    def composer(self, composer_id: int) -> Composer:
        """
        Returns a single Composer by ID

        :param composer_id: Composer ID
        :return: Composer object
        """
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

    def composers_by_name(self, name: str) -> list[Composer]:
        """
        Returns all composers matching the given name, a partial match search

        :param name: Name of composer
        :return: List of Composer objects
        """
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

        Use periods() to receive all valid periods

        :param period: Period of classical music
        :return: List of Composer objects
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

    def works(self, composer_id: int) -> list[Work]:
        """
        Returns all works by a composer based on their composer ID

        :param composer_id: Composer ID
        :return: List of Work objects
        """
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

    def periods(self) -> set[str]:
        """
        Returns all valid classical music periods

        :return: Set of valid periods
        """
        return self.client.get_periods()
