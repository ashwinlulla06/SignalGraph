from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.lifespan import lifespan


# main.py now only assembles the FastAPI application.
app = FastAPI(
    title="SignalGraph API",
    version="0.1.0",
    lifespan=lifespan,
)


# Allow the local React development server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# The router contains every HTTP and WebSocket endpoint.
app.include_router(router)
