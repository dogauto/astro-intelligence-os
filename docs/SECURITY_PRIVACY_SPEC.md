# Security and Privacy Specification

**Version:** 1.0.0
**Status:** CANONICAL

## 1. Core Principle
**Birth date, exact time, and precise geographic location constitute highly sensitive Personally Identifiable Information (PII).**
Astrological data can be used to infer sensitive traits, life events, or deanonymize individuals when combined with other datasets.

## 2. Data Protection Standards
- **Encryption at Rest:** All databases storing birth inputs, user profiles, or `AstroState` snapshots MUST use AES-256 encryption or equivalent.
- **Encryption in Transit:** All API traffic MUST enforce TLS 1.3.
- **Row/User Isolation:** Multi-tenant databases MUST enforce strict Row-Level Security (RLS) policies (e.g. via PostgreSQL). Users cannot query state objects they do not own.

## 3. Data Minimization & Retention
- **Ephemeral Processing:** If a chart is requested for a "one-off" query without an account, the `AstroState` must be deleted immediately or held only in an ephemeral Redis cache that TTLs (expires) within 24 hours.
- **Hard Deletion:** When a user deletes their profile, all associated birth data, `AstroState`s, and `MethodRun`s must be permanently purged, not soft-deleted.

## 4. Architecture Requirements
- **Least Privilege:** Microservices (like the Method Orchestrator) only receive the exact fields of `AstroState` they require.
- **Secret Handling:** API keys, database credentials, and signing secrets MUST be managed via a secure vault or environment injection. Never commit `.env` files.
- **Development/Test Separation:** The test suites MUST ONLY use public figure charts (e.g., Gandhi, historical events) or synthetic/mocked data. Real user data is strictly forbidden in local development environments.

## 5. Audit Logging
Every read/write operation against a `BirthInput` or `AstroState` must generate an immutable audit log detailing:
- Timestamp
- Actor (User ID or System Service)
- Action (Create, Read, Update, Delete)
- Resource ID
