# Documentation Archive

This directory contains historical documentation that has been completed or superseded.

## Purpose

Archived documents preserve the project's history and decision-making process while keeping active documentation clean and focused on current state.

## Archive Categories

### Planning (`planning/`)
- **project-brief-mvp-v2.4.md** - Original MVP planning document (Nov 2024 - Jan 2025)
  - Status: ✅ 100% Complete
  - Release: v0.2.0
  - Epic Coverage: EPIC-001 through EPIC-004
  - All planned features successfully delivered

## When to Archive

Documents should be archived when:
1. ✅ Planning documents are fully executed (all features delivered)
2. ✅ Design documents are superseded by new architecture
3. ✅ Process documents are no longer in use
4. ✅ Historical context is valuable but document is no longer "current"

## When NOT to Archive

Keep documents active when:
- ❌ They describe current system behavior
- ❌ They are referenced in active development workflows
- ❌ They contain non-historical information (current API docs, guides, etc.)

## Archive Guidelines

When archiving a document:
1. Add YAML frontmatter with `archived: true` and `archive_date`
2. Add completion/superseded status to frontmatter
3. Add visual banner at top indicating archived status
4. Update all references in active docs to point to archived location
5. Include version number in filename (e.g., `project-brief-mvp-v2.4.md`)

## Finding Current Documentation

For current project state, see:
- **README.md** - Project overview, features, installation
- **CHANGELOG.md** - Version history and changes
- **docs/epics/** - Epic-level planning (current and future)
- **docs/stories/** - Story-level specifications
- **docs/architecture/** - System architecture and ADRs

---

**Last Updated:** 2025-01-20
