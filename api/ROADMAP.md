# Livininbintaro Roadmap

*Last updated: 2026-02-27*

---

## Completed

### Phase A — Core Platform (2026-02-19)
- Property listings import (17,950+ from Google Drive)
- Leads management CRUD with filtering/pagination
- Lead status tracking and activity log
- Google Drive image sync (`sync_images.py`)

### Phase B — WhatsApp Integration (2026-02-26)
- Fonnte webhook: auto-create lead from inbound WA
- `wa_messages` table: full conversation storage
- Auto-reply welcome message for new contacts
- WA send via API + chat UI in frontend
- 4 default WA templates (welcome, D+1, D+7, D+14)
- Daily auto follow-up cron at 10:00 WIB
- GOWA webhook handler (`wa.py`) added 2026-02-24

### Phase C — AI Features (2026-02-26)
- AI lead summary via Ollama (`minimax-m2.5:cloud`)
- Property matching: SQL-based vs 17,950 listings by area/type/budget
- Lead scoring (`ai_scoring.py`)
- Auto follow-up scheduling from AI analysis
- Lead detail overlay with notes, AI summary, recommendations, timeline
- Notes system (`lead_notes` table): manual/ai_generated/system types
- Daily follow-up reminder to Ocha at 08:00 WIB

### Phase D — UI Polish (2026-02-27)
- Lead detail overlay with slide-in animation
- Mobile-first layout (430px max)
- Remove CPA code from listing cards
- Share button on listing detail (Web Share API)
- Load more button (pagination)
- Lazy image loading
- Dashboard mini charts (CSS progress bars)

---

## Pending / Next Steps

### Near-term
- [ ] Wire up GOWA for both Fonnte & GOWA webhook (QR scan pending)
- [ ] Test AI recommendations with real lead data
- [ ] Verify follow-up cron is registered in crontab
- [ ] Property image lazy loading performance test

### Future
- [ ] Lead pipeline kanban view
- [ ] Bulk WhatsApp broadcast to filtered leads
- [ ] Integration with property portals (Rumah123, OLX)
- [ ] Revenue/commission tracking for Ocha
- [ ] Mobile app (PWA wrapper)

---

*Update this file when features are completed or new ones are planned.*
