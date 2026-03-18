"""
Livininbintaro CRM — AI Lead Scoring via Ollama
"""

import httpx
import json
from datetime import datetime
from config import OLLAMA_URL, LLM_MODEL


async def score_lead(lead: dict) -> dict:
    """Score a lead 0-100 using Ollama. Falls back to rule-based."""

    prompt = f"""You are a property lead scoring assistant for a Century 21 Bintaro real estate agent.

Score this lead from 0-100 based on these weighted factors:
- Budget specificity (25%): Does the lead have a clear budget range?
- Area specificity (20%): Does the lead mention specific areas in Bintaro?
- Urgency signals (20%): Are there signs they need to buy/rent soon?
- Engagement level (20%): How responsive/detailed is the lead?
- Source quality (15%): Where did the lead come from?

Lead data:
- Name: {lead.get('name', 'Unknown')}
- Budget: {lead.get('budget_min', 'Not specified')} - {lead.get('budget_max', 'Not specified')}
- Preferred Area: {lead.get('preferred_area', 'Not specified')}
- Property Type: {lead.get('preferred_type', 'Not specified')}
- Source: {lead.get('source', 'other')}
- Status: {lead.get('status', 'new')}
- Message: {(lead.get('message') or 'None')[:500]}
- Notes: {(lead.get('notes') or 'None')[:500]}

Respond ONLY in this exact JSON format:
{{"score": <0-100>, "reason": "<1-2 sentence explanation in Bahasa Indonesia>"}}
"""

    # AI scoring via Ollama DISABLED — using rule-based scoring only
    # To re-enable: remove this early return
    return _rule_based(lead)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(OLLAMA_URL, json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3},
            })
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    parsed = json.loads(text[start:end])
                else:
                    parsed = json.loads(text)
                score = max(0, min(100, int(parsed.get("score", 50))))
                reason = parsed.get("reason", "AI scored this lead")
                return {"score": score, "reason": reason, "tier": _tier(score)}
    except Exception as e:
        print(f"[AI Scoring] Ollama error: {e}, using fallback")

    return _rule_based(lead)


def _rule_based(lead: dict) -> dict:
    score = 30
    reasons = []

    if lead.get("budget_min") and lead.get("budget_max"):
        score += 25
        reasons.append("budget jelas")
    elif lead.get("budget_min") or lead.get("budget_max"):
        score += 12
        reasons.append("budget partial")

    if lead.get("preferred_area"):
        score += 20
        reasons.append("area spesifik")

    if lead.get("preferred_type"):
        score += 10
        reasons.append("tipe properti jelas")

    source_scores = {
        "whatsapp": 15, "web_form": 12, "referral": 20,
        "social_media": 8, "walk_in": 18, "other": 5,
    }
    score += source_scores.get(lead.get("source", "other"), 5)

    if lead.get("status") in ("appointment", "site_visit", "offer", "counter_offer"):
        score += 10
        reasons.append("sudah engaged")

    msg = lead.get("message", "")
    if msg:
        urgency_words = ["segera", "urgent", "cepat", "butuh", "mau", "cari", "pindah"]
        if any(w in msg.lower() for w in urgency_words):
            score += 8
            reasons.append("sinyal urgensi")

    score = min(100, score)
    reason = "Rule-based: " + ", ".join(reasons) if reasons else "Lead baru, data minimal"
    return {"score": score, "reason": reason, "tier": _tier(score)}


def _tier(score: int) -> str:
    if score >= 80:
        return "hot"
    if score >= 60:
        return "warm"
    if score >= 40:
        return "cool"
    return "cold"
