# Security Implementation Matrix

**Status:** CANONICAL

This matrix tracks the physical implementation of the architectural requirements defined in `SECURITY_PRIVACY_SPEC.md`. Do not claim a requirement is implemented until it is proven in code or configuration.

| Requirement | Specification | Implementation | Test | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Encryption at Rest** | `SECURITY_PRIVACY_SPEC.md` | None | None | **PLANNED** | Database layer not yet instantiated. |
| **Encryption in Transit** | `SECURITY_PRIVACY_SPEC.md` | None | None | **PLANNED** | API Gateway / HTTPS not yet configured. |
| **Row/User Isolation (RLS)** | `SECURITY_PRIVACY_SPEC.md` | None | None | **PLANNED** | Requires PostgreSQL RLS policies. |
| **Ephemeral Processing** | `SECURITY_PRIVACY_SPEC.md` | None | None | **PLANNED** | Requires Redis TTL logic. |
| **Hard Deletion** | `SECURITY_PRIVACY_SPEC.md` | None | None | **PLANNED** | Requires user account management service. |
| **Least Privilege** | `SECURITY_PRIVACY_SPEC.md` | None | None | **PLANNED** | Requires service identity architecture. |
| **Secret Handling** | `SECURITY_PRIVACY_SPEC.md` | None | None | **PLANNED** | Requires Vault or cloud secret manager. |
| **Dev/Test Separation** | `SECURITY_PRIVACY_SPEC.md` | `test_*.py` | `test_method_career.py` | **IMPLEMENTED** | Test suites use Gandhi chart (public figure); no real user data. |
| **Audit Logging** | `SECURITY_PRIVACY_SPEC.md` | None | None | **PLANNED** | Requires structured logger and immutable sink. |
