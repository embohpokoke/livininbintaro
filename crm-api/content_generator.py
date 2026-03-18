"""
Livininbintaro CRM — AI Content Generator
Phase D: Social Media Content Automation
"""

import json
import httpx
from datetime import datetime
from typing import Dict, List, Optional

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "minimax-m2.5:cloud"  # Using same model as lead scoring

# Platform-specific guidelines
PLATFORM_GUIDELINES = {
    "instagram": "Instagram carousel post. Max 2200 chars. Gunakan emoji. Hook di kalimat pertama. CTA ke DM/WA. Hashtags 15-20.",
    "tiktok": "TikTok video script. Hook 3 detik pertama. Durasi 30-60 detik. Casual, energetic. CTA di akhir.",
    "facebook": "Facebook post. Bisa lebih panjang. Storytelling approach. Include link. Emoji moderate.",
    "wa_status": "WhatsApp Status. Singkat, 1-3 kalimat. Eye-catching. Langsung ke point.",
}

# Content pillar guidelines
PILLAR_GUIDELINES = {
    "property_spotlight": "Fokus pada 1 properti spesifik. Highlight unique selling points. Include harga dan spek.",
    "area_guide": "Edukasi tentang area di Bintaro. Data-driven. Perbandingan antar sektor. Target buyer profile.",
    "tips": "Tips praktis untuk buyer/renter. Checklist format. Save-worthy content.",
    "behind_scenes": "Behind the scenes jadi agen properti. Personal, relatable. Day-in-life format.",
}


async def generate_caption(
    property_data: Dict,
    platform: str,
    content_pillar: str,
    template: Optional[str] = None,
    ai_model: str = "ollama"
) -> Dict:
    """
    Generate social media caption from property data.

    Args:
        property_data: Dictionary with property info (judul, lokasi, harga, etc)
        platform: Target platform (instagram, tiktok, facebook, wa_status)
        content_pillar: Content type (property_spotlight, area_guide, tips, behind_scenes)
        template: Optional template text with placeholders
        ai_model: AI model to use (ollama or openclaw)

    Returns:
        Dictionary with caption, hook, hashtags, media_notes, alt_captions
    """

    platform_guide = PLATFORM_GUIDELINES.get(platform, '')
    pillar_guide = PILLAR_GUIDELINES.get(content_pillar, '')

    prompt = f"""Kamu adalah social media copywriter untuk Ocha, agen properti Century 21 Bintaro.
Brand voice: warm, trustworthy, knowledgeable friend yang kebetulan expert properti.

PLATFORM: {platform}
GUIDELINES: {platform_guide}

CONTENT PILLAR: {content_pillar}
GUIDELINES: {pillar_guide}

DATA PROPERTI:
- Judul: {property_data.get('title', '-')}
- Lokasi: {property_data.get('area_location', '-')}
- Harga: {property_data.get('price', '-')}
- Tipe: {property_data.get('property_type', '-')}
- Kamar Tidur: {property_data.get('bedrooms', '-')}
- Kamar Mandi: {property_data.get('bathrooms', '-')}
- Luas Tanah: {property_data.get('land_area', '-')}m²
- Luas Bangunan: {property_data.get('building_area', '-')}m²
- Deskripsi: {property_data.get('description', '-')}

{f'TEMPLATE REFERENCE:{chr(10)}{template}' if template else ''}

Output dalam JSON:
{{
    "caption": "<caption lengkap siap post>",
    "hook": "<kalimat hook pertama>",
    "hashtags": "<hashtags relevan>",
    "media_notes": "<catatan foto/video yang diperlukan>",
    "alt_captions": ["<alternatif caption 1>", "<alternatif caption 2>"]
}}

Tulis dalam Bahasa Indonesia casual tapi profesional. Jangan terlalu formal.
"""

    try:
        if ai_model == "openclaw":
            return await _call_openclaw(prompt)
        else:
            return await _call_ollama(prompt)
    except Exception as e:
        return {
            "caption": f"[Error generating: {str(e)}]",
            "hook": "",
            "hashtags": "",
            "media_notes": "",
            "alt_captions": []
        }


