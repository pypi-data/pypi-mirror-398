"""
Usefly FastAPI Server

Serves the static Next.js export and provides API endpoints for agent runs and reports.
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from src.database import init_db
from src.routers.persona_runs import router as persona_runs_router
from src.routers.reports import router as reports_router
from src.routers.system_config import router as system_config_router
from src.routers.scenarios import router as scenario_router
from src.routers.persona_runner import router as persona_runner_router

# Initialize database
init_db()

app = FastAPI(title="Usefly", description="Agentic UX Analytics")

# Add CORS middleware for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the static directory path
static_dir = Path(__file__).parent / "static"

# Include API routes
app.include_router(persona_runs_router)
app.include_router(reports_router)
app.include_router(system_config_router)
app.include_router(scenario_router)
app.include_router(persona_runner_router)


# API Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "usefly"}


# Serve static files
if static_dir.exists():
    # Mount _next directory for Next.js assets
    next_dir = static_dir / "_next"
    if next_dir.exists():
        app.mount("/_next", StaticFiles(directory=str(next_dir)), name="next_static")

    # Serve other static files (images, etc.)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        Serve static files or fallback to index.html for client-side routing.

        This handles:
        - Direct file requests (e.g., /favicon.ico)
        - Next.js pages (e.g., /reports, /agent-runs)
        - Assets from public directory
        """
        # Don't handle _next paths - those are handled by the StaticFiles mount
        if full_path.startswith("_next"):
            raise HTTPException(status_code=404, detail="File not found")

        # Don't handle API paths - those are handled by the API routers
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        # Handle root path
        if not full_path or full_path == "/":
            index_path = static_dir / "index.html"
            if index_path.exists():
                return HTMLResponse(content=index_path.read_text(), status_code=200)
            raise HTTPException(status_code=404, detail="index.html not found. Please build the UI first.")

        # Try to serve the file directly
        file_path = static_dir / full_path

        # If it's a directory, try index.html
        if file_path.is_dir():
            index_path = file_path / "index.html"
            if index_path.exists():
                return HTMLResponse(content=index_path.read_text(), status_code=200)

        # If it's a file, serve it
        if file_path.is_file():
            return FileResponse(file_path)

        # Try with .html extension
        html_path = static_dir / f"{full_path}.html"
        if html_path.exists():
            return HTMLResponse(content=html_path.read_text(), status_code=200)

        # Fallback to index.html for client-side routing (SPA mode)
        index_path = static_dir / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text(), status_code=200)

        raise HTTPException(status_code=404, detail="File not found")
else:
    # Static directory doesn't exist - show helpful error
    @app.get("/")
    async def no_static():
        return HTMLResponse(
            content="""
            <html>
                <head><title>Usefly - Build Required</title></head>
                <body style="font-family: sans-serif; padding: 2rem; max-width: 600px; margin: 0 auto;">
                    <h1>⚠️ Build Required</h1>
                    <p>The UI has not been built yet. Please run:</p>
                    <pre style="background: #f5f5f5; padding: 1rem; border-radius: 4px;">cd ui && pnpm install && pnpm build</pre>
                    <p>This will generate the static files in <code>src/static/</code></p>
                </body>
            </html>
            """,
            status_code=503
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
