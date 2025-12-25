"""Minimal FastAPI example demonstrating JUSU integration.

Run locally with:
    pip install -e .[web]
    uvicorn examples.fastapi_app:app.app --reload

Then visit http://127.0.0.1:8000
"""
from JUSU import Div, H1, P, Button
from JUSU.app import JusuApp

app = JusuApp(title="JUSU + FastAPI example")

@app.get("/")
async def index():
    return Div(
        H1("Welcome to JUSU + FastAPI"),
        P("This page is rendered by JUSU tags and served by FastAPI."),
        Button("Click me", onclick="alert('Hello')", cls="btn"),
    )

# Example static mount (optional)
# app.mount_static("/static", directory="static")

# Privacy middleware example — strip product data by default
try:
    from JUSU.privacy import StripProductDataMiddleware
    app.add_middleware(StripProductDataMiddleware)
except Exception:
    # optional dependency; ignore if starlette is not available in this env
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app.app, host="127.0.0.1", port=8000, reload=True)
