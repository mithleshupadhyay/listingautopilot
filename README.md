# Listing Autopilot Service

Pixii-style editable photo upgrader and Amazon listing creative pipeline.

Upload a weak supplier product photo and get:

- upgraded Amazon-ready product image
- Canva-style editable listing design preview
- editable layer JSON behind the preview
- listing score, title, bullets, purchase criteria, and creative direction
- Markdown/design exports
- optional saved project history with Postgres

## Structure

```text
.
├── alembic/
├── dashboard/
├── docs/
├── scripts/
├── src/listingautopilot/
├── tests/
├── main.py
├── pyproject.toml
└── docker-compose.yml
```

## Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
```

Live image editing:

- Select `demo` to use the local deterministic image cleaner.
- Select `openai` with `OPENAI_API_KEY` to use OpenAI image edits for the upgraded product image.
- Select `gemini` with `GEMINI_API_KEY` to use Gemini image editing for the upgraded product image.
- Text/design generation and image editing are both provider-aware; Anthropic is supported for text/design only and falls back to the local image cleaner.

Core dashboard without DB:

```bash
scripts/run_dashboard.sh
```

API:

```bash
scripts/run_api.sh
```

The API app is assembled in `src/listingautopilot/main.py`; root `main.py` imports it for deployment compatibility.

Postgres persistence:

```bash
docker compose up -d postgres
alembic upgrade head
```

## Verify

```bash
scripts/test.sh
ruff check .
```
