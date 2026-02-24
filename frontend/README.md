# Frontend Streamlit - Workways RAG FAQ

Interface Streamlit connectee au backend FastAPI RAG.

## Features

- UI chat moderne (gradient, cartes, animations legeres)
- Verification backend `/health`
- Envoi question vers `/chat`
- Affichage de la reponse + top 3 FAQ sources (rank, score, lien)
- Historique de session + clear
- Gestion erreurs reseau/API (400/429/502/503)

## Setup

```bash
cd frontend
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Config

Variables dans `.env`:

- `BACKEND_BASE_URL=http://localhost:8000`
- `BACKEND_CHAT_PATH=/chat`
- `BACKEND_HEALTH_PATH=/health`
- `REQUEST_TIMEOUT_SECONDS=20`
- `MAX_QUESTION_LENGTH=1000`
- `SHOW_DEBUG=false`

## Run

```bash
streamlit run app.py
```

## Tests

```bash
pytest
```

## Notes integration

Le frontend suppose que le backend est deja indexe et lance.

Backend expected flow:
1. `python -m src.ingestion.scrape_faq`
2. `python -m src.indexing.build_index`
3. `uvicorn src.app:app --reload --port 8000`