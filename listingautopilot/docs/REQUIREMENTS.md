# Listing Autopilot Requirements

## 1. Product Summary

Listing Autopilot is a Pixii-aligned editable photo upgrader and Amazon listing creative engine.

It takes a product photo and optional product context, then generates an Amazon-ready creative pack:

- upgraded Amazon-ready product image
- Canva-style editable listing design preview
- editable layer JSON behind the visual preview
- listing quality score
- product and customer analysis
- key purchase criteria and pain points
- main image recommendation
- lifestyle image concept
- infographic callout plan
- Amazon title and bullets
- Markdown and JSON exports
- optional saved project history

The project demonstrates the core Pixii idea: convert weak ecommerce inputs into a beautiful visual output and editable listing design without asking the user to write prompts.

## 2. Target Users

Primary user:

- Amazon sellers, ecommerce founders, and small agencies with weak supplier photos who need listing assets quickly.

Secondary user:

- Ecommerce creative operators who need repeatable listing directions for many SKUs.

Reviewer user:

- Pixii founders or hiring reviewers who need to run the app without paid API keys and still see the product workflow.

## 3. User Problem

Amazon sellers often start with low-quality supplier photos from Alibaba, WhatsApp, manufacturer catalogs, or marketplace screenshots. Agency work is expensive and slow, while generic image/copy tools produce unstructured assets that are hard to edit or reuse.

Listing Autopilot solves this by turning one product photo plus optional context into a listing creative pack that looks closer to an ecommerce operator workflow than a generic chat prompt.

## 4. MVP Scope

### In Scope

- Streamlit dashboard as the first usable UI.
- FastAPI service with health, provider, generation, project, and metrics endpoints.
- Product photo upload.
- Optional product name, brand name, category, target customer, Amazon listing URL, competitor URL, and brand tone.
- Multi-provider LLM selection for `demo`, `openai`, `gemini`, and `anthropic`.
- Deterministic demo fallback when API keys are missing.
- Demo image upgrade pipeline that creates a clean white Amazon-style product image.
- Rendered editable design preview from the design JSON layer model.
- Listing readiness score.
- Creative pack generation.
- Editable design JSON generation.
- Markdown and design JSON export.
- Optional Postgres persistence for saved projects and Recent Projects.
- Alembic migration for persistence tables.
- Unit tests for pipeline, FastAPI app assembly, provider selection, and project CRUD.
- Local Docker Compose Postgres for persistence.

### Out Of Scope For Initial Version

- Real Amazon Seller Central integration.
- Shopify app installation.
- Real image generation/upscaling provider.
- Object storage for production media.
- Full canvas editor.
- Real user authentication and tenant onboarding.
- Celery or async worker queue.
- Large-scale review scraping.
- Competitor revenue estimation.
- Payment or subscription system.
- Exact Pixii product clone.

## 5. Functional Requirements

### FR-001: Upload Product Photo

The user can upload one product image.

Acceptance criteria:

- Supports `jpg`, `jpeg`, `png`, and `webp` in the Streamlit dashboard.
- FastAPI accepts multipart upload through the `image` form field.
- Empty uploads are rejected.
- Files above `MAX_UPLOAD_MB` are rejected by the API.
- The dashboard shows a preview before generation.

### FR-002: Capture Optional Listing Context

The user can optionally provide:

- product name
- brand name
- category
- target customer
- brand tone
- Amazon listing URL
- competitor URL

Acceptance criteria:

- The app works when only an image is provided.
- Optional fields are included in the generation context.
- Product name or uploaded filename is used as the saved project name.

### FR-003: Select LLM Provider

The system lets the user choose a model provider.

Supported providers:

- `demo`
- `openai`
- `gemini`
- `anthropic`

Acceptance criteria:

- Demo provider is always available.
- Live providers are available only when their environment variables are configured.
- If a requested live provider is not configured, the pipeline falls back to demo mode and returns a warning.

### FR-004: Product Analysis

The system analyzes the uploaded image and optional context.

Output includes:

- product name
- category
- description
- visible features
- likely use cases
- target customer
- visual issues
- selling angles

Acceptance criteria:

- Output validates against the product analysis schema.
- Demo output is deterministic enough for tests and review.
- Live provider output is parsed into the same structured schema.

### FR-005: Editable Photo Upgrade

The system returns image references for the original image, upgraded product image, and rendered editable listing design preview.

Initial implementation:

- Uses the demo image provider only when `demo` is selected.
- Uses OpenAI image edits when `openai` is selected and `OPENAI_API_KEY` is configured.
- Uses Gemini image editing when `gemini` is selected and `GEMINI_API_KEY` is configured.
- Normalizes upgraded images to a `2000x2000` Amazon-style PNG output.
- Writes local output references for upgraded image and rendered design preview.
- Records provider metadata.

Acceptance criteria:

