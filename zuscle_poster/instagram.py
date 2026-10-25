"""Publish a carousel through the Instagram Graph API (Instagram Login or Facebook Login token)."""
import os
import time

import requests

GRAPH = "https://graph.facebook.com/v21.0"


def _post(path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    r = requests.post(f"{GRAPH}/{path}", data=params, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram API error {r.status_code}: {r.text}")
    return r.json()


def _wait_ready(container_id, tries=20):
    for _ in range(tries):
        r = requests.get(f"{GRAPH}/{container_id}",
                         params={"fields": "status_code", "access_token": os.environ["IG_ACCESS_TOKEN"]},
                         timeout=60)
        status = r.json().get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {container_id} failed: {r.text}")
        time.sleep(3)
    raise RuntimeError(f"Container {container_id} not ready in time")


def publish_carousel(image_urls, caption):
    user = os.environ["IG_USER_ID"]
    children = []
    for url in image_urls:
        res = _post(f"{user}/media", image_url=url, is_carousel_item="true")
        children.append(res["id"])
    for c in children:
        _wait_ready(c)
    parent = _post(f"{user}/media", media_type="CAROUSEL",
                   children=",".join(children), caption=caption)["id"]
    _wait_ready(parent)
    return _post(f"{user}/media_publish", creation_id=parent)["id"]
