# API ENDPOINTS REFERENCE — LIVININBINTARO V2.0

**Version:** 1.0
**Date:** 2026-03-14
**Base URL:** `https://livininbintaro.my.id/api`

---

## OVERVIEW

V2.0 API is a unified FastAPI backend combining public listings endpoints and authenticated CRM endpoints.

**Authentication:** JWT Bearer token in `Authorization` header

**Rate Limiting:** None (internal use only)

**Response Format:** JSON

---

## AUTHENTICATION

### POST /api/auth/login

Login to get JWT token.

**Request:**

```json
{
  "email": "ocha@livininbintaro.my.id",
  "password": "password123"
}
```

**Response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "ocha@livininbintaro.my.id",
    "full_name": "Ocha",
    "role": "agent"
  },
  "expires_at": "2026-03-21T10:30:00Z"
}
```

**Status Codes:**
- `200` - Success
- `401` - Invalid credentials
- `422` - Validation error

**Example:**

```bash
curl -X POST https://livininbintaro.my.id/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ocha@livininbintaro.my.id",
    "password": "password123"
  }'
```

---

## PUBLIC ENDPOINTS (No Auth Required)

### GET /api/public/listings

Get paginated property listings.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `limit` | integer | 20 | Items per page (max 100) |
| `property_type` | string | null | Filter: "rumah", "tanah", "apartemen" |
| `transaction_type` | string | null | Filter: "dijual", "disewa" |
| `district` | string | null | Filter by district |
| `min_price` | number | null | Minimum price |
| `max_price` | number | null | Maximum price |
| `bedrooms` | integer | null | Minimum bedrooms |

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "listing_code": "BSD001",
      "property_name": "Rumah Modern Minimalis",
      "property_type": "rumah",
      "transaction_type": "dijual",
      "price": 2500000000,
      "bedrooms": 3,
      "bathrooms": 2,
      "land_area": 120,
      "building_area": 90,
      "address": "Jl. Raya BSD No. 123",
      "district": "BSD",
      "city": "Tangerang Selatan",
      "province": "Banten",
      "description": "Rumah modern dengan desain minimalis...",
      "facilities": ["AC", "Water Heater", "Carport"],
      "images": [
        "https://livininbintaro.my.id/images/BSD001-1.jpg",
        "https://livininbintaro.my.id/images/BSD001-2.jpg"
      ],
      "is_active": true,
      "created_at": "2026-01-15T08:00:00Z",
      "updated_at": "2026-03-10T12:30:00Z"
    }
  ],
  "total": 17930,
  "page": 1,
  "limit": 20,
  "total_pages": 897
}
```

**Example:**

```bash
curl "https://livininbintaro.my.id/api/public/listings?page=1&limit=10&property_type=rumah&min_price=1000000000&max_price=3000000000"
```

---

### GET /api/public/listings/{id}

Get single property listing by ID.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Listing ID |

**Response:**

```json
{
  "id": 1,
  "listing_code": "BSD001",
  "property_name": "Rumah Modern Minimalis",
  "property_type": "rumah",
  "transaction_type": "dijual",
  "price": 2500000000,
  "bedrooms": 3,
  "bathrooms": 2,
  "land_area": 120,
  "building_area": 90,
  "address": "Jl. Raya BSD No. 123",
  "district": "BSD",
  "city": "Tangerang Selatan",
  "province": "Banten",
  "description": "Rumah modern dengan desain minimalis di lokasi strategis...",
  "facilities": ["AC", "Water Heater", "Carport", "Taman"],
  "images": [
    "https://livininbintaro.my.id/images/BSD001-1.jpg",
    "https://livininbintaro.my.id/images/BSD001-2.jpg",
    "https://livininbintaro.my.id/images/BSD001-3.jpg"
  ],
  "drive_folder_id": "1A2B3C4D5E6F",
  "is_active": true,
  "created_at": "2026-01-15T08:00:00Z",
  "updated_at": "2026-03-10T12:30:00Z"
}
```

**Status Codes:**
- `200` - Success
- `404` - Listing not found

**Example:**

```bash
curl https://livininbintaro.my.id/api/public/listings/1
```

---

### GET /api/public/listings/search

Search listings with keyword.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search keyword (property name, address, district) |
| `page` | integer | Page number |
| `limit` | integer | Items per page |

