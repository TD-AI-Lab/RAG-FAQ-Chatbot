# Backend RAG FAQ (Workways)

Backend Python modulaire pour ingérer une FAQ WordPress, indexer en embeddings, puis répondre via RAG (`top-3`) avec GPT.

## Stack

- Python 3.11+
- FastAPI
- OpenAI: `text-embedding-3-small`, `gpt-4o-mini`
- FAISS (cosine via normalisation + Inner Product)
- httpx + BeautifulSoup
- pytest

## Arborescence

```text
backend/
  src/
    app.py
    api/
    core/
    domain/
    ingestion/
    indexing/
    rag/
    utils/
  data/
    raw/
    processed/
  storage/
    index/
    cache/
  tests/
```

## Setup

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -e .[test]
copy .env.example .env
```

## Variables d'environnement

Voir `.env.example`:

- `OPENAI_API_KEY`
- `OPENAI_EMBEDDING_MODEL`
- `OPENAI_CHAT_MODEL`
- `FAQ_SOURCE_URL`
- `INDEX_PATH`
- `PROCESSED_FAQ_PATH`
- `TOP_K`
- `MIN_SCORE_THRESHOLD`
- `ENABLE_DEBUG`
- `REQUEST_TIMEOUT_SECONDS`
- `RATE_LIMIT_PER_MINUTE` (0 = desactive)
- `RATE_LIMIT_MAX_CLIENTS`
- `CORS_ALLOW_ORIGINS` (liste CSV)
- `CORS_ALLOW_CREDENTIALS`

## Ingestion FAQ

```bash
python -m src.ingestion.scrape_faq
```

Sorties:

- `data/raw/*.html`
- `data/processed/faqs.json`

Notes:

- Gère retries HTTP
- Tente JSON-LD FAQPage + structures HTML FAQ
- Crawl limité à des URLs support/help/faq même domaine
- Si 0 item: n'écrase pas le fichier précédent

## Construction d'index

```bash
python -m src.indexing.build_index
```

Sorties:

- `storage/index/faiss.index`
- `storage/index/meta.json`
- `storage/index/manifest.json`

## Lancer l'API

```bash
uvicorn src.app:app --reload --port 8000
```

## Endpoints

### `GET /health`

Réponse:

```json
{"status":"ok|degraded","index_ready":true,"llm_ready":true}
```

### `POST /chat`

Request:

```json
{"question":"Comment reinitialiser mon mot de passe ?"}
```

Response:

```json
{
  "answer": "...",
  "sources": [
    {"id":"...","question":"...","url":"...","score":0.83,"rank":1}
  ],
  "debug": {}
}
```

## Curl

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"question":"Comment contacter le support ?"}'
```

## Tests

```bash
pytest
```

## Sécurité / robustesse

- Ne log pas la clé API
- Validation des entrées (trim, min/max, emoji)
- Seuil de similarité pour éviter hors-sujet
- Fallback anti-hallucination: `Je ne sais pas.`
- Option de rate limit en mémoire
- Erreurs explicites 400/502/503
