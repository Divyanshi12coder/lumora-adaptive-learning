# Lumora REST API

Interactive OpenAPI docs are served by FastAPI at **`/docs`** (Swagger UI) and **`/redoc`**. The raw schema is at `/openapi.json`.
All endpoints are prefixed with `/api`. Authenticated endpoints need `Authorization: Bearer <JWT>`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | – | Liveness + DB check, active AI/embedding provider |
| POST | `/adaptive/preview` | – | Runs the real adaptive engine on simulated signals for a 0–100 learner level (landing slider) |
| POST | `/demo/tutor` | – | "Watch the tutor adapt": engine + RAG + offline demo provider |
| POST | `/auth/register` | – | Create an account → JWT + user |
| POST | `/auth/login` | – | Sign in → JWT + user (generic error, no account enumeration) |
| POST | `/auth/logout` | ✓ | Revokes **all** tokens for the user (token-version bump) |
| GET | `/me` | ✓ | Current user + preferences |
| DELETE | `/me` | ✓ | Permanently delete the account and all learning data |
| GET / PUT | `/profile` | ✓ | Profile + learning/accessibility preferences |
| GET | `/subjects` | ✓ | Subjects → topics with the learner's mastery and stage |
| GET | `/courses` | ✓ | Courses |
| GET | `/topics?subject=` | ✓ | Topic cards |
| GET | `/lessons/{id}` | ✓ | Lesson whose sections are expanded or collapsed by the engine |
| POST | `/lessons/{id}/start` | ✓ | Same as above, plus a `lesson_started` event and a persisted strategy |
| POST | `/lessons/{id}/complete` | ✓ | `lesson_completed` event (seconds, progress) |
| POST | `/sessions/start` · `/sessions/{id}/end` | ✓ | Learning sessions |
| POST | `/interactions` | ✓ | Record one event or a batch (≤ 50). Unknown payload keys are dropped |
| POST | `/quiz/generate` | ✓ | Personalized quiz: difficulty, length, options and review items chosen by the engine |
| GET | `/quiz/{attempt}/hint/{question}` | ✓ | Hint at the strategy's hint level (logs `hint_requested`) |
| POST | `/quiz/{attempt}/submit` | ✓ | Grade → BKT update → results, mistakes, revision plan, next difficulty |
| POST | `/tutor/chat` | ✓ | Ask Divi (safety → intent → strategy → RAG → LLM → output safety) |
| GET | `/tutor/history[?conversation_id=]` | ✓ | List conversations, or the messages of one |
| POST | `/tutor/messages/{id}/feedback` | ✓ | `helpful` · `too_long` · `too_hard` · `too_easy` · `not_helpful`. Adjusts preference biases |
| GET | `/dashboard` | ✓ | Child-friendly dashboard payload |
| GET | `/analytics?days=` | ✓ | Grown-up analytics: trends, topic performance, engine decisions, ML insight |
| GET | `/adaptive/strategy?topic_id=` | ✓ | Full engine output with factor weights |
| GET | `/ml/model-card` | ✓ | Training provenance and held-out metrics |
| GET | `/recommendations[?refresh=true]` | ✓ | Ranked next steps with factors |
| POST | `/study-plan` | ✓ | Study plan from the ranking (LLM or demo) |
| GET / POST | `/goals` · PATCH / DELETE `/goals/{id}` | ✓ | Learning goals |
| GET / POST | `/documents` | ✓ | List visible docs / upload `.txt` `.md` `.pdf` (≤ 5 MB, multipart) |
| GET | `/documents/search?q=` | ✓ | Inspect what the retriever returns |
| GET | `/documents/{id}` | ✓ | Document + chunk preview |
| POST | `/documents/{id}/ingest` | ✓ | Chunk → embed → store in pgvector |
| POST | `/documents/{id}/summary` | ✓ | Summary (LLM or extractive demo) |
| DELETE | `/documents/{id}` | ✓ | Delete your own document (built-in library documents are read-only) |

## Example

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"demo@lumora.app","password":"LumoraDemo2026!"}' | jq -r .access_token)

curl -s -X POST localhost:8000/api/tutor/chat -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"message":"How do plants make food?"}' | jq '.message | {content, sources: [.sources[] | .title]}'
```

## Errors

Errors always come back as `{"detail": "<friendly sentence>"}`. Validation errors also include `errors: [{field, message}]`.
Unhandled exceptions return a generic message and never include a stack trace. Rate-limited requests get `429` with `Retry-After`.