**Response:**

Same as `/api/public/listings` but filtered by keyword.

**Example:**

```bash
curl "https://livininbintaro.my.id/api/public/listings/search?q=BSD&page=1&limit=20"
```

---

### GET /api/public/districts

Get list of available districts.

**Response:**

```json
{
  "data": [
    {"district": "BSD", "count": 5230},
    {"district": "Bintaro", "count": 4120},
    {"district": "Serpong", "count": 3890},
    {"district": "Gading Serpong", "count": 2450},
    {"district": "Alam Sutera", "count": 2240}
  ]
}
```

**Example:**

```bash
curl https://livininbintaro.my.id/api/public/districts
```

---

## LISTINGS ENDPOINTS (Auth Required)

### GET /api/listings

Get all listings (agent view, includes inactive).

**Headers:**

```
Authorization: Bearer <token>
```

**Query Parameters:**

Same as `/api/public/listings` plus:

| Parameter | Type | Description |
|-----------|------|-------------|
| `is_active` | boolean | Filter by active status |

**Response:**

Same structure as public endpoint.

**Example:**

```bash
curl https://livininbintaro.my.id/api/listings?is_active=false \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### PUT /api/listings/{id}

Update listing (admin only).

**Request:**

```json
{
  "property_name": "Updated Name",
  "price": 2800000000,
  "description": "Updated description...",
  "is_active": true
}
```

**Response:**

```json
{
  "id": 1,
  "listing_code": "BSD001",
  "property_name": "Updated Name",
  "price": 2800000000,
  "updated_at": "2026-03-14T10:45:00Z"
}
```

**Status Codes:**
- `200` - Success
- `403` - Forbidden (agent role cannot update)
- `404` - Listing not found

---

### POST /api/listings/sync

Trigger Google Sheets sync (admin only).

**Request:**

```json
{
  "full_sync": false
}
```

**Response:**

```json
{
  "status": "syncing",
  "job_id": "sync-20260314-104500",
  "estimated_duration": "5 minutes"
}
```

**Example:**

```bash
curl -X POST https://livininbintaro.my.id/api/listings/sync \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"full_sync": true}'
```

---

## LEADS ENDPOINTS (Auth Required)

### GET /api/leads

Get all leads with optional filters.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: "inbox", "active", "follow_up", "non_lead", "closed" |
| `source` | string | Filter: "whatsapp", "website", "referral" |
| `min_score` | integer | Minimum AI score (0-100) |
| `page` | integer | Page number |
| `limit` | integer | Items per page |

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "name": "Budi Santoso",
      "phone": "628123456789",
      "email": "budi@example.com",
      "source": "whatsapp",
      "status": "active",
      "ai_score": 78,
      "ai_reasoning": "High intent: mentioned budget 2-3M, looking for BSD area, timeline 1-2 months",
      "interested_properties": [1, 5, 12],
      "created_at": "2026-03-10T08:30:00Z",
      "updated_at": "2026-03-14T09:15:00Z"
    }
  ],
  "total": 110,
  "page": 1,
  "limit": 20
}
```

**Example:**

```bash
curl "https://livininbintaro.my.id/api/leads?status=active&min_score=60" \
  -H "Authorization: Bearer <token>"
```

---

### GET /api/leads/{id}

Get single lead details.

**Response:**

```json
{
  "id": 1,
  "name": "Budi Santoso",
  "phone": "628123456789",
  "email": "budi@example.com",
  "source": "whatsapp",
  "status": "active",
  "ai_score": 78,
  "ai_reasoning": "High intent: mentioned budget 2-3M, looking for BSD area, timeline 1-2 months",
  "interested_properties": [
    {
      "id": 1,
      "property_name": "Rumah Modern Minimalis",
      "price": 2500000000,
      "district": "BSD"
    }
  ],
  "created_at": "2026-03-10T08:30:00Z",
  "updated_at": "2026-03-14T09:15:00Z"
}
```

**Example:**

