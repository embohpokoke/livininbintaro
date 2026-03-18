"""
Livininbintaro CRM — Leads CRUD + AI Scoring
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional
from datetime import datetime, timedelta

from db import get_db, normalize_phone
from config import (
    VALID_BUCKETS, VALID_STATUSES, VALID_SOURCES, STATUS_TO_BUCKET,
)
from ai_scoring import score_lead

router = APIRouter(prefix="/leads", tags=["leads"])


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


# ─── List / Filter ──────────────────────────────────────────────────────────

@router.get("/")
async def list_leads(
    bucket: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    assigned_agent: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    conn = get_db()
    try:
        where, params = ["1=1"], []

        if bucket:
            where.append("bucket = ?")
            params.append(bucket)
        if status:
            where.append("status = ?")
            params.append(status)
        if source:
            where.append("source = ?")
            params.append(source)
        if assigned_agent:
            where.append("assigned_agent = ?")
            params.append(assigned_agent)
        if search:
            where.append("(name LIKE ? OR phone LIKE ? OR email LIKE ?)")
            term = f"%{search}%"
            params.extend([term, term, term])

        w = " AND ".join(where)

        total = conn.execute(f"SELECT COUNT(*) FROM leads WHERE {w}", params).fetchone()[0]

        rows = conn.execute(f"""
            SELECT * FROM leads WHERE {w}
            ORDER BY
                CASE WHEN ai_score IS NOT NULL THEN 0 ELSE 1 END,
                ai_score DESC,
                created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, skip]).fetchall()

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": [dict(r) for r in rows],
        }
    finally:
        conn.close()


@router.get("/counts")
async def lead_counts():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT bucket, COUNT(*) as cnt FROM leads GROUP BY bucket"
        ).fetchall()
        result = {b: 0 for b in VALID_BUCKETS}
        for r in rows:
            key = r["bucket"] or "inbox"
            if key in result:
                result[key] = r["cnt"]
        return result
    finally:
        conn.close()


