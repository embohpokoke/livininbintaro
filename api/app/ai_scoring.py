import httpx
import json
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "minimax-m2.5:cloud"


async def score_lead(lead: dict) -> dict:
    """Score a lead using Ollama MiniMax. Falls back to rule-based if Ollama unavailable."""

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
- Source: {lead.get('source', 'manual')}
- Status: {lead.get('status', 'new')}
- Notes: {lead.get('notes', 'None')}

Respond ONLY in this exact JSON format:
{{"score": <0-100>, "reason": "<1-2 sentence explanation in Bahasa Indonesia>"}}
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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
                    # Try to extract JSON from response
                    start = text.find("{")
                    end = text.rfind("}") + 1
                    if start >= 0 and end > start:
                        parsed = json.loads(text[start:end])
                    else:
                        parsed = json.loads(text)
                    score = max(0, min(100, int(parsed.get("score", 50))))
                    reason = parsed.get("reason", "AI scored this lead")
                except (json.JSONDecodeError, ValueError):
                    return _rule_based_score(lead)

                tier = _get_tier(score)
                return {"score": score, "reason": reason, "tier": tier, "scored_at": datetime.utcnow().isoformat()}
            else:
                return _rule_based_score(lead)

    except Exception as e:
        print(f"[AI Scoring] Ollama error: {e}, using fallback")
        return _rule_based_score(lead)


def _rule_based_score(lead: dict) -> dict:
    """Fallback rule-based scoring when Ollama is unavailable."""
    score = 30
    reasons = []

    if lead.get('budget_min') and lead.get('budget_max'):
        score += 25
        reasons.append("budget jelas")
    elif lead.get('budget_min') or lead.get('budget_max'):
        score += 12
        reasons.append("budget partial")

    if lead.get('preferred_area') and str(lead['preferred_area']).strip():
        score += 20
        reasons.append("area spesifik")

    if lead.get('preferred_type') and str(lead['preferred_type']).strip():
        score += 10
        reasons.append("tipe properti jelas")

    source_scores = {'rumah123': 15, '99co': 15, 'instagram': 10, 'facebook': 8, 'whatsapp': 12, 'web': 10, 'manual': 5}
    source = lead.get('source', 'manual')
    score += source_scores.get(source, 5)

    if lead.get('status') in ['appointment', 'showing', 'negotiation']:
        score += 10
        reasons.append("sudah engaged")

    score = min(100, score)
    reason = "Rule-based: " + ", ".join(reasons) if reasons else "Lead baru, data minimal"
    tier = _get_tier(score)

    return {"score": score, "reason": reason, "tier": tier, "scored_at": datetime.utcnow().isoformat()}


def _get_tier(score: int) -> str:
    if score >= 80:
        return "hot"
    if score >= 60:
        return "warm"
    if score >= 40:
        return "cool"
    return "cold"
