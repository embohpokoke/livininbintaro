"""
Livininbintaro CRM — WA Template CRUD + Send via GOWA
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from db import get_db
from config import VALID_TEMPLATE_CATEGORIES
from gowa_client import send_message

router = APIRouter(prefix="/wa/templates", tags=["wa-templates"])


# ─── CRUD ────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_templates(category: str = None):
    conn = get_db()
    try:
        if category:
            rows = conn.execute(
                "SELECT * FROM wa_templates WHERE category = ? ORDER BY created_at DESC",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM wa_templates ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get("/{template_id}")
async def get_template(template_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM wa_templates WHERE id = ?", (template_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")
        return dict(row)
    finally:
        conn.close()


@router.post("/")
async def create_template(body: dict):
    conn = get_db()
    try:
        name = body.get("name")
        category = body.get("category", "greeting")
        content = body.get("content")

        if not name or not content:
            raise HTTPException(status_code=400, detail="name and content are required")
        if category not in VALID_TEMPLATE_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Valid: {VALID_TEMPLATE_CATEGORIES}",
            )

        cur = conn.execute("""
            INSERT INTO wa_templates (name, category, content) VALUES (?, ?, ?)
        """, (name, category, content))
        conn.commit()
        return {"id": cur.lastrowid, "message": "Template berhasil dibuat"}
    finally:
        conn.close()


@router.put("/{template_id}")
async def update_template(template_id: int, body: dict):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM wa_templates WHERE id = ?", (template_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")

        sets, params = [], []
        for k in ("name", "category", "content"):
            if k in body:
                if k == "category" and body[k] not in VALID_TEMPLATE_CATEGORIES:
                    raise HTTPException(status_code=400, detail=f"Invalid category. Valid: {VALID_TEMPLATE_CATEGORIES}")
                sets.append(f"{k} = ?")
                params.append(body[k])

        if not sets:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        params.append(template_id)
        conn.execute(f"UPDATE wa_templates SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()

        updated = conn.execute("SELECT * FROM wa_templates WHERE id = ?", (template_id,)).fetchone()
        return dict(updated)
    finally:
        conn.close()


@router.delete("/{template_id}")
async def delete_template(template_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM wa_templates WHERE id = ?", (template_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Template not found")

        conn.execute("DELETE FROM wa_templates WHERE id = ?", (template_id,))
        conn.commit()
        return {"status": "deleted", "id": template_id}
    finally:
        conn.close()


# ─── Send Template ──────────────────────────────────────────────────────────

@router.post("/send/{lead_id}/{template_id}")
async def send_template(lead_id: int, template_id: int):
    conn = get_db()
    try:
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        template = conn.execute("SELECT * FROM wa_templates WHERE id = ?", (template_id,)).fetchone()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        phone = lead["phone"]
        if not phone:
            raise HTTPException(status_code=400, detail="Lead has no phone number")

        # Render template placeholders
        rendered = template["content"].replace("{name}", lead["name"] or "")
        rendered = rendered.replace("{phone}", phone or "")
        rendered = rendered.replace("{property}", lead["interested_property_id"] or "")
        rendered = rendered.replace("{area}", lead["preferred_area"] or "")
        rendered = rendered.replace("{budget}", _format_budget(lead["budget_min"], lead["budget_max"]))

        # Send via GOWA
        result = await send_message(phone, rendered)

        # Store outbound message
        conn.execute("""
            INSERT INTO wa_messages (lead_id, phone, message, direction, message_type)
            VALUES (?, ?, ?, 'outbound', 'text')
        """, (lead_id, phone, rendered))

        # Log activity
        conn.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, 'wa_template_sent', ?)
        """, (lead_id, f"Template '{template['name']}' sent: {rendered[:200]}"))

        # Update last contacted
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE leads SET last_contacted_at = ?, updated_at = ? WHERE id = ?",
            (now, now, lead_id),
        )
        conn.commit()

        return {
            "status": "sent",
            "lead_id": lead_id,
            "template_id": template_id,
            "rendered_message": rendered,
            "gowa_response": result,
        }
    finally:
        conn.close()


def _format_budget(bmin, bmax):
    def fmt(v):
        if not v:
            return "-"
        if v >= 1_000_000_000:
            return f"Rp {v / 1_000_000_000:.1f}M"
        if v >= 1_000_000:
            return f"Rp {v / 1_000_000:.0f}jt"
        return f"Rp {v:,.0f}"
    return f"{fmt(bmin)} - {fmt(bmax)}"
