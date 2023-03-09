import json
from datetime import datetime
from os import getenv
from typing import Any

import requests

HEADER = {
        "Authorization": "Token <token>",
        "Accept": "application/json",
        "Content-type": "application/json"
    }

def prep_endpoint(endpoint: str | None) -> str:
    if endpoint is None:
        endpoint = ""
    endpoint = endpoint.lower()
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    return endpoint

def get(endpoint: str | None = None, params: dict | None = None) -> dict | None:
    if (PAPERLESS_URL := getenv("PAPERLESS_URL")) is None:
        raise EnvironmentError("No PAPERLESS_URL")
    if not PAPERLESS_URL.endswith("/"):
        PAPERLESS_URL = PAPERLESS_URL + "/"

    if (PAPERLESS_TOKEN := getenv("PAPERLESS_TOKEN")) is None:
        raise EnvironmentError("No PAPERLESS_TOKEN")
    else:
        HEADER["Authorization"] = HEADER["Authorization"].replace("<token>", PAPERLESS_TOKEN)

    req = requests.get(f"{PAPERLESS_URL}api{prep_endpoint(endpoint)}", params=params, headers=HEADER)
    if getenv("DEBUG") is not None:
        print(f"{req.request.method} {req.url}")
    if req.status_code >= 400:
        return None
    else:
        return req.json()
    
def patch(endpoint: str, data: dict) -> bool:
    if (PAPERLESS_URL := getenv("PAPERLESS_URL")) is None:
        raise EnvironmentError("No PAPERLESS_URL")
    if not PAPERLESS_URL.endswith("/"):
        PAPERLESS_URL = PAPERLESS_URL + "/"

    if (PAPERLESS_TOKEN := getenv("PAPERLESS_TOKEN")) is None:
        raise EnvironmentError("No PAPERLESS_TOKEN")
    else:
        HEADER["Authorization"] = HEADER["Authorization"].replace("<token>", PAPERLESS_TOKEN)

    req = requests.patch(f"{PAPERLESS_URL}api{prep_endpoint(endpoint)}", json.dumps(data), headers=HEADER)
    if getenv("DEBUG") is not None:
        print(f"{req.request.method} {req.url}")
    return req.status_code < 400

def test_connection() -> bool:
    req = get()
    return req is not None

def get_datetimestr(date: datetime) -> str:
    return date.strftime("%Y%m%d%H%M%S")

def get_datetimeobj(date: str) -> datetime:
    return datetime.strptime(date, "%Y%m%d%H%M%S")

def search(query: str, page: int = 1) -> dict[str, Any]:
    result = {
        "count": 0,
        "results": []
    }
    req = get(f"/documents/", params={ "page": page, "query": query })
    if req is None:
        return result

    result["count"] = req["count"]
    result["results"] = req["results"]
    if req["next"] is not None:
        next_page = search(query, page + 1)
        result["results"] = result["results"] + next_page["results"]

    return result