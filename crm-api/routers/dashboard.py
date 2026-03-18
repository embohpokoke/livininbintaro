"""
Livininbintaro CRM — Dashboard Endpoints (funnel, source-stats, action-items)
"""

from fastapi import APIRouter
from datetime import datetime, timedelta

from db import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/funnel")
async def funnel():
    """Conversion funnel: Inbox -> Qualified -> Showing -> Negotiation -> Closed."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT bucket, COUNT(*) as cnt FROM leads GROUP BY bucket"
        ).fetchall()
        counts = {r["bucket"]: r["cnt"] for r in rows}
        total = sum(counts.values()) or 1

        stages = ["inbox", "qualified", "showing", "negotiation", "closed"]
        funnel_data = []
        for s in stages:
            c = counts.get(s, 0)
            funnel_data.append({
                "bucket": s,
                "count": c,
                "pct": round(c / total * 100, 1),
            })

        # Won/lost breakdown for closed
        won = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE status = 'closed_won'"
        ).fetchone()[0]
        lost = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE status = 'closed_lost'"
        ).fetchone()[0]

        return {
            "total": sum(counts.values()),
            "funnel": funnel_data,
            "nurture": counts.get("nurture", 0),
            "closed_won": won,
            "closed_lost": lost,
        }
    finally:
        conn.close()


@router.get("/source-stats")
async def source_stats():
    """Leads per source with conversion rates."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT
                source,
                COUNT(*) as total,
                SUM(CASE WHEN bucket = 'qualified' THEN 1 ELSE 0 END) as qualified,
                SUM(CASE WHEN bucket = 'showing' THEN 1 ELSE 0 END) as showing,
                SUM(CASE WHEN bucket = 'negotiation' THEN 1 ELSE 0 END) as negotiation,
                SUM(CASE WHEN bucket = 'closed' THEN 1 ELSE 0 END) as closed,
                AVG(ai_score) as avg_score
            FROM leads
            GROUP BY source
            ORDER BY total DESC
        """).fetchall()

        result = []
        for r in rows:
            total = r["total"] or 1
            result.append({
                "source": r["source"] or "other",
                "total": r["total"],
                "qualified": r["qualified"],
                "showing": r["showing"],
                "negotiation": r["negotiation"],
                "closed": r["closed"],
                "conversion_rate": round((r["closed"] / total) * 100, 1),
                "avg_score": round(r["avg_score"], 1) if r["avg_score"] else None,
            })

        return result
    finally:
        conn.close()


@router.get("/action-items")
async def action_items():
    """Today's action items: overdue follow-ups, SLA breaches, new leads."""
    conn = get_db()
    try:
        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")

        # Overdue follow-ups
        overdue_fu = conn.execute("""
            SELECT id, name, phone, bucket, next_follow_up_at, follow_up_reason
            FROM leads
            WHERE next_follow_up_at IS NOT NULL
              AND date(next_follow_up_at) <= ?
              AND bucket NOT IN ('closed', 'nurture')
            ORDER BY next_follow_up_at
        """, (today,)).fetchall()

        # SLA breaches
        sla_breach = conn.execute("""
            SELECT id, name, phone, bucket, sla_deadline, created_at
            FROM leads
            WHERE sla_deadline IS NOT NULL
              AND sla_deadline < ?
              AND bucket NOT IN ('closed', 'nurture')
            ORDER BY sla_deadline
        """, (now.isoformat(),)).fetchall()

        # New leads today
        new_today = conn.execute("""
            SELECT id, name, phone, source, ai_score, created_at
            FROM leads
            WHERE date(created_at) = ?
            ORDER BY created_at DESC
        """, (today,)).fetchall()

        # Unscored leads
        unscored = conn.execute("""
            SELECT COUNT(*) FROM leads
            WHERE ai_score IS NULL AND bucket NOT IN ('closed', 'nurture')
        """).fetchone()[0]

        return {
            "overdue_followups": [dict(r) for r in overdue_fu],
            "sla_breaches": [dict(r) for r in sla_breach],
            "new_today": [dict(r) for r in new_today],
            "unscored_leads": unscored,
            "counts": {
                "overdue_followups": len(overdue_fu),
                "sla_breaches": len(sla_breach),
                "new_today": len(new_today),
                "unscored": unscored,
            },
        }
    finally:
        conn.close()


@router.get("/recent-activity")
async def recent_activity():
    """Recent activities across all leads."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT a.id, a.lead_id, a.activity_type, a.description, a.created_at,
                   l.name as lead_name
            FROM lead_activities a
            JOIN leads l ON l.id = a.lead_id
            ORDER BY a.created_at DESC
            LIMIT 30
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
