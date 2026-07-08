from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cohort, explain, ingest, patients, cascade, referral
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
    app.include_router(referral.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    import os
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    dist_dir = os.path.join(os.path.dirname(__file__), "../../frontend/dist")
    if os.path.exists(dist_dir):
        app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            path = os.path.join(dist_dir, full_path)
            if os.path.isfile(path):
                return FileResponse(path)
            return FileResponse(os.path.join(dist_dir, "index.html"))

    return app


app = create_app()
