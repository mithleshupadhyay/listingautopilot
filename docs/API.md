# API Design

## 1. API Strategy

The MVP is Streamlit-first, so the dashboard can call Python service functions directly.

However, service boundaries should be designed as if they will later be exposed through FastAPI. This document defines the API contract for both:

- internal Python service calls
- future HTTP endpoints

## 2. Internal Service API

### `generate_listing_pack`

Primary orchestration function.

```python
from listingautopilot.apis.services.generation import generate_listing_pack

response = generate_listing_pack(request)
```

Input:

```python
GenerateRequest
```

Output:

```python
GenerateResponse
```

## 3. Future HTTP API

Base path:

```text
/api/v1
```

### Health Check

```http
GET /api/v1/health
```

Response:

```json
{
  "status": "ok",
  "service": "listing-autopilot",
  "version": "0.1.0"
}
```

### Generate Creative Pack

```http
POST /api/v1/generate
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
| `brand_tone` | string | no | Tone for copy |
| `amazon_listing_url` | string | no | Listing URL |
| `competitor_url` | string | no | Competitor listing URL |
| `use_demo_mode` | boolean | no | Force demo fallback |

Response:

```json
{
  "request_id": "req_20260503_001",
  "mode": "demo",
  "product": {
    "product_name": "Insulated Steel Bottle",
    "category": "Kitchen & Dining",
    "description": "A stainless steel insulated water bottle with screw cap.",
    "visible_features": ["matte finish", "metal body", "compact lid"],
    "likely_use_cases": ["gym", "office", "travel"],
    "target_customer": "busy professionals and fitness users",
    "visual_issues": ["background clutter", "low contrast"],
    "selling_angles": ["keeps drinks cold", "durable build", "travel friendly"]
  },
  "score": {
    "overall": 74,
    "image_quality": 68,
    "amazon_readiness": 72,
    "conversion_potential": 78,
    "benefit_clarity": 76,
    "proof_readiness": 70,
    "issues": [
      "Background does not look like Amazon main image style",
      "Key benefits are not visible in the image"
    ],
    "recommendations": [
      "Use a clean white main image with product centered",
      "Add infographic callouts for insulation and leak resistance"
    ]
  },
  "creative_pack": {
    "amazon_title": "Insulated Stainless Steel Water Bottle for Gym, Office and Travel",
    "bullets": [
      "Keeps drinks cold during long workdays and workouts",
      "Durable stainless steel body for everyday use",
      "Leak-resistant cap designed for bags and commutes",
      "Compact shape fits desks, cup holders and backpacks",
      "Clean matte finish for a premium everyday carry look"
    ],
    "benefits": ["Cold retention", "Leak resistance", "Travel-ready build"],
    "pain_points": ["warm drinks", "leaky bottles", "fragile plastic bottles"],
    "purchase_criteria": ["insulation", "leak resistance", "durability", "capacity", "easy cleaning"],
    "main_image_recommendation": "Show bottle centered on pure white background with balanced lighting.",
    "lifestyle_concept": "Bottle placed beside a laptop and gym bag to show office-to-workout use.",
    "infographic_headline": "Built for cold drinks on busy days",
    "infographic_callouts": ["Keeps cold", "Leak-resistant cap", "Stainless steel body"],
    "a_plus_sections": ["Problem/solution banner", "Material proof section", "Use-case grid"]
  },
  "images": {
    "original_url": "outputs/original.png",
    "upgraded_url": "outputs/upgraded.png",
    "lifestyle_url": null,
    "provider": "demo"
  },
  "editable_design": {
    "version": "1.0",
    "canvas": {
      "width": 2000,
      "height": 2000,
      "background": "#ffffff"
    },
    "layers": [
      {
        "id": "product-main",
        "type": "image",
        "name": "Product image",
        "x": 620,
        "y": 360,
        "width": 760,
        "height": 980,
        "image_ref": "outputs/upgraded.png",
        "style": {}
      },
      {
        "id": "headline",
        "type": "text",
        "name": "Headline",
        "x": 160,
        "y": 130,
        "width": 1680,
        "height": 160,
        "text": "Built for cold drinks on busy days",
        "style": {
          "font_size": 72,
          "font_weight": "700",
          "color": "#111827"
        }
      }
    ],
    "metadata": {
      "source": "listing-autopilot",
      "format": "editable-design-json"
    }
  },
  "exports": {
    "markdown": "# Listing Autopilot Report...",
    "design_json": "{...}"
  },
  "warnings": []
}
```

### Export Markdown

```http
POST /api/v1/export/markdown
Content-Type: application/json
```

Request:

```json
{
  "response": {}
}
```

Response:

```json
{
  "filename": "listing-autopilot-report.md",
  "content": "# Listing Autopilot Report..."
}
```

### Export Design JSON

```http
POST /api/v1/export/design-json
Content-Type: application/json
```

Request:

```json
{
  "design_spec": {}
}
```

Response:

```json
{
  "filename": "design-spec.json",
  "content": {}
}
```

## 4. Error Response Shape

Future HTTP error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Unsupported file type",
    "details": {
      "allowed_types": ["image/jpeg", "image/png", "image/webp"]
    }
  }
}
```

Common error codes:

| Code | Meaning |
| --- | --- |
| `VALIDATION_ERROR` | Bad request input |
| `FILE_TOO_LARGE` | Upload exceeds size limit |
| `UNSUPPORTED_FILE_TYPE` | Unsupported image type |
| `PROVIDER_NOT_CONFIGURED` | Live provider key missing |
| `PROVIDER_FAILED` | External provider failed |
| `EXPORT_FAILED` | Export generation failed |

## 5. Streamlit Integration Contract

The Streamlit dashboard should call:

```python
response = generate_listing_pack(
    GenerateRequest(
        image_filename=uploaded_file.name,
        image_content_type=uploaded_file.type,
        image_bytes=uploaded_file.getvalue(),
        product_name=product_name,
        brand_name=brand_name,
        category=category,
        target_customer=target_customer,
        amazon_listing_url=amazon_listing_url,
        competitor_url=competitor_url,
        use_demo_mode=use_demo_mode,
    )
)
```

Then render:

- `response.images`
- `response.score`
- `response.creative_pack`
- `response.editable_design`
- `response.exports`

## 6. Versioning

Initial version:

```text
0.1.0
```

Internal design JSON version:

```text
1.0
```

Future breaking API changes should increment API path:

```text
/api/v2
```
