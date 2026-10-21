from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_db_and_tables
from auth import router as auth_router
from widgets import router as widgets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()   
    yield                    

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(widgets_router)

@app.get("/health")
def health():
    return {"status": "ok"}