from collections import Counter


class CacheMetrics:
    def __init__(self):
        self.hits = Counter()
        self.misses = Counter()

    def hit(self, key_prefix: str):
        self.hits[key_prefix] += 1

    def miss(self, key_prefix: str):
        self.misses[key_prefix] += 1
