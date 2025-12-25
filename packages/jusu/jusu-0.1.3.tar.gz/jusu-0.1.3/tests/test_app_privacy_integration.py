from starlette.testclient import TestClient
from starlette.requests import Request

from JUSU.app import JusuApp
from JUSU.privacy import StripProductDataMiddleware


def test_jusuapp_middleware_strips():
    app = JusuApp()
    # add the middleware via the JusuApp convenience method
    app.add_middleware(StripProductDataMiddleware)

    @app.post('/echo')
    async def echo(request: Request):
        return await request.json()

    client = TestClient(app.app)
    payload = {"name": "bob", "products": [{"id": 5}], "meta": {"ok": True}}
    r = client.post('/echo', json=payload)
    assert r.status_code == 200
    assert r.json()['products'][0]['_removed']
    assert r.headers.get('x-product-data-removed') == '1'
