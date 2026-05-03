# Listing Autopilot Requirements

## 1. Product Summary

Listing Autopilot is a Pixii-aligned Amazon listing creative engine.

It takes a product photo and optional listing context, then generates an Amazon-ready creative pack:

- upgraded main product image
- listing quality score
- product and customer analysis
- purchase criteria
- Amazon title and bullets
- lifestyle image concept
- infographic preview plan
- editable design JSON
- exportable creative report

The project should demonstrate the core Pixii-style idea: **zero-prompt listing creative generation from product inputs**.

## 2. Target Users

### Primary User

Amazon sellers, ecommerce founders, or agencies who have weak supplier photos and need better listing creatives quickly.

### Secondary User

An ecommerce creative operator who needs to convert one product input into repeatable listing design assets.

## 3. User Problem

Amazon sellers often start with low-quality supplier photos from Alibaba, WhatsApp, manufacturer catalogs, or marketplace screenshots. Hiring an agency is slow and expensive. Prompting generic image models is unreliable and does not produce structured, editable listing assets.

Listing Autopilot solves this by turning one product photo into a creative pack that is closer to an Amazon listing design workflow than a generic image generation workflow.

## 4. MVP Scope

### In Scope

- Streamlit dashboard as the first UI.
- Modular Python backend-style package.
- Product photo upload.
- Optional product name, brand name, category, Amazon listing URL, and competitor URL fields.
- AI or demo-mode product analysis.
- Image upgrade pipeline with pluggable providers.
- Listing score generation.
- Creative pack generation.
- Editable design JSON generation.
- Markdown export.
- Unit tests for scoring, design JSON, and creative planning.
- Streamlit Community Cloud compatibility.

### Out of Scope For MVP

- Full Canva-like editor.
- Real Amazon seller account integration.
- Shopify app installation.
- Production database.
- User authentication.
- Payment or subscription system.
- Large-scale competitor scraping.
- 1000-review ingestion.
- Exact Pixii product clone.

## 5. Functional Requirements

### FR-001: Upload Product Photo

The user can upload a product image.

Acceptance criteria:

- Supports `jpg`, `jpeg`, `png`, and `webp`.
- Rejects unsupported file types.
- Rejects files larger than configured max size.
- Shows preview before generation.
- Stores uploaded file only for the current local/session workflow unless storage is explicitly enabled.

### FR-002: Capture Optional Listing Context

The user can optionally provide:

- product name
- brand name
- product category
- Amazon listing URL
- competitor URL
- target customer
- brand tone

Acceptance criteria:

- App works even if only image is provided.
- Optional fields improve analysis but are not required.

### FR-003: Product Analysis

The system analyzes the uploaded image and optional context.

Output should include:

- product type
- visible attributes
- probable category
- target customer
- likely use cases
- visual quality issues
- selling angle hypotheses

Acceptance criteria:

- Uses LLM vision provider when configured.
- Uses deterministic demo fallback when provider is unavailable.
- Produces structured output validated by schemas.

### FR-004: Image Upgrade

The system upgrades the product photo for Amazon main-image usage.

Expected outputs:

- original image reference
- upgraded image reference
- provider metadata
- warning if fallback mode was used

MVP image upgrade may include one or more:

- background cleanup/removal
- studio-style background
- lighting/contrast improvement
- image upscaling
- generated replacement preview

Acceptance criteria:

- App never fails completely if image provider fails.
- Fallback mode returns a usable preview/explanation.
- Provider code is isolated behind an interface.

### FR-005: Listing Quality Score

The system generates a listing readiness score.

Score dimensions:

- image clarity
- background suitability
- product centering
- Amazon main-image readiness
- conversion potential
- benefit clarity
- proof/callout readiness

Acceptance criteria:

- Overall score from `0` to `100`.
- Includes issue list and recommendation list.
- Scoring is deterministic for tests.

### FR-006: Customer And Market Insight Summary

The system generates customer-facing insights.

Output should include:

- customer pain points
- purchase criteria
- objections
- visual proof required
- competitor comparison suggestions

Acceptance criteria:

- Minimum 3 pain points.
- Minimum 5 purchase criteria.
- Insights are written for ecommerce listing optimization, not generic marketing.

### FR-007: Creative Pack Generation

The system generates Amazon listing creative content.

Output should include:

- improved Amazon title
- 5 bullet points
- 3 to 5 product benefits
- infographic headline
- infographic callouts
- lifestyle image concept
- main image recommendation
- A+ content section ideas

Acceptance criteria:

- Copy is concise and marketplace-friendly.
- No unsupported medical/legal/compliance claims.
- Uses product analysis as source context.

### FR-008: Editable Design JSON

The system generates editable design layers.

Output should include:

- canvas dimensions
- product image layer
- text layers
- callout/badge layers
- colors
- layout positions
- export metadata

Acceptance criteria:

- JSON validates against design schema.
- Layer positions are within canvas bounds.
- At least one product image layer and three text/callout layers are present.

### FR-009: Infographic Preview

The dashboard should render a simple preview from the design JSON.

Acceptance criteria:

- Shows product image area.
- Shows headline and callouts.
- Makes it obvious that output is editable/layered.

### FR-010: Export

The user can export the result.

MVP exports:

- Markdown report
- design JSON

Future exports:

- ZIP containing images, report, and design JSON.
- PNG render of infographic preview.

Acceptance criteria:

- Export uses generated data, not static placeholder text.
- Download buttons are available in Streamlit UI.

## 6. Non-Functional Requirements

### NFR-001: Maintainability

- Code must be modular.
- Streamlit UI must be thin.
- Business logic must live in `listingautopilot/`.
- Provider-specific logic must be isolated.
- Schemas must define service boundaries.

### NFR-002: Reliability

- External API failures should degrade gracefully.
- Demo fallback should allow reviewers to use the app without keys.
- Errors should be user-readable in UI and developer-readable in logs.

### NFR-003: Security

- API keys must be read from environment variables or Streamlit secrets.
- API keys must never be exposed in UI.
- Uploaded image validation must check file type and size.
- Do not log binary image data or secrets.

### NFR-004: Performance

- Upload preview should appear immediately.
- Generation should show progress state.
- External calls should use timeouts.
- MVP should complete generation within 60 seconds in demo mode.

### NFR-005: Portability

- Must run locally with `pip install -r requirements.txt`.
- Must run on Streamlit Community Cloud.
- Docker support should be included for local API mode.

### NFR-006: Testability

- Unit tests for scoring, creative planning, and design JSON.
- Demo pipeline should be deterministic.
- Core services should be callable without Streamlit.

## 7. Success Criteria

The MVP is successful when a reviewer can:

1. Open the deployed Streamlit app.
2. Upload a product photo.
3. Click one generate button.
4. See upgraded/processed image output.
5. See an Amazon-focused creative pack.
6. See score, recommendations, and editable design JSON.
7. Download a report.

## 8. Future Scope

- Real Amazon listing scraper.
- Review analytics for 1000+ reviews.
- Competitor comparison.
- Batch SKU processing.
- Shopify or Amazon listing publishing.
- Full editable web canvas.
- Brand kit ingestion.
- Async job queue.
- Persistent project history.
- Multi-user accounts. 
