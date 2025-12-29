# Epic 14: Multilingual Console Client

**Goal**: Add internationalization (i18n) support to console client for multiple languages, expanding global adoption and accessibility.

**Value**: Makes tool accessible to non-English speaking teams, supports global enterprises, and demonstrates commitment to inclusivity.

**Priority**: Low (Post-MVP enhancement)

---

## Story 14.1: i18n Framework Integration

As a developer,
I want internationalization framework integrated into console client,
So that all user-facing text can be translated into multiple languages.

**Acceptance Criteria:**

**Given** console client with i18n support
**When** user sets language preference
**Then** all CLI output displays in selected language

**And** language selection via: LANGUAGE env var (e.g., LANGUAGE=es_ES), --language flag, system locale detection

**And** supported languages initially: English (en_US), Spanish (es_ES), Portuguese (pt_BR), French (fr_FR)

**And** translations for: command help text, error messages, success messages, table headers, prompts

**And** fallback to English if translation missing (no crashes)

**And** language files: ./locales/en_US.json, ./locales/es_ES.json, etc.

**And** translation API: _("message") or t("message") function for all user-facing strings

**And** pluralization support: handle singular/plural forms correctly per language

**Prerequisites:** Epic 5 complete (console client)

**Technical Notes:**
- Use gettext or babel for i18n: from babel.support import Translations
- Translation files: GNU gettext (.po files) or JSON format
- Extract strings: pybabel extract -o messages.pot . (creates template)
- Translation workflow: developers mark strings → extract → translators translate → compile
- Locale detection: import locale; locale.getdefaultlocale()
- Format strings: support variable interpolation: _("Queue {name} created").format(name=queue_name)
- Date/time formatting: locale-aware using babel.dates

---
