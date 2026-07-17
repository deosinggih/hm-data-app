from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.models import BaConfig  # noqa: F401 — register models
from app.routers import ba, export, hm, master, pa, po, status
from app.services.excel_import import seed_master_from_form


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_master_from_form(db)
        if not db.query(BaConfig).first():
            db.add(BaConfig())
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="BA HM GENERATOR", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(master.router)
app.include_router(hm.router)
app.include_router(status.router)
app.include_router(po.router)
app.include_router(export.router)
app.include_router(pa.router)
app.include_router(ba.router)


@app.get("/api/health")
def health():
    return {"ok": True, "service": "BA HM GENERATOR"}