@router.get("/follow-up-today")
async def follow_up_today():
    conn = get_db()
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        rows = conn.execute("""
            SELECT * FROM leads
            WHERE next_follow_up_at IS NOT NULL
              AND date(next_follow_up_at) <= ?
              AND bucket NOT IN ('closed', 'nurture')
            ORDER BY next_follow_up_at
        """, (today,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@router.get("/sla-breached")
async def sla_breached():
    conn = get_db()
    try:
        now = datetime.utcnow().isoformat()
        rows = conn.execute("""
            SELECT * FROM leads
            WHERE sla_deadline IS NOT NULL
              AND sla_deadline < ?
              AND bucket NOT IN ('closed', 'nurture')
            ORDER BY sla_deadline
        """, (now,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ─── CRUD ────────────────────────────────────────────────────────────────────

@router.get("/{lead_id}")
async def get_lead(lead_id: int):
    conn = get_db()
    try:
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        result = dict(lead)

        activities = conn.execute("""
            SELECT * FROM lead_activities WHERE lead_id = ?
            ORDER BY created_at DESC
        """, (lead_id,)).fetchall()
        result["activities"] = [dict(a) for a in activities]

        messages = conn.execute("""
            SELECT * FROM wa_messages WHERE lead_id = ?
            ORDER BY created_at DESC LIMIT 20
        """, (lead_id,)).fetchall()
        result["recent_messages"] = [dict(m) for m in messages]

        return result
    finally:
        conn.close()


@router.post("/")
async def create_lead(body: dict, background_tasks: BackgroundTasks):
    conn = get_db()
    try:
        name = body.get("name")
        if not name:
            raise HTTPException(status_code=400, detail="name is required")

        phone = normalize_phone(body.get("phone", ""))
        source = body.get("source", "other")
        if source not in VALID_SOURCES:
            source = "other"

        bucket = body.get("bucket", "inbox")
        if bucket not in VALID_BUCKETS:
            bucket = "inbox"

        status = body.get("status", "new")
        if status not in VALID_STATUSES:
            status = "new"

        now = datetime.utcnow().isoformat()
        sla_deadline = (datetime.utcnow() + timedelta(hours=1)).isoformat() if bucket == "inbox" else body.get("sla_deadline")

        cur = conn.execute("""
            INSERT INTO leads (name, phone, email, source, bucket, status,
                assigned_agent, requirement_text, budget_min, budget_max,
                preferred_type, preferred_area, deal_value,
                interested_property_id, sla_deadline, notes,
                created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, phone, body.get("email"), source, bucket, status,
            body.get("assigned_agent"), body.get("requirement_text"),
            body.get("budget_min"), body.get("budget_max"),
            body.get("preferred_type"), body.get("preferred_area"),
            body.get("deal_value"), body.get("interested_property_id"),
            sla_deadline, body.get("notes"),
            now, now,
        ))
        conn.commit()
        lead_id = cur.lastrowid

        # Log activity
        conn.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, 'lead_created', ?)
        """, (lead_id, f"Lead dibuat via {source}"))
        conn.commit()

        # Trigger background AI scoring
        lead_data = {
            "name": name, "phone": phone, "source": source,
            "budget_min": body.get("budget_min"),
            "budget_max": body.get("budget_max"),
            "preferred_area": body.get("preferred_area"),
            "preferred_type": body.get("preferred_type"),
            "status": status, "notes": body.get("notes"),
            "message": body.get("requirement_text"),
        }
        background_tasks.add_task(_bg_score_lead, lead_id, lead_data)

        return {"id": lead_id, "message": "Lead berhasil dibuat", "sla_deadline": sla_deadline}
    finally:
        conn.close()


@router.put("/{lead_id}")
async def update_lead(lead_id: int, body: dict):
    conn = get_db()
    try:
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        allowed = {
            "name", "phone", "email", "source", "bucket", "status",
            "assigned_agent", "requirement_text", "budget_min", "budget_max",
            "preferred_type", "preferred_area", "deal_value",
            "interested_property_id", "sla_deadline", "notes",
            "last_contacted_at", "next_follow_up_at", "follow_up_reason",
        }

        sets, params = [], []
        for k, v in body.items():
            if k in allowed:
                if k == "source" and v not in VALID_SOURCES:
                    continue
                if k == "bucket" and v not in VALID_BUCKETS:
                    continue
                if k == "status" and v not in VALID_STATUSES:
                    continue
                if k == "phone":
                    v = normalize_phone(v)
                sets.append(f"{k} = ?")
                params.append(v)

        # Auto-update bucket when status changes
        new_status = body.get("status")
        if new_status and new_status in STATUS_TO_BUCKET:
            if "bucket" not in body:
                sets.append("bucket = ?")
                params.append(STATUS_TO_BUCKET[new_status])

        if not sets:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        sets.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(lead_id)

        conn.execute(f"UPDATE leads SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()

        updated = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return {"id": lead_id, "status": updated["status"], "bucket": updated["bucket"], "message": "Lead berhasil diupdate"}
    finally:
        conn.close()


@router.put("/{lead_id}/bucket")
async def update_bucket(lead_id: int, body: dict):
    conn = get_db()
    try:
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        new_bucket = body.get("bucket")
        if new_bucket not in VALID_BUCKETS:
            raise HTTPException(status_code=400, detail=f"Invalid bucket. Valid: {VALID_BUCKETS}")

        now = datetime.utcnow().isoformat()
        conn.execute("UPDATE leads SET bucket = ?, updated_at = ? WHERE id = ?", (new_bucket, now, lead_id))
        conn.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, 'bucket_change', ?)
        """, (lead_id, f"Bucket changed: {lead['bucket']} -> {new_bucket}"))
        conn.commit()

        updated = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        return dict(updated)
    finally:
        conn.close()


# ─── AI Score ────────────────────────────────────────────────────────────────

@router.post("/{lead_id}/ai-score")
async def trigger_ai_score(lead_id: int):
    # Step 1: Read lead data, then CLOSE connection before slow Ollama call
    conn = get_db()
    try:
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        lead_data = {
            "name": lead["name"], "phone": lead["phone"], "source": lead["source"],
            "budget_min": lead["budget_min"], "budget_max": lead["budget_max"],
            "preferred_area": lead["preferred_area"], "preferred_type": lead["preferred_type"],
            "status": lead["status"], "notes": lead["notes"],
            "message": lead["requirement_text"],
        }
        lead_bucket = lead["bucket"]
    finally:
        conn.close()  # Release DB connection BEFORE slow Ollama call

    # Step 2: Call Ollama (can take 15-30s) without holding DB connection
    result = await score_lead(lead_data)
    now = datetime.utcnow().isoformat()

    # Step 3: Open fresh connection to write results
    conn2 = get_db()
    try:
        updates = {"ai_score": result["score"], "ai_score_reason": result["reason"], "ai_scored_at": now, "updated_at": now}
        if result["score"] >= 70 and lead_bucket == "inbox":
            updates["bucket"] = "qualified"
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn2.execute(f"UPDATE leads SET {set_clause} WHERE id = ?", list(updates.values()) + [lead_id])
        conn2.commit()
    finally:
        conn2.close()

    return {"lead_id": lead_id, "score": result["score"], "reason": result["reason"], "tier": result["tier"]}


# ─── Activities & Timeline ──────────────────────────────────────────────────

@router.post("/{lead_id}/activities")
async def add_activity(lead_id: int, body: dict):
    conn = get_db()
    try:
        lead = conn.execute("SELECT id FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        cur = conn.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, ?, ?)
        """, (lead_id, body.get("activity_type", "note"), body.get("description", "")))
        conn.commit()
        return {"id": cur.lastrowid, "message": "Aktivitas berhasil ditambahkan"}
    finally:
        conn.close()


@router.get("/{lead_id}/timeline")
async def get_timeline(lead_id: int):
    conn = get_db()
    try:
        lead = conn.execute("SELECT id FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        timeline = []

        activities = conn.execute("""
            SELECT id, activity_type, description, created_at
            FROM lead_activities WHERE lead_id = ?
        """, (lead_id,)).fetchall()
        for a in activities:
            timeline.append({
                "type": "activity", "id": a["id"],
                "content": a["description"], "activity_type": a["activity_type"],
                "created_at": a["created_at"],
            })

        messages = conn.execute("""
            SELECT id, message, direction, message_type, created_at
            FROM wa_messages WHERE lead_id = ?
        """, (lead_id,)).fetchall()
        for m in messages:
            timeline.append({
                "type": "message", "id": m["id"],
                "content": m["message"] or "", "direction": m["direction"],
                "created_at": m["created_at"],
            })

        timeline.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return timeline
    finally:
        conn.close()


# ─── Schedule Follow-up ─────────────────────────────────────────────────────

@router.patch("/{lead_id}/schedule-followup")
async def schedule_followup(lead_id: int, body: dict):
    conn = get_db()
    try:
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        follow_up_date = body.get("follow_up_date")
        reason = body.get("reason", "")

        if not follow_up_date:
            raise HTTPException(status_code=400, detail="follow_up_date is required (YYYY-MM-DD or ISO datetime)")

        now = datetime.utcnow().isoformat()
        conn.execute("""
            UPDATE leads SET next_follow_up_at = ?, follow_up_reason = ?, updated_at = ?
            WHERE id = ?
        """, (follow_up_date, reason, now, lead_id))

        conn.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, 'follow_up_scheduled', ?)
        """, (lead_id, f"Follow-up dijadwalkan: {follow_up_date}. Alasan: {reason}"))
        conn.commit()

        return {"lead_id": lead_id, "next_follow_up_at": follow_up_date, "reason": reason, "message": "Follow-up berhasil dijadwalkan"}
    finally:
        conn.close()


# ─── Background AI scoring ──────────────────────────────────────────────────

async def _bg_score_lead(lead_id: int, lead_data: dict):
    """Background task: AI-score a lead and auto-qualify if score >= 70."""
    try:
        result = await score_lead(lead_data)
        conn = get_db()
        now = datetime.utcnow().isoformat()

        updates = {"ai_score": result["score"], "ai_score_reason": result["reason"], "ai_scored_at": now, "updated_at": now}
        if result["score"] >= 70:
            updates["bucket"] = "qualified"

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE leads SET {set_clause} WHERE id = ?", list(updates.values()) + [lead_id])
        conn.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, 'ai_scored', ?)
        """, (lead_id, f"AI Score: {result['score']} ({result['tier']}). {result['reason']}"))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[BG AI Score] Error for lead {lead_id}: {e}")


# ─── Notes API (Phase C) ─────────────────────────────────────────────────────

@router.get("/{lead_id}/notes")
async def get_lead_notes(lead_id: int):
    """Get all notes for a lead, ordered by newest first."""
    conn = get_db()
    try:
        # Verify lead exists
        lead = conn.execute("SELECT id FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Get notes with user info
        notes = conn.execute("""
            SELECT n.id, n.lead_id, n.user_id, n.content, n.note_type, n.created_at,
                   u.username, u.full_name
            FROM lead_notes n
            LEFT JOIN users u ON n.user_id = u.id
            WHERE n.lead_id = ?
            ORDER BY n.created_at DESC
        """, (lead_id,)).fetchall()
        
        return [dict(n) for n in notes]
    finally:
        conn.close()


@router.post("/{lead_id}/notes")
async def add_lead_note(lead_id: int, body: dict):
    """Add a note to a lead."""
    conn = get_db()
    try:
        # Verify lead exists
        lead = conn.execute("SELECT id FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        content = body.get("content", "").strip()
        if not content:
            raise HTTPException(status_code=400, detail="content is required")
        
        note_type = body.get("note_type", "manual")
        user_id = body.get("user_id")  # Optional, can be NULL for system notes
        
        # Insert and get ID using RETURNING
        cur = conn.execute("""
            INSERT INTO lead_notes (lead_id, user_id, content, note_type)
            VALUES (?, ?, ?, ?)
            RETURNING *
        """, (lead_id, user_id, content, note_type))
        note = cur.fetchone()
        conn.commit()
        
        # Log activity
        conn.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, 'note_added', ?)
        """, (lead_id, f"Note added: {content[:100]}"))
        conn.commit()
        
        return dict(note)
    finally:
        conn.close()


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int):
    """Delete a note."""
    conn = get_db()
    try:
        note = conn.execute("SELECT * FROM lead_notes WHERE id = ?", (note_id,)).fetchone()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        lead_id = note["lead_id"]
        
        conn.execute("DELETE FROM lead_notes WHERE id = ?", (note_id,))
        conn.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, 'note_deleted', ?)
        """, (lead_id, f"Note deleted: {note['content'][:100]}"))
        conn.commit()
        
        return {"status": "deleted", "id": note_id}
    finally:
        conn.close()


# ─── AI Recommendations (Phase C) ────────────────────────────────────────────

@router.post("/{lead_id}/ai-summary")
async def generate_summary(lead_id: int):
    """Generate AI summary from lead data, conversations, and notes."""
    conn = get_db()
    try:
        # Get lead data
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Get conversations
        messages = conn.execute("""
            SELECT message, direction, created_at
            FROM wa_messages
            WHERE lead_id = ?
            ORDER BY created_at
        """, (lead_id,)).fetchall()
        
        # Get notes
        notes = conn.execute("""
            SELECT content, created_at
            FROM lead_notes
            WHERE lead_id = ?
            ORDER BY created_at
        """, (lead_id,)).fetchall()
        
        # Convert to dicts
        lead_data = dict(lead)
        msg_data = [{"direction": m["direction"], "message": m["message"], "created_at": str(m["created_at"])} for m in messages]
        note_data = [{"content": n["content"], "created_at": str(n["created_at"])} for n in notes]
        
    finally:
        conn.close()  # Release DB connection before slow AI call
    
    # Call AI service (no DB connection held)
    from ai_recommendations import generate_lead_summary
    result = await generate_lead_summary(lead_data, msg_data, note_data)
    
    # Update lead with results
    conn2 = get_db()
    try:
        now = datetime.utcnow().isoformat()
        follow_up_date = None
        
        if result.get("follow_up_days"):
            from datetime import timedelta
            follow_up_date = (datetime.utcnow() + timedelta(days=result["follow_up_days"])).isoformat()
        
        conn2.execute("""
            UPDATE leads
            SET ai_summary = ?,
                ai_summary_at = ?,
                next_follow_up_at = ?,
                follow_up_reason = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            result.get("summary", ""),
            now,
            follow_up_date,
            result.get("recommended_action", ""),
            now,
            lead_id
        ))
        
        # Log activity
        conn2.execute("""
            INSERT INTO lead_activities (lead_id, activity_type, description)
            VALUES (?, 'ai_summary_generated', ?)
        """, (lead_id, f"AI Summary: {result.get('summary', '')[:100]}"))
        
        conn2.commit()
        
        return result
    finally:
        conn2.close()


@router.post("/{lead_id}/ai-recommend")
async def get_recommendations(lead_id: int):
    """Get property recommendations based on lead preferences."""
    conn = get_db()
    try:
        # Get lead data
        lead = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Build preferences from lead data
        preferences = {
            "preferred_areas": [lead["preferred_area"]] if lead.get("preferred_area") else [],
            "property_types": [lead["preferred_type"]] if lead.get("preferred_type") else [],
            "budget_min": lead.get("budget_min"),
            "budget_max": lead.get("budget_max"),
        }
        
        # Get property matches
        from ai_recommendations import match_properties
        properties = await match_properties(preferences, conn)
        
        return {
            "lead_id": lead_id,
            "recommendations": properties,
            "match_criteria": preferences,
            "count": len(properties)
        }
    finally:
        conn.close()
