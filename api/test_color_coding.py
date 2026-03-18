#!/usr/bin/env python3
"""
Test color coding logic before implementing in main script.
"""

def get_color_status(bg_color):
    """Map RGB color to listing status.
    
    Returns: tuple (is_active, is_hot, hot_reason)
    """
    if not bg_color:
        return True, False, None  # Default active
    
    # White: {red: 1, green: 1, blue: 1}
    if bg_color == {"red": 1, "green": 1, "blue": 1}:
        return True, False, None
    
    # Red: {red: 1}
    if bg_color == {"red": 1}:
        return False, False, None  # Sold
    
    # Yellow: {red: 1, green: 1}
    if bg_color == {"red": 1, "green": 1}:
        return False, False, None  # Cancelled
    
    # Cyan: blue+green dominant, little/no red
    if ("blue" in bg_color and "green" in bg_color and 
        bg_color.get("red", 1) < 0.9):
        return True, True, "sheet"  # Hot sale
    
    # Other colors - default active
    return True, False, None

def apply_color_to_listing(listing_data, color_status, existing_hot_reason=None):
    """Apply color-based status to listing data.
    
    Constraint: Don't overwrite user-set hot_reason='user'
    """
    is_active, is_hot, hot_reason = color_status
    
    # Update is_active based on color
    listing_data["is_active"] = is_active
    
    # Only update is_hot and hot_reason if not user-set
    if existing_hot_reason != "user":
        listing_data["is_hot"] = is_hot
        if hot_reason:
            listing_data["hot_reason"] = hot_reason
        elif is_hot and "hot_reason" in listing_data:
            # Clear hot_reason if not hot anymore
            listing_data["hot_reason"] = None
    
    return listing_data

# Test cases
test_colors = [
    ({"red": 1}, "Red → sold"),
    ({"red": 1, "green": 1}, "Yellow → cancelled"),
    ({"blue": 0.8, "green": 0.9, "red": 0.1}, "Cyan → hot sale"),
    ({"red": 1, "green": 1, "blue": 1}, "White → active"),
    ({"red": 0.5, "green": 0.5, "blue": 0.5}, "Gray → active (default)"),
    (None, "No color → active (default)"),
]

print("Testing color mapping logic:")
print("=" * 60)
for color, desc in test_colors:
    is_active, is_hot, hot_reason = get_color_status(color)
    status_desc = f"Active: {is_active}, Hot: {is_hot}, Reason: {hot_reason}"
    print(f"{desc:30} → {status_desc}")

print("\n" + "=" * 60)
print("Testing constraint: hot_reason='user' should not be overwritten")

listing = {"title": "Test Listing", "is_active": True, "is_hot": False, "hot_reason": "user"}
color_status = (True, True, "sheet")  # Cyan would make it hot
result = apply_color_to_listing(listing.copy(), color_status, existing_hot_reason="user")
print(f"Original: {listing}")
print(f"After cyan (user-set): {result}")
print(f"is_hot unchanged? {listing['is_hot'] == result['is_hot']} (should be True)")

# Test without user constraint
listing2 = {"title": "Test Listing 2", "is_active": True, "is_hot": False}
result2 = apply_color_to_listing(listing2.copy(), color_status)
print(f"\nOriginal: {listing2}")
print(f"After cyan (no user): {result2}")
print(f"is_hot changed? {listing2['is_hot'] != result2['is_hot']} (should be True)")

print("\n✅ Color coding logic test complete!")
