
import requests, time
_CACHE = {}
def get_jwks(issuer):
    url = issuer.rstrip("/") + "/.well-known/jwks.json"
    if url not in _CACHE:
        _CACHE[url] = requests.get(url).json()["keys"]
    return _CACHE[url]
