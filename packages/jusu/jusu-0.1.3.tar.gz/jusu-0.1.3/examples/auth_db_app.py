"""Example FastAPI app with SQLModel-backed User and auth flows.

Run (after installing extras):
    pip install -e .[web,auth,db]
    python examples/auth_db_app.py

Visit endpoints:
- POST /register {"username","password"}
- POST /login {"username","password"} -> sets session cookie and returns JWT
- GET /protected -> requires session or Bearer token
"""
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Field, SQLModel, Session, create_engine, select

from JUSU.auth import hash_password, verify_password, create_jwt, login_required, SessionManager

DATABASE_URL = "sqlite:///./jusu_example.db"
engine = create_engine(DATABASE_URL, echo=False)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    salt: str
    hashed: str

app = FastAPI(title="JUSU Auth Example")

# Simple session manager using cookie sessions; in production use env secret
session_mgr = SessionManager(secret_key="devsecret-session")
session_mgr.init_app(app)

JWT_SECRET = "devsecret-jwt"

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.post("/register")
def register(data: dict):
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    with Session(engine) as sess:
        exists = sess.exec(select(User).where(User.username == username)).first()
        if exists:
            raise HTTPException(status_code=400, detail="username taken")
        salt, hashed = hash_password(password)
        user = User(username=username, salt=salt, hashed=hashed)
        sess.add(user)
        sess.commit()
        sess.refresh(user)
    return JSONResponse({"id": user.id, "username": user.username})

@app.post("/login")
def login(data: dict):
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    with Session(engine) as sess:
        user = sess.exec(select(User).where(User.username == username)).first()
        if not user or not verify_password(password, user.salt, user.hashed):
            raise HTTPException(status_code=401, detail="invalid credentials")
        # Set session
        # FastAPI doesn't expose Request/session here; use low-level response cookie for demo
    token = create_jwt({"sub": user.username}, secret=JWT_SECRET, expires_in=3600)
    resp = JSONResponse({"token": token})
    # Set a simple cookie to simulate a login session (for demo only)
    resp.set_cookie("jusu_session", user.username, httponly=True)
    return resp

@app.get("/protected")
def protected(user=Depends(login_required(jwt_secret=JWT_SECRET))):
    return {"user": user}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
