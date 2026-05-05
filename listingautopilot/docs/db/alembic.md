# Alembic

Alembic manages the optional Postgres persistence schema for saved Listing Autopilot projects.

Run all commands from the service folder:

```bash
cd listingautopilot
```

## 1. Start Local Postgres

```bash
docker compose up -d postgres
```

The default local database URL is documented in `.env.template`:

```text
DATABASE_URL=postgresql+psycopg2://listingautopilot:listingautopilot@localhost:5432/listingautopilot
```

## 2. Apply Migrations

```bash
alembic upgrade head
```

Current migrations:

```text
0001_initial_project_persistence.py
0002_assets_designs.py
63b9a5e4570d_noop_after_assets_designs.py
```

They create:

- `projects`
- `uploaded_assets`
- `generation_jobs`
- `provider_runs`
- `creative_packs`
- `design_specs`
- `image_assets`
- `editable_designs`
- `export_artifacts`

## 3. Check Migration State

```bash
alembic current
alembic history
```

## 4. Generate A New Migration

After changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe change"
```

Review the generated migration before applying it.

## 5. Generate SQL Without Applying

```bash
alembic upgrade head --sql
```

This is useful for review and CI checks.

## 6. Reset Local Dev Database

For local development only:

```bash
docker compose down -v
docker compose up -d postgres
alembic upgrade head
```

Do not use volume reset commands against a shared or production database.
