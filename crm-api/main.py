"""
Livininbintaro CRM — FastAPI Backend v2.0
Port: 8003 | Database: SQLite | WA: GOWA port 3002
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db, migrate_db
from scheduler import start_scheduler, stop_scheduler
from routers import leads, webhook, wa_templates, dashboard, content
from routers import wa_messages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("livininbintaro")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database...")
    init_db()
    migrate_db()
    logger.info("Starting background scheduler...")
    #start_scheduler()  # DISABLED by Erik 2026-03-07
    logger.info("Livininbintaro CRM v2.0 ready")
    yield
    # Shutdown
    stop_scheduler()
    logger.info("Livininbintaro CRM stopped")


app = FastAPI(
    title="Livininbintaro CRM API",
    version="2.0.0",
    description="Property Lead CRM with WhatsApp integration, AI scoring, SLA monitoring",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(leads.router)
app.include_router(webhook.router)
app.include_router(wa_templates.router)
app.include_router(dashboard.router)
app.include_router(content.router)
app.include_router(wa_messages.router)


@app.get("/health")
async def health():
    from db import get_db
    conn = get_db()
    try:
        lead_count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        template_count = conn.execute("SELECT COUNT(*) FROM wa_templates").fetchone()[0]
        return {
            "status": "ok",
            "app": "livininbintaro-crm",
            "version": "2.0.0",
            "leads": lead_count,
            "templates": template_count,
        }
    finally:
        conn.close()


@app.get("/stats")
async def dashboard_stats():
    from db import get_db
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]

        buckets = {}
        for row in conn.execute("SELECT bucket, COUNT(*) as cnt FROM leads GROUP BY bucket").fetchall():
            buckets[row["bucket"] or "inbox"] = row["cnt"]

        statuses = {}
        for row in conn.execute("SELECT status, COUNT(*) as cnt FROM leads GROUP BY status").fetchall():
            statuses[row["status"] or "new"] = row["cnt"]

        scored = conn.execute("SELECT COUNT(*) FROM leads WHERE ai_score IS NOT NULL").fetchone()[0]
        avg_score = conn.execute("SELECT AVG(ai_score) FROM leads WHERE ai_score IS NOT NULL").fetchone()[0]

        from datetime import datetime
        now = datetime.utcnow().isoformat()
        sla_breached = conn.execute("""
            SELECT COUNT(*) FROM leads
            WHERE sla_deadline IS NOT NULL AND sla_deadline < ?
            AND bucket NOT IN ('closed', 'nurture')
        """, (now,)).fetchone()[0]

        return {
            "total_leads": total,
            "buckets": buckets,
            "statuses": statuses,
            "ai_scored": scored,
            "avg_ai_score": round(avg_score, 1) if avg_score else None,
            "sla_breached": sla_breached,
        }
    finally:
        conn.close()
