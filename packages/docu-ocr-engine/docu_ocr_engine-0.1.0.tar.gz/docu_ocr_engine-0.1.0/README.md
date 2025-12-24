# docu-ocr-engine (Self-hosted OCR Engine)

A backend-agnostic, self-hosted OCR engine packaged in Python and shipped as a Docker container.
It exposes:
- **HTTP API** (FastAPI) for Laravel/Node/any backend
- **CLI** for batch/offline OCR
- **Pluggable OCR engines** (Tesseract by default) with an interface for future engines

> This repo is production-oriented but intentionally minimal so you can extend it.

## Features
- Document processing endpoint (`/v1/process`) accepting:
  - local file upload (multipart)
  - or remote URL fetch
- Status tracking (`/v1/jobs/{job_id}`) with in-memory store (swap to Redis/Postgres easily)
- Retry-friendly design: idempotency key support
- OCR engine abstraction (`BaseOcrEngine`)
- Output as structured JSON (text + basic metadata)
- Dockerized for easy self-hosting

## Quickstart (Docker)
```bash
docker build -t docu-ocr-engine:local -f docker/Dockerfile .
docker run --rm -p 8000:8000 docu-ocr-engine:local
```

Open:
- http://localhost:8000/health
- http://localhost:8000/docs

## Quickstart (Local dev)
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn docu_ocr.api.http:app --host 0.0.0.0 --port 8000 --reload
```

## CLI
```bash
python -m docu_ocr.cli.main process --file samples/sample.png --out /tmp/result.json
```

## API usage examples

### cURL (upload)
```bash
curl -X POST "http://localhost:8000/v1/process" \
  -H "X-Idempotency-Key: demo-123" \
  -F "file=@samples/sample.png" \
  -F "language=eng"
```

### cURL (status)
```bash
curl "http://localhost:8000/v1/jobs/<job_id>"
```

## Notes
- Default OCR engine is **Tesseract**. The Docker image includes `tesseract-ocr`.
- For PDFs, the service uses `pdftoppm` (poppler-utils) to render pages to images.

## Extending
- Add new engines in `docu_ocr/ocr/` and wire via `DOCU_OCR_ENGINE=<name>`
- Replace `InMemoryJobStore` with Redis/Postgres
- Add webhooks from `core/pipeline.py` after completion

## License
MIT
# ocr-medz
