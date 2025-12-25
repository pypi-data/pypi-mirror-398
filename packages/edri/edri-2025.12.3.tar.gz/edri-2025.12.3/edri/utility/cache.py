from collections import defaultdict
from datetime import datetime
from pytz import timezone


class Cache:
    timezone = timezone("Europe/Prague")

    def __init__(self):
        self.last_modified = defaultdict(lambda: datetime.now(tz=self.timezone))

    def last_change(self, key: str) -> datetime:
        return self.last_modified[key]

    def tag(self, key: str) -> str:
        return f"{key}-{int(self.last_change(key).timestamp())}"

    def renew(self, key: str) -> None:
        self.last_modified[key] = datetime.now(tz=self.timezone)