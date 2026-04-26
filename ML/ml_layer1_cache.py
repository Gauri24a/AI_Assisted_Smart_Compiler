class StatementCache:
    def __init__(self):
        self._cache = {}
        self._hits  = 0
        self._total = 0

    def get(self, key):
        self._total += 1
        node = self._cache.get(key)
        if node is not None:
            self._hits += 1
        return node

    def put(self, key, node):
        self._cache[key] = node

    @property
    def hit_rate(self):
        return self._hits / self._total if self._total else 0.0

    def stats(self):
        return {"hits": self._hits, "total": self._total, "hit_rate": self.hit_rate}