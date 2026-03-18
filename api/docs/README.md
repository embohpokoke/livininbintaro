# Livininbintaro Documentation

## Active Versions

| Version | Date | Purpose | Status |
|---------|------|---------|--------|
| v2.1 | 2026-03-15 | Current implementation (unified API + Vue/PWA scaffold) | 🟢 ACTIVE |
| v2.0 | 2026-03-14 | Planning baseline & architecture docs | 🟡 ARCHIVED |

## Reading Order (Current)

1. `docs/v2.1/00-OVERVIEW.md` — What we built
2. `docs/v2.1/01-IMPLEMENTATION-STATUS.md` — Status & completion
3. `docs/v2.1/02-VERIFICATION.md` — How to verify

## Archived Versions

Old versions & historical docs stored in `_archived-v1-old/`:
- `v2.0/*` — Original planning phase
- OpenClaw task outputs (Codex sessions)

**Do not use for current work.** Reference only for historical context.

---

## Documentation Rules (All Projects)

**Single Source of Truth:** Project folder is the canonical location for docs
- VPS projects: `/root/[project-name]/docs/v[version]/`
- Backups: Desktop `~/Desktop/project/[project-name]/` (reference only)

**Archive Pattern:**
- Active docs: `docs/v[current]/` (e.g., `v2.1/`)
- Old versions: `docs/_archived-v[old]-old/` (e.g., `_archived-v1-old/`)
- Never delete, always move to `_archived-*` folder

**Cleanup Rules:**
1. After completing a version → move old docs to `_archived-v[N]-old/`
2. Update `README.md` with version table & status
3. Keep only relevant, current docs in main `docs/` folder
4. Desktop archive is **backup reference only**, not active workspace
5. OpenClaw workspace (`~/.openclaw/`) is **temporary build cache**, not permanent docs

**File Naming:**
- Pattern: `[project]-[feature]-v[major].[minor]-[date].md`
- Example: `livininbintaro-ui-audit-v1.0-20260222.md`

---

Last Updated: 2026-03-15 05:26 WIB
