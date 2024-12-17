from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from routers.moiraiRouter import app as moirai


app = FastAPI(title="Ananke API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("START")

    yield
    print("STOP")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return "hello world"


app.include_router(moirai)
