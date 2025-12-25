
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import argparse
import uvicorn
from contextlib import asynccontextmanager, AsyncExitStack
import os

from todolistz.database import Base, engine
from todolistz.api import goals, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Dyson System")

app.include_router(goals.router, prefix="/goals")
app.include_router(tasks.router, prefix="/tasks")

default=8008

# --- Configure CORS ---
origins = [
    "*", # Allows all origins (convenient for development, insecure for production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specifies the allowed origins
    allow_credentials=True, # Allows cookies/authorization headers
    allow_methods=["*"],    # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],    # Allows all headers (Content-Type, Authorization, etc.)
)
# --- End CORS Configuration ---

@app.get("/")
async def root():
    return {"message": "LLM Service is running."}


if __name__ == "__main__":    
    parser = argparse.ArgumentParser(
        description="Start a simple HTTP server similar to http.server."
    )
    parser.add_argument(
        "port",
        metavar="PORT",
        type=int,
        nargs="?",
        default=default,
        help=f"Specify alternate port [default: {default}]",
    )
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--dev",
        action="store_true",  # 当存在 --dev 时，该值为 True
        help="Run in development mode (default).",
    )

    group.add_argument(
        "--prod",
        action="store_true",  # 当存在 --prod 时，该值为 True
        help="Run in production mode.",
    )
    args = parser.parse_args()

    port   = args.port if args.prod else args.port + 100
    reload = False     if args.prod else True
    app_s  = app       if args.prod else f"{__package__}.server:app"

    uvicorn.run(
        app_s, host="0.0.0.0", port=port, reload=reload  # 启用热重载
    )
