from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Listing
from app.presenters import listing_to_dict, paginate

router = APIRouter(prefix="/public", tags=["public"])


def _apply_listing_filters(
    query,
    *,
    search: str | None = None,
    property_type: str | None = None,
    transaction_type: str | None = None,
    district: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    bedrooms: int | None = None,
):
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

    if transaction_type:
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


@router.get("/listings")
def get_public_listings(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    property_type: str | None = None,
    transaction_type: str | None = None,
    district: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    bedrooms: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Listing).filter(Listing.is_active.is_(True))
    query = _apply_listing_filters(
        query,
        property_type=property_type,
        transaction_type=transaction_type,
        district=district,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
    )
    total = query.count()
    listings = (
        query.order_by(Listing.updated_at.desc(), Listing.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return paginate([listing_to_dict(listing) for listing in listings], total, page, limit)


@router.get("/listings/hot")
def get_hot_listings(db: Session = Depends(get_db)):
    listings = (
        db.query(Listing)
        .filter(Listing.is_active.is_(True), Listing.is_hot.is_(True))
        .order_by(Listing.hot_date.desc())
        .limit(20)
        .all()
    )
    return [listing_to_dict(listing) for listing in listings]


@router.get("/listings/search")
def search_public_listings(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Listing).filter(Listing.is_active.is_(True))
    query = _apply_listing_filters(query, search=q)
    total = query.count()
    listings = (
        query.order_by(Listing.updated_at.desc(), Listing.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return paginate([listing_to_dict(listing) for listing in listings], total, page, limit)


@router.get("/listings/{listing_id}")
def get_public_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = (
        db.query(Listing)
        .filter(Listing.id == listing_id, Listing.is_active.is_(True))
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing_to_dict(listing)


@router.get("/districts")
def get_districts(db: Session = Depends(get_db)):
    rows = (
        db.query(Listing.area_location, func.count(Listing.id))
        .filter(Listing.is_active.is_(True), Listing.area_location.isnot(None))
        .group_by(Listing.area_location)
        .order_by(func.count(Listing.id).desc())
        .limit(50)
        .all()
    )
    return {
        "data": [
            {"district": district, "count": count}
            for district, count in rows
            if district
        ]
    }


@router.get("/stats")
def get_public_stats(db: Session = Depends(get_db)):
    total = db.query(Listing).filter(Listing.is_active.is_(True)).count()
    total_rumah = (
        db.query(Listing)
        .filter(Listing.is_active.is_(True), Listing.property_type == "rumah")
        .count()
    )
    return {
        "total_listings": total,
        "total_rumah": total_rumah,
    }
