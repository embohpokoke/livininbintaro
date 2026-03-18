"""
Livininbintaro CRM — Content Calendar Router
Phase D: Social Media Content Management
"""

from datetime import date, datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import get_db, normalize_phone
import content_generator

router = APIRouter(prefix="/content", tags=["Content Calendar"])


# Pydantic models
class ContentCalendarCreate(BaseModel):
    property_id: Optional[int] = None
    platform: str
    content_pillar: Optional[str] = None
    post_date: str  # YYYY-MM-DD
    post_time: str = "10:00"
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    media_notes: Optional[str] = None


class ContentCalendarUpdate(BaseModel):
    property_id: Optional[int] = None
    platform: Optional[str] = None
    content_pillar: Optional[str] = None
    post_date: Optional[str] = None
    post_time: Optional[str] = None
    status: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[str] = None
    media_notes: Optional[str] = None


class GenerateCaptionRequest(BaseModel):
    property_id: Optional[int] = None
    platform: str
    content_pillar: str
    ai_model: str = "ollama"


class GenerateWeekPlanRequest(BaseModel):
    week_start: str  # YYYY-MM-DD


class EngagementUpdate(BaseModel):
    engagement_likes: Optional[int] = None
    engagement_comments: Optional[int] = None
    engagement_saves: Optional[int] = None
    engagement_shares: Optional[int] = None


# Helper functions
def dict_from_row(row) -> dict:
    """Convert database row to dictionary."""
    if row is None:
        return None
    return dict(row)


# Endpoints
@router.get("/calendar")
async def get_content_calendar(month: Optional[str] = None):
    """
    Get content calendar for a specific month.

    Args:
        month: YYYY-MM format (defaults to current month)

    Returns:
        List of content calendar entries
    """
    db = get_db()

    if month:
        try:
            year, m = month.split("-")
            start_date = date(int(year), int(m), 1)
            if int(m) == 12:
                end_date = date(int(year) + 1, 1, 1)
            else:
                end_date = date(int(year), int(m) + 1, 1)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")
    else:
        start_date = date.today().replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1)

    cursor = db.execute(
        """
        SELECT cc.*,
               l.title as property_name,
               l.area_location as property_location
        FROM content_calendar cc
        LEFT JOIN public.listings l ON cc.property_id = l.id
        WHERE cc.post_date >= ? AND cc.post_date < ?
        ORDER BY cc.post_date, cc.post_time
        """,
        (start_date, end_date)
    )

    entries = [dict_from_row(row) for row in cursor.fetchall()]
    db.close()

    return {"entries": entries, "month": month or start_date.strftime("%Y-%m")}


@router.get("/calendar/{entry_id}")
async def get_content_entry(entry_id: int):
    """Get a specific content calendar entry."""
    db = get_db()

    cursor = db.execute(
        """
        SELECT cc.*,
               l.title as property_name,
               l.area_location as property_location,
               l.price as property_price
        FROM content_calendar cc
        LEFT JOIN public.listings l ON cc.property_id = l.id
        WHERE cc.id = ?
        """,
        (entry_id,)
    )

    entry = cursor.fetchone()
    db.close()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return dict_from_row(entry)


@router.post("/calendar")
async def create_content_entry(body: ContentCalendarCreate):
    """Create a new content calendar entry."""
    db = get_db()

    cursor = db.execute(
        """
        INSERT INTO content_calendar (
            property_id, platform, content_pillar, post_date, post_time,
            caption, hashtags, media_notes, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING id
        """,
        (
            body.property_id,
            body.platform,
            body.content_pillar,
            body.post_date,
            body.post_time,
            body.caption or "",
            body.hashtags or "",
            body.media_notes or ""
        )
    )

    row = cursor.fetchone()
    entry_id = row[0]

    db.commit()
    db.close()

    return {"id": entry_id, "message": "Content entry created"}


@router.put("/calendar/{entry_id}")
async def update_content_entry(entry_id: int, body: ContentCalendarUpdate):
    """Update a content calendar entry."""
    db = get_db()

    # Build update query dynamically
    updates = []
    params = []

    if body.property_id is not None:
        updates.append("property_id = ?")
        params.append(body.property_id)

    if body.platform:
        updates.append("platform = ?")
        params.append(body.platform)

    if body.content_pillar:
        updates.append("content_pillar = ?")
        params.append(body.content_pillar)

    if body.post_date:
        updates.append("post_date = ?")
        params.append(body.post_date)

    if body.post_time:
        updates.append("post_time = ?")
        params.append(body.post_time)

    if body.status:
        updates.append("status = ?")
        params.append(body.status)

        # If marking as posted, set posted_at
        if body.status == "posted":
            updates.append("posted_at = CURRENT_TIMESTAMP")

    if body.caption is not None:
        updates.append("caption = ?")
        params.append(body.caption)

    if body.hashtags is not None:
        updates.append("hashtags = ?")
        params.append(body.hashtags)

    if body.media_notes is not None:
        updates.append("media_notes = ?")
        params.append(body.media_notes)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(entry_id)

    db.execute(
        f"UPDATE content_calendar SET {', '.join(updates)} WHERE id = ?",
        tuple(params)
    )

    db.commit()
    db.close()

    return {"message": "Content entry updated"}


@router.delete("/calendar/{entry_id}")
async def delete_content_entry(entry_id: int):
    """Delete a content calendar entry."""
    db = get_db()

    db.execute("DELETE FROM content_calendar WHERE id = ?", (entry_id,))
    db.commit()
    db.close()

    return {"message": "Content entry deleted"}