```bash
curl https://livininbintaro.my.id/api/leads/1 \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/leads

Create new lead.

**Request:**

```json
{
  "name": "Rina Wijaya",
  "phone": "628987654321",
  "email": "rina@example.com",
  "source": "website",
  "status": "inbox",
  "interested_properties": [5, 10]
}
```

**Response:**

```json
{
  "id": 111,
  "name": "Rina Wijaya",
  "phone": "628987654321",
  "email": "rina@example.com",
  "source": "website",
  "status": "inbox",
  "ai_score": null,
  "created_at": "2026-03-14T10:50:00Z"
}
```

**Status Codes:**
- `201` - Created
- `422` - Validation error

---

### PUT /api/leads/{id}

Update lead.

**Request:**

```json
{
  "status": "follow_up",
  "interested_properties": [1, 5, 12, 15]
}
```

**Response:**

```json
{
  "id": 1,
  "name": "Budi Santoso",
  "status": "follow_up",
  "interested_properties": [1, 5, 12, 15],
  "updated_at": "2026-03-14T11:00:00Z"
}
```

**Example:**

```bash
curl -X PUT https://livininbintaro.my.id/api/leads/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "follow_up"}'
```

---

### POST /api/leads/{id}/score

Trigger AI scoring for a lead.

**Request:**

```json
{}
```

**Response:**

```json
{
  "id": 1,
  "ai_score": 82,
  "ai_reasoning": "Very high intent: confirmed budget 2.5M (exact), wants BSD specifically, timeline urgent (1 month), engaged in conversation (5 messages exchanged)",
  "scored_at": "2026-03-14T11:05:00Z"
}
```

**Example:**

```bash
curl -X POST https://livininbintaro.my.id/api/leads/1/score \
  -H "Authorization: Bearer <token>"
```

---

### GET /api/leads/counts

Get lead counts per status bucket.

**Response:**

```json
{
  "inbox": 45,
  "active": 30,
  "follow_up": 20,
  "non_lead": 10,
  "closed": 5,
  "total": 110
}
```

**Example:**

```bash
curl https://livininbintaro.my.id/api/leads/counts \
  -H "Authorization: Bearer <token>"
```

---

## WHATSAPP ENDPOINTS (Auth Required)

### GET /api/wa/messages/{lead_id}

Get WhatsApp conversation for a lead.

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "lead_id": 1,
      "phone": "628123456789",
      "message_text": "Halo, saya tertarik dengan rumah di BSD",
      "media_url": null,
      "direction": "inbound",
      "timestamp": "2026-03-10T08:30:00Z"
    },
    {
      "id": 2,
      "lead_id": 1,
      "phone": "628123456789",
      "message_text": "Halo Pak Budi! Terima kasih sudah menghubungi. Ada budget berapa dan preferensi area?",
      "media_url": null,
      "direction": "outbound",
      "timestamp": "2026-03-10T08:32:00Z"
    },
    {
      "id": 3,
      "lead_id": 1,
      "phone": "628123456789",
      "message_text": "Budget saya 2-3M, prefer BSD atau Gading Serpong",
      "media_url": null,
      "direction": "inbound",
      "timestamp": "2026-03-10T08:35:00Z"
    }
  ],
  "total": 14
}
```

**Example:**

```bash
curl https://livininbintaro.my.id/api/wa/messages/1 \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/wa/send

Send WhatsApp message to a lead.

**Request:**

```json
{
  "lead_id": 1,
  "message": "Pak Budi, saya ada rekomendasi properti yang cocok dengan budget dan preferensi Bapak. Bisa saya share?"
}
```

**Response:**

```json
{
  "id": 15,
  "lead_id": 1,
  "phone": "628123456789",
  "message_text": "Pak Budi, saya ada rekomendasi...",
  "direction": "outbound",
  "timestamp": "2026-03-14T11:10:00Z",
  "gowa_status": "sent"
}
```

**Status Codes:**
- `201` - Message sent
- `500` - GOWA error

**Example:**

```bash
curl -X POST https://livininbintaro.my.id/api/wa/send \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 1,
    "message": "Test message"
  }'
