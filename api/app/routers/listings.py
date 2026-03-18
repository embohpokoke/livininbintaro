import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import Listing
from app.presenters import listing_to_dict, paginate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/listings", tags=["listings"])
REPO_ROOT = Path(__file__).resolve().parents[2]


def _launch_background_command(args: list[str]):
    try:
        subprocess.Popen(
            args,
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        logger.exception("Failed to launch background command: %s", args)


def _build_query(
    db: Session,
    *,
    search: str | None = None,
    property_type: str | None = None,
    transaction_type: str | None = None,
    district: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    bedrooms: int | None = None,
    is_active: bool | None = None,
):
    query = db.query(Listing)
    if is_active is not None:
        query = query.filter(Listing.is_active.is_(is_active))

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Listing.title.ilike(term),
                Listing.address.ilike(term),
                Listing.area_location.ilike(term),
                Listing.cluster.ilike(term),
                Listing.sektor.ilike(term),
                Listing.cpa_code.ilike(term),
            )
        )

    if property_type:
        query = query.filter(Listing.property_type == property_type)
    if transaction_type in {"jual", "dijual"}:
        query = query.filter(Listing.listing_type.in_(["jual", "dijual"]))
    elif transaction_type in {"sewa", "disewa"}:
        query = query.filter(Listing.listing_type.in_(["sewa", "disewa"]))
    if district:
        term = f"%{district}%"
        query = query.filter(
            or_(
                Listing.area_location.ilike(term),
                Listing.cluster.ilike(term),
                Listing.sektor.ilike(term),
            )
        )
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    if bedrooms is not None:
        query = query.filter(Listing.bedrooms >= bedrooms)

    return query


@router.get("/hot")
def get_hot_listings(db: Session = Depends(get_db)):
    listings = (
        db.query(Listing)
        .filter(Listing.is_active.is_(True), Listing.is_hot.is_(True))
        .order_by(Listing.hot_date.desc())
        .limit(20)
        .all()
    )
    return [listing_to_dict(l, include_internal=False) for l in listings]


@router.get("/")
def get_listings(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    property_type: str | None = None,
    transaction_type: str | None = None,
    district: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    bedrooms: int | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    query = _build_query(
        db,
        search=search,
        property_type=property_type,
        transaction_type=transaction_type,
        district=district,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        is_active=is_active,
    )
    total = query.count()
    listings = (
        query.order_by(Listing.updated_at.desc(), Listing.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return paginate(
        [listing_to_dict(listing, include_internal=True) for listing in listings],
        total,
        page,
        limit,
    )


@router.get("/{listing_id}")
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing_to_dict(listing, include_internal=True)


@router.put("/{listing_id}")
def update_listing(
    listing_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    allowed_fields = {
        "title",
        "description",
        "property_type",
        "listing_type",
        "price",
        "price_label",
        "area_location",
        "cluster",
        "sektor",
        "address",
        "bedrooms",
        "bathrooms",
        "land_area",
        "building_area",
        "images",
        "drive_folder_id",
        "drive_link",
        "summary_client",
        "summary_ma",
        "is_active",
        "is_hot",
        "hot_reason",
        "hot_note",
    }
    for key, value in payload.items():
        if key in allowed_fields:
            setattr(listing, key, value)

    if "is_hot" in payload and payload["is_hot"] and not listing.hot_date:
        listing.hot_date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(listing)
    return listing_to_dict(listing, include_internal=True)


@router.post("/sync")
def trigger_listing_sync(
    background_tasks: BackgroundTasks,
    payload: dict = Body(default={}),
    current_user=Depends(require_admin),
):
    job_id = f"sync-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    args = ["python3", "sync_listings.py"]
    if payload.get("sync_images") or payload.get("full_sync"):
        args.append("--sync-images")
    background_tasks.add_task(_launch_background_command, args)
    return {
        "status": "syncing",
        "job_id": job_id,
        "estimated_duration": "5 minutes",
    }


@router.post("/sync/images")
def trigger_image_sync(
    background_tasks: BackgroundTasks,
    current_user=Depends(require_admin),
):
    job_id = f"images-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    background_tasks.add_task(_launch_background_command, ["python3", "sync_images.py"])
    return {
        "status": "syncing",
        "job_id": job_id,
        "estimated_duration": "10 minutes",
    }
