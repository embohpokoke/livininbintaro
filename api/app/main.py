import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import hash_password, require_roles
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import User
from app.routers import auth, content, dashboard, leads, listings, public, users, wa, webhook

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Unified property marketplace, CRM dashboard, and WhatsApp operations API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _safe_bootstrap_tables():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        logger.exception("Database bootstrap failed")


def _safe_seed_users():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            db.add(
                User(
                    username="admin",
                    password_hash=hash_password("Adm1n!L1v1n2026"),
                    full_name="Admin",
                    role="admin",
                )
            )
        agent = db.query(User).filter(User.username == "ocha").first()
        if not agent:
            db.add(
                User(
                    username="ocha",
                    password_hash=hash_password("Ocha!Pr0p2026"),
                    full_name="Ocha",
                    role="agent",
                )
            )
        db.commit()
    except Exception:
        logger.exception("User seeding failed")
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
def startup():
    _safe_bootstrap_tables()
    _safe_seed_users()


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "healthy", "version": settings.APP_VERSION}


app.include_router(auth.router, prefix="/api")
app.include_router(public.router, prefix="/api")
app.include_router(
    listings.router,
    prefix="/api",
    dependencies=[Depends(require_roles(["agent", "admin"]))],
)
app.include_router(
    leads.router,
    prefix="/api",
    dependencies=[Depends(require_roles(["agent", "admin"]))],
)
app.include_router(
    wa.router,
    prefix="/api",
    dependencies=[Depends(require_roles(["agent", "admin"]))],
)
app.include_router(
    content.router,
    prefix="/api",
    dependencies=[Depends(require_roles(["agent", "admin"]))],
)
app.include_router(
    dashboard.router,
    prefix="/api",
    dependencies=[Depends(require_roles(["agent", "admin"]))],
)
app.include_router(
    users.router,
    prefix="/api",
    dependencies=[Depends(require_roles(["agent", "admin"]))],
)
app.include_router(wa.webhook_router, prefix="/api")
app.include_router(webhook.router, prefix="/api")

# Legacy routes kept available while the old frontend and webhooks transition.
app.include_router(auth.router, include_in_schema=False)
app.include_router(listings.router, include_in_schema=False)
app.include_router(leads.router, include_in_schema=False)
app.include_router(wa.router, include_in_schema=False)
app.include_router(users.router, include_in_schema=False)
app.include_router(webhook.router, include_in_schema=False)