- `images.provider` and `image_provider` are returned in the response.
- `images.upgraded_url` points to a generated PNG output.
- `images.design_preview_url` points to a rendered editable listing design preview.
- OpenAI/Gemini image-provider failures are surfaced instead of silently pretending a real edit happened.

### FR-006: Listing Quality Score

The system generates a listing readiness score.

Score dimensions:

- overall
- image quality
- Amazon readiness
- conversion potential
- benefit clarity
- proof readiness

Acceptance criteria:

- Each score is between `0` and `100`.
- Issues and recommendations are returned.
- Scoring is deterministic for tests.

### FR-007: Creative Pack Generation

The system generates Amazon listing creative content.

Output includes:

- Amazon title
- bullet points
- benefits
- customer pain points
- purchase criteria
- main image recommendation
- lifestyle image concept
- infographic headline
- infographic callouts
- A+ content ideas

Acceptance criteria:

- Copy is ecommerce-specific.
- The output avoids unsupported compliance, medical, or legal claims.
- The output uses product analysis and user context as source material.

### FR-008: Canva-Style Editable Listing Design

The system generates a visible listing design preview and a structured editable design specification.

Output includes:

- canvas size and background
- product image layer
- text layers
- callout layers
- style and metadata fields

Acceptance criteria:

- Design JSON is exportable as valid JSON.
- A rendered PNG preview is generated from the layer JSON.
- The design contains a product image layer and multiple text/callout layers.
- Layer positions are suitable for a future canvas editor.

### FR-009: Export Results

The user can export generated results.

MVP exports:

- Markdown report
- upgraded image PNG
- editable design preview PNG
- design JSON

Acceptance criteria:

- Downloads use generated response data.
- Export content changes when product input/context changes.

### FR-010: Save Project

When Postgres is configured and the user enables saving, the system persists a project.

Acceptance criteria:

- A `Project` row is created before generation.
- On success, status becomes `completed`.
- On failure, status becomes `failed` and error metadata is stored.
- Response payload and score payload are saved.
- Related rows are stored for provider run, uploaded asset, image assets, creative pack, design spec, editable design, and export artifacts.

### FR-011: Recent Projects

The dashboard and API expose recent saved projects.

Acceptance criteria:

- Streamlit sidebar shows recent saved projects when `DATABASE_URL` is configured.
- `GET /v1/projects/recent` returns recent project summaries.
- The endpoint returns an empty list when persistence is disabled.

### FR-012: Service API

The app exposes a FastAPI API for local and future frontend use.

Acceptance criteria:

- `GET /health` returns service status and version.
- `GET /v1/providers` lists provider availability.
- `POST /v1/generate` runs the same pipeline as the dashboard.
- `GET /v1/projects/recent` lists recent saved projects.
- `GET /v1/projects/{project_id}` returns project detail when persistence is enabled.
- `GET /v1/projects/{project_id}/assets` returns original/upgraded/preview image asset metadata.
- `GET /v1/assets/{asset_id}` returns one image asset.
- `GET /v1/projects/{project_id}/designs` returns editable design records.
- `GET /v1/designs/{design_id}` returns one editable design payload.
- `GET /metrics` exposes Prometheus metrics.

## 6. Non-Functional Requirements

### NFR-001: Maintainability

- Streamlit UI remains thin.
- Business logic lives in `src/listingautopilot/`.
- Provider logic is isolated under `llm/` and `image/`.
- Persistence code follows explicit SQLAlchemy model/schema/crud structure.
- Docs match the deployed code path.

### NFR-002: Reliability

- Demo mode works without paid API keys.
- Provider fallback returns a warning instead of silently failing.
- API validates upload emptiness and size.
- Persistence is optional; generation works without a database.

### NFR-003: Testability

- Core generation can run without external APIs.
- Provider fallback can be tested deterministically.
- CRUD can be tested without a live Postgres dependency.
- FastAPI app assembly, routes, metrics, and OpenAPI security are covered.

### NFR-004: Deployability

- Dashboard can run locally through `scripts/run_dashboard.sh`.
- API can run locally through `scripts/run_api.sh`.
- Postgres can run locally through Docker Compose.
- Alembic can create/update persistence schema.
- Streamlit Community Cloud can host the dashboard-first version.

### NFR-005: Security And Privacy

- `.env` is not committed.
- `.env.template` documents required configuration.
- API keys are read from environment variables.
- Uploaded images are treated as user-provided data.
- Bearer auth appears in OpenAPI for future production hardening, but auth enforcement is not part of the MVP.

## 7. Success Criteria

The initial version is successful if a reviewer can:

1. Open the dashboard.
2. Upload a product image.
3. Generate a complete creative pack without API keys.
4. See upgraded image, editable listing design preview, score, copy, creative direction, and editable design JSON.
5. Download the Markdown report, upgraded image, preview image, and design JSON.
6. Optionally configure Postgres and see saved projects in Recent Projects.
