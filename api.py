from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="DashFinanceira API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS para React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from routers.categories import router as categories_router
from routers.transactions import router as transactions_router
from routers.upload import router as upload_router
from routers.analytics import router as analytics_router
from routers.budgets import router as budgets_router
from routers.rules import router as rules_router
from routers.investments import router as investments_router
from routers.planning import router as planning_router
from routers.export import router as export_router

app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(upload_router)
app.include_router(analytics_router)
app.include_router(budgets_router)
app.include_router(rules_router)
app.include_router(investments_router)
app.include_router(planning_router)
app.include_router(export_router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}


# Serve frontend em produção (após build)
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8050, reload=True)
