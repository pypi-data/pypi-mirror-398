# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-25

### Added
- Initial release of ATHENA Python SDK
- Sync client (`Athena`) with full API coverage
- Async client (`AsyncAthena`) for high-performance applications
- Pydantic v2 models for all API responses
- 9 resource classes:
  - `calibrate` - Trust calibration analysis
  - `bias` - Cognitive bias detection
  - `trust_score` - Trust score calculation and trends
  - `audit` - Audit trail access
  - `webhooks` - Webhook management (CRUD, rotate secret, test)
  - `export` - Compliance report generation (EU AI Act, Texas TRAIGA, Colorado, FDA, California SB-53)
  - `stats` - Aggregated compliance metrics
  - `users` - At-risk user detection
  - `engines` - Engine status and industry benchmarks
- Webhook signature verification utilities
- Flask decorator (`@athena_webhook`) for webhook routes
- FastAPI async dependency (`verify_athena_webhook`) for webhook routes
- Automatic retry logic with exponential backoff
- Rate limit handling with `Retry-After` header support
- Custom error classes (`AthenaError`, `AuthenticationError`, `RateLimitError`, `ValidationError`, `NotFoundError`)
- Context manager support (`with` statements)
- Type hints (PEP 484) for all public APIs
- `py.typed` marker for PEP 561 compliance
- Comprehensive README with examples
- Python 3.9+ support

### Security
- HMAC-SHA256 webhook signature verification
- Constant-time signature comparison to prevent timing attacks
- Replay attack protection with timestamp validation (5-minute tolerance)

---

## [Unreleased]

Nothing yet!

---

[1.0.0]: https://github.com/athena-ai/sdk-python/releases/tag/v1.0.0

