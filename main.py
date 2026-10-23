from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_db_and_tables
from auth import router as auth_router
from widgets import router as widgets_router
from public import router as public_router
from submissions import router as submissions_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse




@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()   
    yield                    

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(widgets_router)
app.include_router(public_router)
app.include_router(submissions_router)
MAX_BODY_BYTES = 10_000

@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    return await call_next(request)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
    max_age=600,
)



@app.get("/health")
def health():
    return {"status": "ok"}