@router.post("/generate-caption")
async def generate_content_caption(body: GenerateCaptionRequest):
    """
    Generate AI caption for content.

    Args:
        body: Property ID, platform, content pillar, AI model

    Returns:
        Generated caption with alternatives
    """
    db = get_db()

    # Get property data if property_id provided
    property_data = {}
    if body.property_id:
        cursor = db.execute(
            """
            SELECT title, area_location, price, property_type, bedrooms, bathrooms,
                   land_area, building_area, description, listing_type
            FROM public.listings
            WHERE id = ?
            """,
            (body.property_id,)
        )
        row = cursor.fetchone()
        if row:
            property_data = dict_from_row(row)

    # Get template if available
    template = None
    cursor = db.execute(
        """
        SELECT template_text
        FROM content_templates
        WHERE content_pillar = ?
          AND platform = ?
          AND is_active = TRUE
        LIMIT 1
        """,
        (body.content_pillar, body.platform)
    )
    row = cursor.fetchone()
    if row:
        template = row[0]

    db.close()

    # Generate caption using AI
    result = await content_generator.generate_caption(
        property_data=property_data,
        platform=body.platform,
        content_pillar=body.content_pillar,
        template=template,
        ai_model=body.ai_model
    )

    # Add suggested hashtags if not provided
    if not result.get("hashtags") and property_data:
        result["hashtags"] = content_generator.get_hashtags(
            body.content_pillar,
            property_data.get("listing_type", "jual")
        )

    result["ai_model_used"] = body.ai_model

    return result


@router.post("/generate-week-plan")
async def generate_week_content_plan(body: GenerateWeekPlanRequest):
    """
    Generate a week's content plan from hot/recent listings.

    Args:
        body: Week start date (YYYY-MM-DD)

    Returns:
        Planned content schedule for the week
    """
    db = get_db()

    # Get hot/recent listings for content
    cursor = db.execute(
        """
        SELECT id, title, area_location, price, property_type, listing_type
        FROM public.listings
        WHERE is_active = TRUE
        ORDER BY is_hot DESC, updated_at DESC
        LIMIT 5
        """
    )

    listings = [dict_from_row(row) for row in cursor.fetchall()]
    db.close()

    # Generate week plan
    plan = await content_generator.generate_week_plan(listings, body.week_start)

    return {
        "week_start": body.week_start,
        "plan": plan,
        "listings_available": len(listings)
    }


@router.put("/calendar/{entry_id}/engagement")
async def update_engagement(entry_id: int, body: EngagementUpdate):
    """Update engagement metrics for a posted content."""
    db = get_db()

    updates = []
    params = []

    if body.engagement_likes is not None:
        updates.append("engagement_likes = ?")
        params.append(body.engagement_likes)

    if body.engagement_comments is not None:
        updates.append("engagement_comments = ?")
        params.append(body.engagement_comments)

    if body.engagement_saves is not None:
        updates.append("engagement_saves = ?")
        params.append(body.engagement_saves)

    if body.engagement_shares is not None:
        updates.append("engagement_shares = ?")
        params.append(body.engagement_shares)

    if not updates:
        raise HTTPException(status_code=400, detail="No engagement metrics to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(entry_id)

    db.execute(
        f"UPDATE content_calendar SET {', '.join(updates)} WHERE id = ?",
        tuple(params)
    )

    db.commit()
    db.close()

    return {"message": "Engagement updated"}


@router.get("/templates")
async def get_content_templates(
    platform: Optional[str] = None,
    content_pillar: Optional[str] = None
):
    """Get available content templates."""
    db = get_db()

    query = "SELECT * FROM content_templates WHERE is_active = TRUE"
    params = []

    if platform:
        query += " AND platform = ?"
        params.append(platform)

    if content_pillar:
        query += " AND content_pillar = ?"
        params.append(content_pillar)

    query += " ORDER BY name"

    cursor = db.execute(query, tuple(params))
    templates = [dict_from_row(row) for row in cursor.fetchall()]
    db.close()

    return {"templates": templates}


@router.get("/stats")
async def get_content_stats():
    """Get content performance statistics."""
    db = get_db()

    # Total posts by platform
    cursor = db.execute(
        """
        SELECT platform, COUNT(*) as count, status
        FROM content_calendar
        GROUP BY platform, status
        ORDER BY platform, status
        """
    )
    platform_stats = [dict_from_row(row) for row in cursor.fetchall()]

    # Engagement stats for posted content
    cursor = db.execute(
        """
        SELECT
            COUNT(*) as total_posts,
            SUM(engagement_likes) as total_likes,
            SUM(engagement_comments) as total_comments,
            SUM(engagement_saves) as total_saves,
            SUM(engagement_shares) as total_shares,
            AVG(engagement_likes) as avg_likes,
            AVG(engagement_comments) as avg_comments
        FROM content_calendar
        WHERE status = 'posted'
        """
    )
    engagement = dict_from_row(cursor.fetchone())

    # Recent high-performing posts
    cursor = db.execute(
        """
        SELECT id, platform, content_pillar, post_date,
               engagement_likes, engagement_comments, engagement_saves
        FROM content_calendar
        WHERE status = 'posted'
        ORDER BY (engagement_likes + engagement_comments * 2 + engagement_saves * 3) DESC
        LIMIT 10
        """
    )
    top_posts = [dict_from_row(row) for row in cursor.fetchall()]

    db.close()

    return {
        "platform_stats": platform_stats,
        "engagement": engagement,
        "top_posts": top_posts
    }
