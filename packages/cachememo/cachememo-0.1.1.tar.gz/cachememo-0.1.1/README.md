# cachememo

Tiny, safe memoization for Python - with TTL and async support.

`cachememo` helps you cache the results of expensive functions **without accidentally shooting yourself in the foot under concurrency**.

It’s designed for when:

- you need **time-based expiration (TTL)**
- you are working with **async functions**
- you want to avoid **cache stampedes** under load

---
### Installation

```bash
pip install cachememo
```

---

### Basic Usage
```py
from cachememo import memoize

@memoize(ttl=60)
def expensive(x: int) -> int:
    return x * 2

@memoize(ttl=30)
async def fetch_user(uid: str) -> dict:
    ...
```
---
## License

MIT
