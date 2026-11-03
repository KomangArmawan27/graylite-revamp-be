import logging
import time

logger = logging.getLogger("erp-api")

class Replay:
    def __init__(self, status: int, body: bytes, headers: dict):
        self.status = status
        self.body = body
        self.headers = headers

class InFlight:
    pass

class New:
    pass

class InMemoryIdempotencyStore:
    def __init__(self):
        self._store: dict[str, tuple[str, str, int, bytes, dict, float]] = {}
        self._in_flight: dict[str, float] = {}

    def begin(self, key: str, user_id: int, route: str, body_hash: str) -> Replay | InFlight | New | str:
        now = time.time()
        self._cleanup(now)
        composite_key = f"{user_id}:{route}:{key}"
        
        if composite_key in self._in_flight:
            if now - self._in_flight[composite_key] < 30:
                return InFlight()
            else:
                del self._in_flight[composite_key]

        if composite_key in self._store:
            stored_user_id, stored_hash, status, body, headers, ts = self._store[composite_key]
            if stored_hash != body_hash:
                return "conflict_body"
            return Replay(status, body, headers)

        self._in_flight[composite_key] = now
        return New()

    def finish(self, key: str, user_id: int, route: str, body_hash: str, status: int, body: bytes, headers: dict) -> None:
        now = time.time()
        composite_key = f"{user_id}:{route}:{key}"
        if composite_key in self._in_flight:
            del self._in_flight[composite_key]
        if 200 <= status < 300:
            self._store[composite_key] = (str(user_id), body_hash, status, body, headers, now)

    def _cleanup(self, now: float):
        expired = [k for k, v in self._store.items() if now - v[5] > 86400]
        for k in expired:
            del self._store[k]

idempotency_store = InMemoryIdempotencyStore()
