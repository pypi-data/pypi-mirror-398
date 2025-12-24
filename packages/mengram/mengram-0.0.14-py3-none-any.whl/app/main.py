from fastapi import FastAPI

from app.api.routes import api_router
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401  # ensure models are imported for metadata

app = FastAPI(title="Memory OS (local V0)")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(api_router)
