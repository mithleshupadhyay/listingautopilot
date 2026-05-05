# Low-Level Design

## 1. Repository Structure

```text
listingautopilot/
├── alembic/
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_initial_project_persistence.py
│       ├── 0002_assets_designs.py
│       └── 63b9a5e4570d_noop_after_assets_designs.py
├── dashboard/
│   └── streamlit_app.py
├── docs/
│   ├── API.md
│   ├── HLD.md
│   ├── LLD.md
│   ├── REQUIREMENTS.md
│   ├── USER_FLOW.md
│   └── db/
├── outputs/
├── scripts/
│   ├── run_api.sh
│   ├── run_dashboard.sh
│   └── test.sh
├── src/
│   └── listingautopilot/
│       ├── analysis/
│       ├── api/
│       ├── core/
│       ├── db/pgv/
│       ├── domain/
│       ├── exporters/
│       ├── image/
│       ├── llm/
│       ├── schemas/
│       ├── config.py
│       ├── exceptions.py
│       └── main.py
├── tests/
│   └── unit/
├── main.py
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── Dockerfile.app
├── Makefile
└── docker-compose.yml
```

## 2. Package Modules

### `api/`

FastAPI routes and the generation orchestrator.

- `health.py`: `GET /health`.
- `providers.py`: `GET /v1/providers`.
- `generation.py`: `POST /v1/generate` and `generate_listing_pack`.
- `projects.py`: recent project and project detail endpoints.
- `assets.py`: saved image asset endpoints.
- `designs.py`: saved editable design endpoints.
- `dependencies.py`: optional DB session dependency.

### `analysis/`

Business logic for the creative workflow.

- `product_analyzer.py`: turns image/context into structured product analysis.
- `creative_planner.py`: creates title, bullets, pain points, criteria, and visual concepts.
- `listing_scorer.py`: creates deterministic listing readiness scores.
- `design_json_builder.py`: builds editable design layers.

### `llm/`

Provider selection and structured provider schemas.

- `schemas.py`: provider config and output schemas.
- `providers.py`: provider availability, labels, env keys, and fallback selection.
- `client.py`: provider-facing service functions.
- `prompts.py`: prompt constants/templates.

### `image/`

Image upgrade pipeline.

- `upgrade_pipeline.py`: stable image pipeline entrypoint.
- `providers/demo.py`: demo provider that creates a `2000x2000` Amazon-style product image.
- `design_renderer.py`: renders editable design JSON into a PNG preview.

### `db/pgv/`

Postgres-style persistence layer.

- `db.py`: SQLAlchemy base, engine, session factory, DB dependency.
- `models/projects.py`: project and child table models.
- `models/assets.py`: first-class image asset model for original, upgraded, and preview images.
- `models/designs.py`: editable listing design model linked to preview image asset.
- `schemas/projects.py`: Pydantic DB schemas and search schemas.
- `schemas/assets.py`: image asset schemas.
- `schemas/designs.py`: editable design schemas.
- `crud/projects.py`: explicit create/get/list/update/delete/search functions.
- `crud/assets.py`: explicit image asset CRUD functions.
- `crud/designs.py`: explicit editable design CRUD functions.

### `exporters/`

Export builders.

- `markdown.py`: Markdown report.
- `design_json.py`: JSON export string.

### `dashboard/`

Streamlit UI that calls the generation orchestrator directly.

## 3. Generation Flow

```mermaid
sequenceDiagram
    participant UI as Streamlit or API
    participant Gen as generation.py
    participant DB as Project CRUD
    participant LLM as LLM Provider
    participant IMG as Image Pipeline
    participant EXP as Exporters

    UI->>Gen: GenerateRequest
    opt request.save_to_db and db session exists
        Gen->>DB: create_project()
    end
    Gen->>LLM: build_llm_client()
    Gen->>LLM: analyze_product()
    Gen->>IMG: upgrade_image()
    Gen->>LLM: plan_creative_pack()
    Gen->>Gen: score_listing()
    Gen->>LLM: build_design_json()
    Gen->>IMG: render_design_preview()
    Gen->>EXP: export_markdown_report()
    Gen->>EXP: export_design_json()
    opt request.save_to_db and project exists
        Gen->>DB: update_project_status(completed)
    end
    Gen-->>UI: GenerateResponse
```

Failure behavior:

- If generation fails after project creation, project status is updated to `failed`.
- The exception is re-raised so the API/UI can show the error.
- If no DB session exists, the pipeline still runs without persistence.

## 4. Request Model

`GenerateRequest` contains:

- `product_name`
- `brand_name`
- `category`
- `target_customer`
- `brand_tone`
- `amazon_listing_url`
- `competitor_url`
- `image_filename`
- `image_content_type`
- `image_bytes`
- `llm_provider`
- `use_demo_mode`
- `save_to_db`

Streamlit builds this model from UI inputs. FastAPI builds it from multipart form data.

## 5. Response Model

`GenerateResponse` contains:

- `request_id`
- `mode`: `demo`, `live`, or `mixed`
- `project_id`
- `llm_provider`
- `llm_model`
- `image_provider`
- `product`
- `score`
- `creative_pack`
- `images`
  - `original_url`
  - `upgraded_url`
  - `design_preview_url`
