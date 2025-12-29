import sys
import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx
from crawlerd_web.api import nodes, projects, jobs, status
from crawlerd_web.database import create_tables
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager. Handles startup and shutdown events.
    """
    print("🚀 Crawlerd-Web Server is starting up...")
    create_tables()
    scheduler.start()
    yield
    print("👋 Crawlerd-Web Server is shutting down...")
    scheduler.shutdown()
    await agent_client.aclose()
app = FastAPI(
    title="Crawlerd-Web: The Master Control Tower",
    description="A centralized management platform for the distributed crawlframe.",
    version="0.1.0",
    lifespan=lifespan
)

agent_client = httpx.AsyncClient(timeout=10.0)
scheduler = AsyncIOScheduler()
app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="react-assets")

app.include_router(nodes.router, prefix="/api/v1", tags=["Nodes"])
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(status.router, prefix="/api/v1", tags=["Status"])
app.state.scheduler = scheduler # type: ignore
app.state.agent_client = agent_client # type: ignore


@app.get("/{full_path:path}", response_class=FileResponse)
async def serve_react_app(full_path: str):
    if ".." in full_path:
        return FileResponse(os.path.join(STATIC_DIR, "index.html")) # Or return 404
    requested_path = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(requested_path):
        return FileResponse(requested_path)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

def start():
    """Entry point for the crawlerd-web CLI."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Start the Crawlerd Web Dashboard")
    parser.add_argument("--db-path", help="Path to the SQLite database file (required if CRAWLERD_DB_PATH env var is not set)", type=str)
    parser.add_argument("--host", help="Host to bind to", default="0.0.0.0", type=str)
    parser.add_argument("--port", help="Port to bind to", default=80, type=int)
    
    args = parser.parse_args()

    # 优先使用命令行参数，其次检查环境变量
    if args.db_path:
        os.environ["CRAWLERD_DB_PATH"] = args.db_path
    
    # 最终检查
    if not os.getenv("CRAWLERD_DB_PATH"):
        print("\n❌ Error: Database path is missing.")
        print("You must specify where to store the SQLite database.")
        print("-" * 50)
        parser.print_help()
        print("-" * 50)
        print("\nQuick Start Example:")
        print("  crawlerd-web --db-path ./crawlerd.db")
        print("")
        sys.exit(1)

    print(f"🔧 Database Path: {os.environ['CRAWLERD_DB_PATH']}")
    uvicorn.run("crawlerd_web.main:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    start()
