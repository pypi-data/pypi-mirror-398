from dataclasses import dataclass


@dataclass(frozen=True)
class Composer:
    id: int
    name: str
    birth: str | None
    death: str | None
    epoch: str
    portrait: str | None


@dataclass(frozen=True)
class Work:
    id: int
    title: str
    genre: str
