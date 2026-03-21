from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager

from api.path import path_router, PathOpr
from api.pattern import pattern_router, pattern
from api.test import test_router
from api.file import file_router
from api.tran import tran_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pattern.init()
    PathOpr._temp_path.mkdir(exist_ok=True)
    yield
    await pattern.end()
    if PathOpr._temp_path.exists():
        for i in PathOpr._temp_path.iterdir():
            if i.is_file():
                i.unlink()
        PathOpr._temp_path.rmdir()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(path_router)
app.include_router(pattern_router)
app.include_router(file_router)
app.include_router(tran_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(test_router)
