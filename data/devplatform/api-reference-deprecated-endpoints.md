# DevPlatform API Reference — Deprecated Endpoints

> ⚠️ **NOTICE**: This document describes endpoints from DevPlatform API v2, which was deprecated on January 1, 2025. For current API documentation, please refer to the v3 API at api.devplatform.com/docs/v3.

## Deprecated Endpoints

### Tests

| Method | Endpoint | Replacement |
|---|---|---|
| GET | `/api/v2/tests` | `/api/v3/tests` |
| POST | `/api/v2/tests` | `/api/v3/tests` |
| PUT | `/api/v2/tests/{id}` | `/api/v3/tests/{id}` |
| DELETE | `/api/v2/tests/{id}` | `/api/v3/tests/{id}` |

### Candidates

| Method | Endpoint | Replacement |
|---|---|---|
| GET | `/api/v2/tests/{id}/candidates` | `/api/v3/tests/{id}/candidates` |
| POST | `/api/v2/tests/{id}/candidates` | `/api/v3/tests/{id}/candidates/invite` |
| GET | `/api/v2/tests/{id}/candidates/{cid}/report` | `/api/v3/tests/{id}/candidates/{cid}/report` |

### Questions

| Method | Endpoint | Replacement |
|---|---|---|
| GET | `/api/v2/questions` | `/api/v3/library/questions` |
| POST | `/api/v2/questions` | `/api/v3/library/questions` |

## Migration Guide

1. Update base URL from `api.devplatform.com/v2` to `api.devplatform.com/v3`
2. Update authentication: v3 uses Bearer tokens instead of API keys in query parameters
3. Response format changes: v3 returns camelCase field names instead of snake_case
4. Pagination: v3 uses cursor-based pagination instead of offset-based
5. Rate limits: v3 has stricter rate limits (100 requests/minute vs 1000 requests/minute in v2)

## Rate Limits (v3)

| Plan | Rate Limit | Burst Limit |
|---|---|---|
| Free | 10 requests/minute | 5 |
| Starter | 50 requests/minute | 25 |
| Professional | 100 requests/minute | 50 |
| Enterprise | 500 requests/minute | 100 |

## Common Error Codes

| Code | Meaning | Resolution |
|---|---|---|
| 400 | Bad Request | Check request body format |
| 401 | Unauthorized | Invalid or expired token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Wait and retry with exponential backoff |
| 500 | Internal Server Error | Retry after 30 seconds; if persistent, contact support |

## Support

For API issues: api-support@devplatform.com
Documentation: api.devplatform.com/docs
Status: status.devplatform.com
