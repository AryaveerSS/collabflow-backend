"""
app/main.py

FastAPI application entry point.
Creates the app, registers middleware, mounts all routers,
and handles startup/shutdown events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import check_database_connection
from app.auth.routes import router as auth_router
from app.users.routes import router as users_router


# ================================
# Lifespan (startup + shutdown)
# ================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events.
    Replaces deprecated @app.on_event("startup").
    """

    # ---- Startup ----
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Environment : {settings.ENVIRONMENT}")
    print(f"   Debug mode  : {settings.DEBUG}")

    # Check database connection
    db_ok = await check_database_connection()
    if db_ok:
        print("   Database    : ✅ Connected")
    else:
        print("   Database    : ❌ Connection failed — check PostgreSQL")

    print(f"   Docs        : http://{settings.HOST}:{settings.PORT}/docs")
    print("-" * 50)

    yield  # App runs here

    # ---- Shutdown ----
    print(f"🛑 Shutting down {settings.APP_NAME}...")


# ================================
# App Instance
# ================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## CollabFlow Backend API

Production-style real-time team collaboration platform.

### Features
- 🔐 JWT Authentication with refresh tokens
- 👥 Workspace and team management
- 📋 Project and task management
- ⚡ Real-time updates via WebSockets
- 🔔 Notification system
- 📝 Activity audit trail

### Authentication
Use `POST /api/v1/auth/login` to get tokens.
Include `Authorization: Bearer <access_token>` in all protected requests.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ================================
# Middleware
# ================================

# CORS — allow frontend origins to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================
# Routers
# ================================

API_PREFIX = "/api/v1"

app.include_router(auth_router,  prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)


# ================================
# Root Endpoints
# ================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint — confirms API is running."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Used by Docker, load balancers, and monitoring tools.
    """
    db_ok = await check_database_connection()

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "version": settings.APP_VERSION,
    }   