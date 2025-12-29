from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from kryten_playlist.web.routes import auth, catalog, marathon, nowplaying, playlists, queue, stats
from kryten_playlist.web.ui import router as ui_router


def create_app() -> FastAPI:
    app = FastAPI(title="kryten-playlist", version="0.1")

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    app.include_router(ui_router)

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["catalog"])
    app.include_router(nowplaying.router, prefix="/api/v1/nowplaying", tags=["nowplaying"])
    app.include_router(playlists.router, prefix="/api/v1/playlists", tags=["playlists"])
    app.include_router(queue.router, prefix="/api/v1/queue", tags=["queue"])
    app.include_router(marathon.router, prefix="/api/v1/marathon", tags=["marathon"])
    app.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])

    # Serve frontend static assets (production build)
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")
        
        # Catch-all for SPA client-side routing
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # Don't intercept API routes
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404)
            
            # Serve index.html for all other routes (SPA handles routing)
            index_file = frontend_dist / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
            raise HTTPException(status_code=404)

    return app


# Module-level app instance for uvicorn development (e.g., uvicorn kryten_playlist.web.app:app)
app = create_app()

