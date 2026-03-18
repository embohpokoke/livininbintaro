"""
Livininbintaro CRM — AI Recommendations Service (Phase C)
Functions:
- generate_lead_summary: AI summary from conversations + notes using Ollama
- match_properties: Property matching based on lead preferences
"""

import httpx
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List

from config import OLLAMA_URL, LLM_MODEL

logger = logging.getLogger("ai_recommendations")


async def generate_lead_summary(lead: dict, messages: list, notes: list) -> dict:
    """
    Generate AI summary from lead data, WA conversations, and agent notes.
    
    Args:
        lead: Lead data dict
        messages: List of WA message dicts (direction, message, created_at)
        notes: List of note dicts (content, created_at)
    
    Returns:
        dict with summary, preferences, recommended_action, follow_up_days, risk_level
    """
    
    # Build conversation text
    conversation_text = "\n".join([
        f"{'Agent' if m.get('direction') == 'outbound' else 'Client'}: {m.get('message', '')}"
        for m in messages[-30:]  # last 30 messages
    ]) or "Belum ada percakapan"
    
    # Build notes text
    notes_text = "\n".join([
        f"[{n.get('created_at', '')}] {n.get('content', '')}"
        for n in notes[-10:]  # last 10 notes
    ]) or "Belum ada catatan"
    
    # Build prompt
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
{{
    "summary": "<rangkuman 2-3 kalimat tentang lead ini, kebutuhan, dan statusnya>",
    "preferences": {{
        "budget_range": "<extracted budget>",
        "preferred_areas": ["<area1>", "<area2>"],
        "property_types": ["<type1>"],
        "timeline": "<kapan butuh>",
        "special_requirements": "<hal khusus yang diminta>"
    }},
    "recommended_action": "<1 kalimat rekomendasi langkah selanjutnya>",
    "follow_up_days": <angka: berapa hari lagi follow up>,
    "risk_level": "<low/medium/high - risiko cancel>"
}}
"""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OLLAMA_URL, json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3}
            })
            
            if response.status_code == 200:
                result = response.json()
                text = result.get("response", "").strip()
                
                # Try to parse JSON response
                try:
                    # Strip markdown code blocks if present
                    if text.startswith('```json'):
                        text = text.replace('```json', '').replace('```', '').strip()
                    elif text.startswith('```'):
                        text = text.replace('```', '').strip()
                    
                    parsed = json.loads(text)
                    return {
                        "summary": parsed.get("summary", ""),
                        "preferences": parsed.get("preferences", {}),
                        "recommended_action": parsed.get("recommended_action", ""),
                        "follow_up_days": parsed.get("follow_up_days", 7),
                        "risk_level": parsed.get("risk_level", "medium"),
                    }
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM, using raw text")
                    return {
                        "summary": text[:500] if text else "AI summary gagal",
                        "recommended_action": "Review manual diperlukan",
                        "follow_up_days": 7,
                        "risk_level": "medium",
                        "preferences": {}
                    }
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {
                    "summary": "AI summary error",
                    "recommended_action": "Review manual",
                    "follow_up_days": 7,
                    "risk_level": "medium",
                    "preferences": {}
                }
                
    except Exception as e:
        logger.error(f"AI summary error: {e}")
        return {
            "summary": f"AI summary gagal: {str(e)}",
            "recommended_action": "Review manual diperlukan",
            "follow_up_days": 7,
            "risk_level": "medium",
            "preferences": {}
        }


async def match_properties(lead_preferences: dict, db_conn) -> List[dict]:
    """
    Match lead preferences to property listings using SQL.
    
    Args:
        lead_preferences: Dict with preferred_areas, property_types, budget_range
        db_conn: Database connection
    
    Returns:
        List of matched property dicts
    """
    
    query_parts = []
    params = []
    
    # Budget matching
    budget_min = lead_preferences.get("budget_min")
    budget_max = lead_preferences.get("budget_max")
    
    if budget_min and budget_max:
        query_parts.append("price BETWEEN %s AND %s")
        params.extend([budget_min, budget_max])
    elif budget_max:
        query_parts.append("price <= %s")
        params.append(budget_max)
    
    # Area matching (extract key area names for better matching)
    preferred_areas = lead_preferences.get("preferred_areas", [])
    if preferred_areas:
        area_conditions = []
        for area in preferred_areas:
            # Extract key area name (e.g., "Bintaro Jaya" -> "Bintaro")
            area_clean = area.lower().strip()
            # Try to match the first word or common area name
            area_words = area_clean.split()
            
            if area_words:
                # Use first word for broader matching
                key_area = area_words[0]
                area_conditions.append("LOWER(area_location) LIKE %s")
                params.append(f"%{key_area}%")
        if area_conditions:
            query_parts.append(f"({' OR '.join(area_conditions)})")
    
    # Property type matching
    property_types = lead_preferences.get("property_types", [])
    if property_types:
        type_conditions = []
        for ptype in property_types:
            type_conditions.append("LOWER(property_type) LIKE %s")
            params.append(f"%{ptype.lower()}%")
        if type_conditions:
            query_parts.append(f"({' OR '.join(type_conditions)})")
    
    # Build WHERE clause
    where_clause = " AND ".join(query_parts) if query_parts else "1=1"
    
    # Execute query
    try:
        sql = f"""
            SELECT id, title, property_type, listing_type, price, price_label,
                   area_location, bedrooms, bathrooms, land_area, building_area,
                   is_hot, drive_link
            FROM public.listings
            WHERE {where_clause}
              AND is_active = TRUE
            ORDER BY is_hot DESC, updated_at DESC
            LIMIT 5
        """
        
        cursor = db_conn.execute(sql, params)
        results = cursor.fetchall()
        
        return [dict(r) for r in results]
        
    except Exception as e:
        logger.error(f"Property matching error: {e}")
        return []


def format_price(price: Optional[int]) -> str:
    """Format price in Indonesian Rupiah."""
    if not price:
        return "-"
    
    if price >= 1_000_000_000:
        return f"Rp {price / 1_000_000_000:.1f}M"
    elif price >= 1_000_000:
        return f"Rp {price / 1_000_000:.0f}jt"
    else:
        return f"Rp {price:,.0f}"