```

---

### POST /api/webhook/gowa

Webhook endpoint for incoming WhatsApp messages (public, no auth).

**Request from GOWA:**

```json
{
  "from": "628123456789",
  "name": "Budi Santoso",
  "message": "Halo, saya tertarik dengan rumah di BSD",
  "media_url": null,
  "timestamp": "2026-03-14T11:15:00Z"
}
```

**Response:**

```json
{
  "status": "ok",
  "lead_id": 1,
  "message_id": 16
}
```

**Notes:**
- Auto-creates lead if phone number not found
- Stores message in `crm.wa_messages` table
- Can trigger AI scoring if configured

---

## NOTES ENDPOINTS (Auth Required)

### GET /api/leads/{lead_id}/notes

Get notes for a lead.

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "lead_id": 1,
      "content": "Klien prefer rumah dengan halaman luas untuk anak bermain",
      "created_by": {
        "id": 1,
        "full_name": "Ocha"
      },
      "created_at": "2026-03-10T09:00:00Z"
    },
    {
      "id": 2,
      "lead_id": 1,
      "content": "Follow up: kirim katalog rumah BSD 2-3M",
      "created_by": {
        "id": 1,
        "full_name": "Ocha"
      },
      "created_at": "2026-03-11T14:30:00Z"
    }
  ]
}
```

**Example:**

```bash
curl https://livininbintaro.my.id/api/leads/1/notes \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/leads/{lead_id}/notes

Add note to a lead.

**Request:**

```json
{
  "content": "Klien setuju untuk survey lokasi hari Sabtu, 16 Maret jam 10 pagi"
}
```

**Response:**

```json
{
  "id": 3,
  "lead_id": 1,
  "content": "Klien setuju untuk survey lokasi hari Sabtu, 16 Maret jam 10 pagi",
  "created_by": {
    "id": 1,
    "full_name": "Ocha"
  },
  "created_at": "2026-03-14T11:20:00Z"
}
```

**Example:**

```bash
curl -X POST https://livininbintaro.my.id/api/leads/1/notes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test note"}'
```

---

## ACTIVITIES ENDPOINTS (Auth Required)

### GET /api/leads/{lead_id}/activities

Get activity timeline for a lead.

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "lead_id": 1,
      "activity_type": "wa_message",
      "description": "Sent WhatsApp message",
      "created_at": "2026-03-10T08:30:00Z"
    },
    {
      "id": 2,
      "lead_id": 1,
      "activity_type": "status_change",
      "description": "Status changed: inbox → active",
      "created_at": "2026-03-10T09:00:00Z"
    },
    {
      "id": 3,
      "lead_id": 1,
      "activity_type": "ai_score",
      "description": "AI scored: 78 (High intent)",
      "created_at": "2026-03-10T09:05:00Z"
    }
  ]
}
```

**Example:**

```bash
curl https://livininbintaro.my.id/api/leads/1/activities \
  -H "Authorization: Bearer <token>"
```

---

## AI RECOMMENDATIONS ENDPOINT (Auth Required)

### GET /api/leads/{lead_id}/recommendations

Get AI recommendations for a lead.

**Response:**

```json
{
  "lead_id": 1,
  "ai_recommendations": {
    "properties": [
      {
        "id": 5,
        "property_name": "Rumah Cluster BSD",
        "price": 2800000000,
        "match_score": 95,
        "reason": "Perfect match: BSD area, 3 bedrooms, within budget 2-3M, has large yard"
      },
      {
        "id": 12,
        "property_name": "Rumah Modern Gading Serpong",
        "price": 2600000000,
        "match_score": 88,
        "reason": "Good match: Gading Serpong (preferred area), 3 bedrooms, within budget"
      }
    ],
    "follow_up_timing": {
      "next_contact": "2026-03-15T10:00:00Z",
      "reason": "High intent lead, contact within 24 hours"
    },
    "talking_points": [
      "Highlight large yard for children",
      "Mention proximity to good schools in BSD",
      "Offer site visit this weekend"
    ],
    "risk_assessment": {
      "likelihood_to_close": "high",
      "reasoning": "Confirmed budget, specific area preference, urgent timeline"
    }
  },
  "generated_at": "2026-03-14T11:25:00Z"
}
```

**Example:**

```bash
curl https://livininbintaro.my.id/api/leads/1/recommendations \
  -H "Authorization: Bearer <token>"
```

---

## CONTENT CALENDAR ENDPOINTS (Auth Required)

### GET /api/content-calendar

