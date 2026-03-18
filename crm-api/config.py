"""
Livininbintaro CRM — Configuration
Updated: 2026-03-07 - Migrated to PostgreSQL
"""

# Database configuration
# OLD: SQLite (migrated 2026-03-07)
# DB_PATH = "/var/www/livininbintaro/crm-api/livininbintaro.db"

# NEW: PostgreSQL (schema: crm)
DATABASE_URL = "postgresql://livin:L1v1n!B1nt4r0_2026@localhost:5432/livininbintaro"
DB_SCHEMA = "crm"

# GOWA WhatsApp API (Livininbintaro instance, port 3004)
GOWA_URL = "http://127.0.0.1:3004"
GOWA_AUTH = ("livinin", "livininwa2026")
GOWA_WEBHOOK_SECRET = "liviningowaSecret2026"

# Ollama LLM
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
LLM_MODEL = "minimax-m2.5:cloud"

# Agent phone for SLA alerts
AGENT_PHONE = "62811309991"

# Valid enums
VALID_BUCKETS = ["inbox", "qualified", "showing", "negotiation", "closed", "nurture"]
VALID_STATUSES = [
    "new", "contacted", "qualified", "appointment", "site_visit",
    "offer", "counter_offer", "closed_won", "closed_lost",
    "re_engage", "long_term",
]
VALID_SOURCES = ["whatsapp", "web_form", "referral", "social_media", "walk_in", "other"]
VALID_TEMPLATE_CATEGORIES = ["greeting", "follow_up", "recommendation", "thank_you", "reminder"]

STATUS_TO_BUCKET = {
    "new": "inbox",
    "contacted": "inbox",
    "qualified": "qualified",
    "appointment": "showing",
    "site_visit": "showing",
    "offer": "negotiation",
    "counter_offer": "negotiation",
    "closed_won": "closed",
    "closed_lost": "closed",
    "re_engage": "nurture",
    "long_term": "nurture",
}
