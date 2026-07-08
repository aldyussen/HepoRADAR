from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cascade, cohort, explain, ingest, patients
from app.auth import router as auth_router
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="HepaRadar")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router.router)
    app.include_router(ingest.router)
    app.include_router(cohort.router)
    app.include_router(patients.router)
    app.include_router(explain.router)
    app.include_router(cascade.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
