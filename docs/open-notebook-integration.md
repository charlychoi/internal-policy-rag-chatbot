# Open Notebook Integration Notes

## Runtime

- UI: `http://localhost:8502`
- REST API: `http://localhost:5055/api`
- Docker image: `lfnovo/open_notebook:v1-latest`
- DB: SurrealDB

## Core Flow

1. Create or select a notebook.
2. Upload files using `POST /api/sources` with `type=upload`, `embed=true`, `async_processing=true`.
3. Poll source status with `GET /api/sources/{source_id}/status`.
4. Ask questions using `POST /api/search/ask/simple` or search chunks with `POST /api/search`.

## Known PoC Limitation

Open Notebook's basic Search/Ask path may not strictly scope by `notebook_id`. For this PoC, run a single dataset or a separate Open Notebook instance. Before production, add notebook-scoped search, result filtering, or instance separation.
