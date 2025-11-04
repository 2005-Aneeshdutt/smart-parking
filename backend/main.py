from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth
from routes import parking
from routes import admin

app = FastAPI(title="Smart Parking System API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(parking.router)
app.include_router(admin.router)
