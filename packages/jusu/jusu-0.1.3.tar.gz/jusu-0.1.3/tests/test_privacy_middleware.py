
from fastapi import FastAPI
from starlette.testclient import TestClient
from starlette.requests import Request

from JUSU.privacy import StripProductDataMiddleware


app = FastAPI()

# simple endpoint that echoes back parsed JSON
@app.post("/echo")
async def echo(request: Request):
    data = await request.json()
    return data

# mount middleware
app.add_middleware(StripProductDataMiddleware)


def test_strips_product_data_from_body():
    client = TestClient(app)

    payload = {"name": "alice", "products": [{"id": 1, "name": "widget"}], "meta": {"ok": True}}
    r = client.post("/echo", json=payload)
    if r.status_code != 200:
        print('DEBUG: status', r.status_code)
        print('DEBUG: content:', r.content)
    assert r.status_code == 200
    assert r.json()["products"][0]["_removed"]
    # header indicates removal
    assert r.headers.get("x-product-data-removed") == "1"


def test_passes_through_when_no_product_keys():
    client = TestClient(app)
    payload = {"name": "alice", "meta": {"ok": True}}
    r = client.post("/echo", json=payload)
    assert r.status_code == 200
    assert r.json() == payload


def test_block_mode_rejects():
    app2 = FastAPI()
    app2.add_middleware(StripProductDataMiddleware, mode="block")

    client = TestClient(app2)
    payload = {"products": [{"id": 1}]}
    r = client.post("/echo", json=payload)
    assert r.status_code == 400
    assert b"Product data is not allowed" in r.content
