def format_listing_summary(listing):
    """Format a single listing with CPA, location, type, price, and link.
    
    Format:
    CPA XXXX | Location | DIJUAL/DISEWA | Harga
    https://livininbintaro.my.id/listing/slug
    """
    cpa = listing.get("cpa_code", "N/A").strip()
    title = listing.get("title", "N/A")
    cluster = listing.get("cluster", "")
    address = listing.get("address", "")
    
    # Use cluster if available, fallback to address, fallback to title
    location = cluster if cluster else (address if address else title)
    
    listing_type = listing.get("listing_type", "").upper()
    if listing_type in ["JUAL", "DIJUAL"]:
        listing_type = "DIJUAL"
    elif listing_type in ["SEWA", "DISEWA"]:
        listing_type = "DISEWA"
    
    price = format_price(listing.get("price"))
    slug = listing.get("slug", "")
    
    # Format: CPA | Location | Type | Price
    line = f"{cpa} | {location} | {listing_type} | {price}"
    
    # Add link if slug available
    if slug:
        url = f"https://livininbintaro.my.id/listing/{slug}"
        line = f"{line}\n{url}"
    
    return line