async def _call_ollama(prompt: str) -> Dict:
    """Call Ollama for caption generation."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7}
            })

            if response.status_code == 200:
                text = response.json().get("response", "").strip()

                # Try to parse as JSON
                try:
                    # Extract JSON from markdown code blocks if present
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()

                    result = json.loads(text)

                    # Ensure all required keys exist
                    return {
                        "caption": result.get("caption", text),
                        "hook": result.get("hook", ""),
                        "hashtags": result.get("hashtags", ""),
                        "media_notes": result.get("media_notes", ""),
                        "alt_captions": result.get("alt_captions", [])
                    }
                except json.JSONDecodeError:
                    # If not valid JSON, return the text as caption
                    return {
                        "caption": text,
                        "hook": "",
                        "hashtags": "",
                        "media_notes": "",
                        "alt_captions": []
                    }
            else:
                return {
                    "caption": f"[Ollama error: {response.status_code}]",
                    "hook": "",
                    "hashtags": "",
                    "media_notes": "",
                    "alt_captions": []
                }
    except Exception as e:
        return {
            "caption": f"[Ollama unavailable: {str(e)}]",
            "hook": "",
            "hashtags": "",
            "media_notes": "",
            "alt_captions": []
        }


async def _call_openclaw(prompt: str) -> Dict:
    """
    Call OpenClaw agent for higher quality copy.
    NOTE: OpenClaw endpoint needs to be configured.
    """
    # OpenClaw integration placeholder
    # This would connect to OpenClaw API endpoint if configured
    return {
        "caption": "[OpenClaw not configured yet]",
        "hook": "",
        "hashtags": "",
        "media_notes": "",
        "alt_captions": []
    }


async def generate_week_plan(listings: List[Dict], week_start: str) -> List[Dict]:
    """
    Generate a week's content plan from available listings.

    Distribution: 2 IG posts + 3 stories + 1 WA status per week

    Args:
        listings: List of property listings (hot/recent)
        week_start: Week start date (YYYY-MM-DD format)

    Returns:
        List of content plan items
    """

    plan = []

    # Tuesday: Property Spotlight (IG Post)
    if len(listings) > 0:
        plan.append({
            "day": "Tuesday",
            "platform": "instagram",
            "pillar": "property_spotlight",
            "format": "post",
            "property_id": listings[0].get("id"),
            "property_name": listings[0].get("judul", ""),
        })

    # Thursday: Area Guide or Tips (IG Post)
    plan.append({
        "day": "Thursday",
        "platform": "instagram",
        "pillar": "area_guide" if len(plan) % 2 == 0 else "tips",
        "format": "post",
        "property_id": None,
    })

    # Mon/Wed/Fri: Stories
    for day in ["Monday", "Wednesday", "Friday"]:
        plan.append({
            "day": day,
            "platform": "instagram",
            "pillar": "behind_scenes" if day == "Friday" else "property_spotlight",
            "format": "story",
        })

    # Saturday: WA Status
    if len(listings) > 1:
        plan.append({
            "day": "Saturday",
            "platform": "wa_status",
            "pillar": "property_spotlight",
            "format": "status",
            "property_id": listings[1].get("id") if len(listings) > 1 else None,
        })

    return plan


# Hashtag sets for different content types
HASHTAG_SETS = {
    "bintaro_general": "#bintaro #bintarojakarta #bintarosector #properti #property #rumahbintaro #rumahdijualbintaro #rumahbintarosouth #century21 #century21bintaro",
    "property_sell": "#dijual #dijualbintaro #rumahmurah #rumahidaman #rumahbaru #investasiproperti #propertibintaro",
    "property_rent": "#sewa #disewakan #rumahsewa #kontrakanrumah #sewabintaro",
    "tips": "#tipsrumah #tipsproperti #beliproperti #investasipemula #tipsinvestasi",
    "area_guide": "#infobintaro #bintarolife #livinginbintaro #bintarocommunity",
}


def get_hashtags(content_pillar: str, listing_type: str = "jual") -> str:
    """Get appropriate hashtags based on content type."""

    tags = [HASHTAG_SETS["bintaro_general"]]

    if content_pillar == "property_spotlight":
        if listing_type == "jual":
            tags.append(HASHTAG_SETS["property_sell"])
        else:
            tags.append(HASHTAG_SETS["property_rent"])
    elif content_pillar == "tips":
        tags.append(HASHTAG_SETS["tips"])
    elif content_pillar == "area_guide":
        tags.append(HASHTAG_SETS["area_guide"])

    return " ".join(tags)