- `editable_design`
- `exports`
- `warnings`

This single response shape is used by both Streamlit and FastAPI.

## 6. Persistence Model

```mermaid
erDiagram
    PROJECTS ||--o{ UPLOADED_ASSETS : has
    PROJECTS ||--o{ GENERATION_JOBS : has
    PROJECTS ||--o{ PROVIDER_RUNS : has
    PROJECTS ||--o{ CREATIVE_PACKS : has
    PROJECTS ||--o{ DESIGN_SPECS : has
    PROJECTS ||--o{ IMAGE_ASSETS : has
    PROJECTS ||--o{ EDITABLE_DESIGNS : has
    PROJECTS ||--o{ EXPORT_ARTIFACTS : has

    PROJECTS {
        uuid id
        string name
        string brand_name
        string product_name
        string category
        string status
        json request_payload
        json response_payload
        json score_payload
        string customer_id
        string created_by
        datetime created_at
        datetime updated_at
        boolean is_deleted
        datetime deleted_at
    }
```

Saved generation data:

- `projects.request_payload`: request metadata.
- `projects.response_payload`: full generated response.
- `projects.score_payload`: score object for quick listing.
- `uploaded_assets`: uploaded asset metadata.
- `image_assets`: original upload, upgraded product image, and rendered design preview metadata.
- `provider_runs`: provider/model/mode metadata.
- `creative_packs`: generated creative pack data.
- `design_specs`: editable design JSON data.
- `editable_designs`: Canva-style design payload with preview asset reference.
- `export_artifacts`: report and design JSON exports.

## 7. CRUD Style

`db/pgv/crud/projects.py` follows the direct service style used in the reference service.

Project CRUD exposes:

- `create_project`
- `get_project`
- `list_projects`
- `list_recent_projects`
- `update_project`
- `update_project_status`
- `delete_project`
- `undelete_project`
- `list_deleted_projects`
- `search_projects`

Image asset CRUD exposes:

- `create_image_asset`
- `get_image_asset`
- `list_project_image_assets`
- `list_recent_image_assets`
- `update_image_asset`
- `delete_image_asset`
- `search_image_assets`

Editable design CRUD exposes:

- `create_editable_design`
- `get_editable_design`
- `list_project_designs`
- `update_editable_design`
- `attach_design_preview`
- `delete_editable_design`
- `search_editable_designs`

The functions use explicit SQLAlchemy `query().filter().first()/all()` patterns, commit directly, and raise `HTTPException` for API-facing persistence errors.

## 8. Provider Selection

```mermaid
flowchart TD
    A[Requested provider] --> B{Configured?}
    B -- yes --> C[Use requested provider settings]
    B -- no --> D{Demo fallback allowed?}
    D -- yes --> E[Use demo provider]
    D -- no --> F[Raise LLMClientError]
```

Provider availability comes from environment variables:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

Demo provider does not need secrets.

## 9. Configuration

Environment is loaded from `.env`.

Important settings:

```text
APP_NAME=Listing Autopilot
APP_VERSION=0.1.0
APP_ENV=local
OUTPUT_DIR=outputs
MAX_UPLOAD_MB=10
DEFAULT_CUSTOMER_ID=demo-customer
DEFAULT_USER_ID=demo-user
ALLOWED_ORIGINS=*
DATABASE_URL=postgresql+psycopg2://listingautopilot:listingautopilot@localhost:5432/listingautopilot
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_IMAGE_MODEL=gpt-image-1
OPENAI_IMAGE_SIZE=1024x1024
OPENAI_IMAGE_QUALITY=medium
OPENAI_IMAGE_OUTPUT_FORMAT=png
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview
GEMINI_IMAGE_ASPECT_RATIO=1:1
GEMINI_IMAGE_SIZE=2K
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

`listingautopilot.config.settings` is the main application settings object.

`listingautopilot.core.config.settings` is a facade with uppercase attributes to match the service app style.

## 10. API App Assembly

`src/listingautopilot/main.py`:

- loads `.env`
- creates `FastAPI`
- registers Prometheus metrics at `/metrics`
- registers CORS
- includes health, provider, generation, and project routers
- adds bearer auth scheme to OpenAPI

Root `main.py` mirrors the same app assembly for local `uvicorn main:app` compatibility.

## 11. Tests

Current test coverage:

- `tests/unit/apis/test_generation_pipeline.py`: core pipeline without DB.
- `tests/unit/apis/test_main_app.py`: FastAPI routes, metrics, and OpenAPI bearer auth.
- `tests/unit/db/pgv/crud/test_project_crud.py`: project CRUD and saved generation rows.
- `tests/unit/llm/test_llm_providers.py`: provider config, fallback, and demo structured output.

Run:

```bash
scripts/test.sh
ruff check .
```

## 12. Deployment Notes

Local dashboard:

```bash
scripts/run_dashboard.sh
```

Local API:

```bash
scripts/run_api.sh
```

Local Postgres:

```bash
docker compose up -d postgres
alembic upgrade head
```

Streamlit Community Cloud:

- app entrypoint: `listingautopilot/dashboard/streamlit_app.py`
- secrets: provider keys and optional `DATABASE_URL`
- demo mode works without secrets
