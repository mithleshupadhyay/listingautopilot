# API Design

## 1. Entry Points

The project has two runtime entry points:

- Streamlit dashboard: `dashboard/streamlit_app.py`
- FastAPI service: `src/listingautopilot/main.py`

Root `main.py` mirrors the package FastAPI app assembly so local `uvicorn main:app` also works from the service folder.

HTTP endpoints are versioned under `/v1` except health and metrics.

OpenAPI includes a bearer auth security scheme for the future production path. The initial version does not enforce JWT authentication.

## 2. Health

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "listing-autopilot",
  "version": "0.1.0"
}
```

## 3. Providers

```http
GET /v1/providers
```

Response:

```json
[
  {
    "provider_type": "demo",
    "label": "Demo fallback",
    "model": "demo-listing-autopilot",
    "configured": true,
    "available": true,
    "env_keys": []
  },
  {
    "provider_type": "openai",
    "label": "OpenAI",
    "model": "gpt-4o-mini",
    "configured": false,
    "available": false,
    "env_keys": ["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"]
  }
]
```

Notes:

- Demo is always configured and available.
- Live providers become available when their required API key is present.
- The response includes expected env keys so setup is clear.

## 4. Generate Creative Pack

```http
POST /v1/generate
Content-Type: multipart/form-data
```

Form fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `image` | file | yes | Product image |
| `product_name` | string | no | Product name |
| `brand_name` | string | no | Brand name |
| `category` | string | no | Product category |
| `target_customer` | string | no | Intended buyer |
| `brand_tone` | string | no | Copy tone. Defaults to `clear, premium, Amazon-friendly` |
| `amazon_listing_url` | string | no | Existing listing URL |
| `competitor_url` | string | no | Competitor listing URL |
| `llm_provider` | string | no | `demo`, `openai`, `gemini`, or `anthropic` |
| `use_demo_mode` | boolean | no | Uses deterministic demo behavior for local review |
| `save_to_db` | boolean | no | Saves project when a DB session is available |

Validation:

- Empty image uploads return `400`.
- Images above `MAX_UPLOAD_MB` return `413`.
- If DB is unavailable, generation still works; `save_to_db` simply has no persistence effect through the optional DB dependency.

Response shape:

```json
{
  "request_id": "req_abc123",
  "mode": "demo",
  "project_id": "6a5e0b62-a4f3-4d3c-9d6b-f56f9c0fdd8c",
  "llm_provider": "demo",
  "llm_model": "demo-listing-autopilot",
  "image_provider": "demo",
  "product": {
    "product_name": "Steel Bottle",
    "category": "Kitchen",
    "description": "Steel Bottle prepared for an Amazon listing creative workflow.",
    "visible_features": ["clean silhouette"],
    "likely_use_cases": ["everyday use"],
    "target_customer": "office workers",
    "visual_issues": ["supplier-style image"],
    "selling_angles": ["durable everyday carry"]
  },
  "score": {
    "overall": 72,
    "image_quality": 60,
    "amazon_readiness": 70,
    "conversion_potential": 82,
    "benefit_clarity": 80,
    "proof_readiness": 76,
    "issues": [],
    "recommendations": []
  },
  "creative_pack": {
    "amazon_title": "Steel Bottle for Everyday Use",
    "bullets": [],
    "benefits": [],
    "pain_points": [],
    "purchase_criteria": [],
    "main_image_recommendation": "Use a centered product image on a clean white background.",
    "lifestyle_concept": "Show the product in a realistic use case.",
    "infographic_headline": "Why shoppers choose Steel Bottle",
    "infographic_callouts": [],
    "a_plus_sections": []
  },
  "images": {
    "original_url": "outputs/original-abc.jpg",
    "upgraded_url": "outputs/upgraded-amazon-openai-def.png",
    "design_preview_url": "outputs/editable-design-preview-abc.png",
    "lifestyle_url": null,
    "provider": "openai",
    "metadata": {
      "note": "OpenAI image edit produced a real AI-edited Amazon-ready product image."
    }
  },
  "editable_design": {
    "version": "1.0",
    "canvas": {
      "width": 2000,
      "height": 2000,
      "background": "#ffffff"
    },
    "layers": [],
    "metadata": {}
  },
  "exports": {
    "markdown": "# Listing Autopilot Report...",
    "design_json": "{...}"
  },
  "warnings": []
}
```

## 5. Recent Projects

```http
GET /v1/projects/recent?limit=5
```

Behavior:

- Returns recent saved projects for the configured demo customer.
- Returns `[]` when `DATABASE_URL` is not configured.

Response:

```json
[
  {
    "id": "6a5e0b62-a4f3-4d3c-9d6b-f56f9c0fdd8c",
    "name": "Steel Bottle",
    "brand_name": "Acme",
    "product_name": "Steel Bottle",
    "category": "Kitchen",
    "status": "completed",
    "score_payload": {
      "overall": 72
    },
    "created_at": "2026-05-04T10:00:00Z",
    "updated_at": "2026-05-04T10:00:10Z"
  }
]
```

## 6. Project Detail

```http
GET /v1/projects/{project_id}
```

Behavior:

- Returns `503` when `DATABASE_URL` is not configured.
- Returns `404` when the project does not exist for the configured customer.
- Returns full saved project payload when found.

Response:

```json
{
  "id": "6a5e0b62-a4f3-4d3c-9d6b-f56f9c0fdd8c",
  "name": "Steel Bottle",
  "brand_name": "Acme",
  "product_name": "Steel Bottle",
  "category": "Kitchen",
  "status": "completed",
  "request_payload": {},
  "response_payload": {},
  "score_payload": {
    "overall": 72
  },
  "customer_id": "demo-customer",
  "created_by": "demo-user",
  "created_at": "2026-05-04T10:00:00Z",
  "updated_at": "2026-05-04T10:00:10Z",
  "is_deleted": false
}
```

## 7. Project Assets

```http
GET /v1/projects/{project_id}/assets
```

Behavior:

- Returns `503` when `DATABASE_URL` is not configured.
- Returns `404` when the project does not exist for the configured customer.
- Returns saved image asset metadata for original upload, upgraded product image, and editable design preview.

Response:

```json
[
  {
    "id": "d4d12a8f-3e79-4a28-93a6-fc5a99d87f24",
    "project_id": "6a5e0b62-a4f3-4d3c-9d6b-f56f9c0fdd8c",
    "asset_type": "upgraded_product",
    "file_name": "upgraded-amazon-demo-def.png",
    "content_type": "image/png",
    "storage_path": "outputs/upgraded-amazon-demo-def.png",
    "public_url": "outputs/upgraded-amazon-demo-def.png",
    "width": 2000,
    "height": 2000,
    "file_size_bytes": 123456,
    "provider": "demo",
    "asset_metadata": {
      "purpose": "amazon-ready-upgraded-product-image"
    },
    "customer_id": "demo-customer",
    "created_at": "2026-05-04T10:00:10Z",
    "is_deleted": false
  }
]
```

## 8. Asset Detail

```http
GET /v1/assets/{asset_id}
```

Returns one image asset record. Returns `503` when persistence is disabled and `404` when the asset is not found.

## 9. Project Designs

```http
GET /v1/projects/{project_id}/designs
```

Behavior:

- Returns `503` when `DATABASE_URL` is not configured.
- Returns `404` when the project does not exist for the configured customer.
- Returns editable design records connected to a project.

Response:

```json
[
  {
    "id": "f4d12a8f-3e79-4a28-93a6-fc5a99d87f24",
    "project_id": "6a5e0b62-a4f3-4d3c-9d6b-f56f9c0fdd8c",
    "name": "Steel Bottle listing design",
    "design_type": "infographic",
    "version": "1.0",
    "canvas_width": 2000,
    "canvas_height": 2000,
    "design_payload": {
      "version": "1.0",
      "layers": []
    },
    "preview_asset_id": "d4d12a8f-3e79-4a28-93a6-fc5a99d87f24",
    "status": "rendered",
    "error_message": null,
    "customer_id": "demo-customer",
    "created_by": "demo-user",
    "created_at": "2026-05-04T10:00:10Z",
    "updated_at": "2026-05-04T10:00:10Z",
    "is_deleted": false
  }
]
```

## 10. Design Detail

```http
GET /v1/designs/{design_id}
```

Returns one editable design record with full layer JSON. Returns `503` when persistence is disabled and `404` when the design is not found.

## 11. Metrics

```http
GET /metrics
```

Prometheus scrape endpoint registered by `prometheus-fastapi-instrumentator`.

## 12. Internal Python API

Streamlit calls the service function directly:

```python
from listingautopilot.api.generation import generate_listing_pack
from listingautopilot.schemas.request import GenerateRequest

response = generate_listing_pack(
    request=GenerateRequest(
        image_filename="bottle.jpg",
        image_content_type="image/jpeg",
        image_bytes=b"...",
        llm_provider="demo",
    ),
    db=None,
)
```

Persistence path:

```python
response = generate_listing_pack(
    request=GenerateRequest(
        image_filename="bottle.jpg",
        image_content_type="image/jpeg",
        image_bytes=b"...",
        llm_provider="demo",
        save_to_db=True,
    ),
    db=session,
    user_context=user_context,
)
```

`db=None` runs the full core pipeline without persistence. Passing a SQLAlchemy session and `save_to_db=True` creates a saved project and related generation rows.
