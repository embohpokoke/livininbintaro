import httpx
import json
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "minimax-m2.5:cloud"


async def generate_lead_summary(lead: dict, messages: list, notes: list) -> dict:
    """Generate AI summary from lead data, WA conversations, and agent notes."""

    conversation_text = "\n".join([
        f"{'Agent' if m['direction']=='outbound' else 'Client'}: {m['message']}"
        for m in messages[-30:]
    ]) or "Belum ada percakapan"

    notes_text = "\n".join([
        f"[{n['created_at']}] {n['content']}"
        for n in notes[-10:]
    ]) or "Belum ada catatan"

    prompt = f"""Kamu adalah asisten CRM untuk agen properti Century 21 Bintaro.
Analisis data lead berikut dan berikan summary dalam Bahasa Indonesia.

DATA LEAD:
- Nama: {lead.get('name', '-')}
- Budget: {lead.get('budget_min', '-')} - {lead.get('budget_max', '-')}
- Area preferensi: {lead.get('preferred_area', '-')}
- Tipe properti: {lead.get('preferred_type', '-')}
- Status: {lead.get('status', '-')}
- Source: {lead.get('source', '-')}

RIWAYAT PERCAKAPAN WA:
{conversation_text}

CATATAN AGENT:
{notes_text}

Berikan output dalam JSON format:
{{"summary": "<rangkuman 2-3 kalimat tentang lead ini, kebutuhan, dan statusnya>", "preferences": {{"budget_range": "<extracted budget>", "preferred_areas": ["<area1>", "<area2>"], "property_types": ["<type1>"], "timeline": "<kapan butuh>", "special_requirements": "<hal khusus yang diminta>"}}, "recommended_action": "<1 kalimat rekomendasi langkah selanjutnya>", "follow_up_days": <angka: berapa hari lagi follow up>, "risk_level": "<low/medium/high - risiko cancel>"}}
"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OLLAMA_URL, json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            })

            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "").strip()

                try:
                    start = text.find("{")
                    end = text.rfind("}") + 1
                    if start >= 0 and end > start:
                        parsed = json.loads(text[start:end])
                    else:
                        parsed = json.loads(text)

                    return {
                        "summary": parsed.get("summary", ""),
                        "preferences": parsed.get("preferences", {}),
                        "recommended_action": parsed.get("recommended_action", ""),
                        "follow_up_days": parsed.get("follow_up_days", 7),
                        "risk_level": parsed.get("risk_level", "medium"),
                    }
                except json.JSONDecodeError:
                    return {"summary": text[:500], "recommended_action": "Review manual diperlukan"}
    except Exception as e:
        return {"summary": f"AI summary gagal: {str(e)}", "recommended_action": "Review manual"}

    return {"summary": "AI tidak tersedia", "recommended_action": "Review manual"}


async def match_properties(lead_preferences: dict, db_session) -> list:
    """Match lead preferences to property listings using SQL."""
    from sqlalchemy import text

    query_parts = []
    params = {}

    if lead_preferences.get("preferred_areas"):
        areas = lead_preferences["preferred_areas"]
        if areas and areas[0]:
            area_conditions = " OR ".join([f"LOWER(area_location) LIKE :area_{i} OR LOWER(cluster) LIKE :area_{i} OR LOWER(sektor) LIKE :area_{i}" for i in range(len(areas))])
            query_parts.append(f"({area_conditions})")
            for i, area in enumerate(areas):
                params[f"area_{i}"] = f"%{area.lower()}%"

    if lead_preferences.get("property_types"):
        types = lead_preferences["property_types"]
        if types and types[0]:
            type_conditions = " OR ".join([f"LOWER(property_type) LIKE :type_{i}" for i in range(len(types))])
            query_parts.append(f"({type_conditions})")
            for i, t in enumerate(types):
                params[f"type_{i}"] = f"%{t.lower()}%"

    if lead_preferences.get("budget_min"):
        query_parts.append("price >= :budget_min")
        params["budget_min"] = lead_preferences["budget_min"]

    if lead_preferences.get("budget_max"):
        query_parts.append("price <= :budget_max")
        params["budget_max"] = lead_preferences["budget_max"]

    where_clause = " AND ".join(query_parts) if query_parts else "1=1"

    results = db_session.execute(text(f"""
        SELECT id, title, slug, area_location, cluster, sektor, price, price_label,
               property_type, listing_type, land_area, building_area, bedrooms, bathrooms,
               is_hot, images
        FROM listings
        WHERE {where_clause}
          AND is_active = TRUE
        ORDER BY is_hot DESC, updated_at DESC
        LIMIT 5
    """), params).fetchall()

    return [dict(r._mapping) for r in results]
