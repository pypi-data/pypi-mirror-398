import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

DEFAULT_TIMEOUT = (2, 5)  # (connect_timeout, read_timeout) -> total ≤ ~5s


def safe_get_json(url, headers=None, timeout=DEFAULT_TIMEOUT):
    try:
        r = requests.get(url, headers=headers or {}, timeout=timeout)
        if r.ok:
            return r.json(), None
        return None, f"HTTP {r.status_code}"
    except (Timeout, ConnectionError) as e:
        return None, f"timeout/conn error: {e}"
    except RequestException as e:
        return None, f"request error: {e}"
    except ValueError as e:  # JSON decode
        return None, f"json decode error: {e}"


def safe_post_json(url, payload, headers=None, timeout=DEFAULT_TIMEOUT):
    try:
        r = requests.post(url, json=payload, headers=headers or {}, timeout=timeout)
        return r, None
    except (Timeout, ConnectionError) as e:
        return None, f"timeout/conn error: {e}"
    except RequestException as e:
        return None, f"request error: {e}"