Get content calendar posts.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: "draft", "scheduled", "posted" |
| `start_date` | date | Filter from date (YYYY-MM-DD) |
| `end_date` | date | Filter to date (YYYY-MM-DD) |

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "post_type": "property_spotlight",
      "content": "🏡 Rumah Modern Minimalis di BSD\n\n✅ 3 KT, 2 KM\n✅ LT 120m², LB 90m²\n✅ Harga: 2.5M\n\nHub: 0811-1111-2222\n\n#BSD #RumahDijual #PropertyBintaro",
      "scheduled_date": "2026-03-15",
      "status": "scheduled",
      "platform": "instagram",
      "created_at": "2026-03-14T10:00:00Z"
    }
  ]
}
```

**Example:**

```bash
curl "https://livininbintaro.my.id/api/content-calendar?status=scheduled&start_date=2026-03-15&end_date=2026-03-31" \
  -H "Authorization: Bearer <token>"
```

---

### POST /api/content-calendar

Create content calendar post.

**Request:**

```json
{
  "post_type": "property_spotlight",
  "content": "Generated caption...",
  "scheduled_date": "2026-03-16",
  "platform": "instagram"
}
```

**Response:**

```json
{
  "id": 2,
  "post_type": "property_spotlight",
  "content": "Generated caption...",
  "scheduled_date": "2026-03-16",
  "status": "draft",
  "created_at": "2026-03-14T11:30:00Z"
}
```

---

### PUT /api/content-calendar/{id}

Update content post.

**Request:**

```json
{
  "status": "posted"
}
```

**Response:**

```json
{
  "id": 1,
  "status": "posted",
  "updated_at": "2026-03-15T14:00:00Z"
}
```

---

## DASHBOARD ENDPOINTS (Auth Required)

### GET /api/dashboard/stats

Get dashboard statistics.

**Response:**

```json
{
  "leads": {
    "total": 110,
    "new_this_week": 8,
    "by_status": {
      "inbox": 45,
      "active": 30,
      "follow_up": 20,
      "non_lead": 10,
      "closed": 5
    },
    "avg_ai_score": 67
  },
  "properties": {
    "total": 17930,
    "active": 17912,
    "new_this_week": 12
  },
  "activities": {
    "total_this_week": 42,
    "wa_messages": 28,
    "notes_added": 10,
    "status_changes": 4
  },
  "content": {
    "scheduled_this_week": 5,
    "posted_this_week": 3
  }
}
```

**Example:**

```bash
curl https://livininbintaro.my.id/api/dashboard/stats \
  -H "Authorization: Bearer <token>"
```

---

### GET /api/dashboard/today-tasks

Get tasks for today.

**Response:**

```json
{
  "follow_ups": [
    {
      "lead_id": 5,
      "lead_name": "Rina Wijaya",
      "last_contact": "2026-03-07T10:00:00Z",
      "reason": "No contact for 7 days"
    }
  ],
  "scheduled_content": [
    {
      "id": 1,
      "post_type": "property_spotlight",
      "platform": "instagram",
      "scheduled_date": "2026-03-14"
    }
  ],
  "high_priority_leads": [
    {
      "lead_id": 1,
      "lead_name": "Budi Santoso",
      "ai_score": 82,
      "reason": "High score + active status"
    }
  ]
}
```

**Example:**

```bash
curl https://livininbintaro.my.id/api/dashboard/today-tasks \
  -H "Authorization: Bearer <token>"
```

---

## ERROR RESPONSES

All endpoints return consistent error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

**Common Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INTERNAL_ERROR` | 500 | Server error |
| `GOWA_ERROR` | 500 | WhatsApp service error |
| `OLLAMA_ERROR` | 500 | AI service error |

---

## RATE LIMITING

Currently no rate limiting implemented (internal use only).

Future: 100 requests/minute per user.

---

## WEBHOOKS

### GOWA WhatsApp Webhook

**Endpoint:** `POST /api/webhook/gowa`

**Authentication:** None (signature verification planned)

**Payload:**

```json
{
  "from": "628123456789",
  "name": "Sender Name",
  "message": "Message text",
  "media_url": "https://example.com/image.jpg",
  "timestamp": "2026-03-14T11:40:00Z"
}
```

**Behavior:**
- Auto-create lead if phone not found
- Store message in database
- Trigger AI scoring (optional)
- Send auto-reply (optional)

---

**Document Version:** 1.0
**Last Updated:** 2026-03-14
**Next Review:** After Phase 2 implementation
