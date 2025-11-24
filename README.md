# Tool_MR400Pro_UR_Tracing

Streamlit application for mapping **MR400 Pro legacy requirements** to **canonical user needs** using a **hybrid scoring pipeline** combining:
- **Semantic similarity** (Azure OpenAI `text-embedding-3-large` or SBERT fallback)
- **Lexical similarity** (TF-IDF with custom stop-phrases and n-grams)
- **Rule-based domain keyword matching** (ECG, SpO2, NIBP, alarms, MRI, etc.)

Tailored to the specs in `Prompt_UR_Tracing_Tool.md` and aligned with the **MRPC RAG platform architecture** (see `/docs`).

---

## Features

✅ **Hybrid Matching Algorithm**
- Azure OpenAI embeddings for semantic similarity
- TF-IDF with tri-grams for lexical matching
- Domain-specific keyword rules for boost scoring
- Configurable fusion logic (max of rule/embedding/TF-IDF scores)

✅ **Interactive Streamlit UI**
- Upload Excel workbooks with multiple sheets
- Map columns dynamically (IDs, text, optional extras)
- Adjust Top-K, n-gram range, stop-phrases, and rule toggles
- Filter results by score/method
- Validation warnings for orphan children and childless parents

✅ **Excel & CSV Export**
- Download trace matrix with all scores + metadata
- Proper sheet naming (`Trace_Matrix_Scores`)
- Include optional extra columns from source data

✅ **Docker Deployment**
- Ready for MRPC AI Platform (EC2 + Docker Compose)
- Integrated with LiteLLM proxy or direct Azure OpenAI
- Corporate proxy support (HTTP_PROXY, HTTPS_PROXY)

---

## Quick Start (Local)

```bash
# Clone and set up environment
git clone https://github.com/scottdstearns/Tool_MR400Pro_UR_Tracing.git
cd Tool_MR400Pro_UR_Tracing
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure Azure credentials
cp .env.example .env
# Edit .env with your Azure OpenAI keys

# Run app
streamlit run app.py
```

Open http://localhost:8501

---

## Sample Workbook

Generate a test workbook:

```bash
python samples/create_sample_workbook.py
```

Upload `samples/sample_requirements.xlsx` in the UI, then map:
- **Child sheet:** `Combined URs` → ID: `Requirement ID`, Text: `Description`
- **Parent sheet:** `Canonical_User_Needs` → ID: `new_doors_id`, Text: `User Requirement`, Title: `Title`

---

## Docker Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for full EC2/Docker instructions.

**Quick deploy:**

```bash
# On EC2 instance
cd /data
git clone https://github.com/<your-org>/Tool_MR400Pro_UR_Tracer.git
cd Tool_MR400Pro_UR_Tracer
cp .env.example .env
# Edit .env with Azure keys
docker compose up -d --build
```

Access at: http://161.88.75.204:8503

---

## Environment Variables (`.env`)

| Variable                             | Description                                      | Default                                   |
|--------------------------------------|--------------------------------------------------|-------------------------------------------|
| `AZURE_OPENAI_API_KEY`               | Azure OpenAI API key                             | *(required)*                              |
| `AZURE_OPENAI_ENDPOINT`              | Azure OpenAI endpoint URL                        | *(required)*                              |
| `AZURE_OPENAI_API_VERSION`           | API version                                      | `2024-02-01`                              |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`  | Deployment name for embeddings                   | `text-embedding-3-large`                  |
| `AZURE_OPENAI_EMBEDDING_MODEL`       | Model name override (optional)                   | `text-embedding-3-large`                  |
| `SBERT_MODEL_NAME`                   | SBERT fallback model                             | `sentence-transformers/all-MiniLM-L6-v2`  |
| `HTTP_PROXY`, `HTTPS_PROXY`          | Corporate proxy settings                         | *(optional)*                              |
| `NO_PROXY`                           | Proxy bypass list                                | `localhost,127.0.0.1,::1`                 |

---

## Project Layout

```
Tool_MR400Pro_UR_Tracing/
├── app.py                     # Streamlit UI
├── matching.py                # Hybrid matching engine
├── domain_lexicon.json        # Domain keyword groups
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker build
├── docker-compose.yml         # Docker Compose config
├── .env.example               # Sample environment config
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── DEPLOYMENT.md              # Deployment guide
├── Prompt_UR_Tracing_Tool.md  # Original requirements spec
├── docs/                      # MRPC platform architecture docs
└── samples/                   # Test data and scripts
    ├── create_sample_workbook.py
    └── sample_requirements.xlsx
```

---

## Algorithm Details

### Preprocessing
- Remove boilerplate phrases: `"the user shall be able to"`, `"the monitor shall"`, etc.
- Normalize whitespace and lemmatize tokens
- Keep domain-specific terms (SpO₂, mmHg, MAC)

### Rule-Based Matching
- Keyword groups: ALM (alarm), ECG, SpO2, NIBP/NBP, IBP, CO2, TEMP, AGENT, MRI, PWR, CONN, SRV
- If both child and parent match any group → `Score_Rule = 0.85`

### Semantic Similarity
- Azure OpenAI `text-embedding-3-large` (default, 3072-dim)
- Fallback: SBERT `all-MiniLM-L6-v2` (384-dim)
- Cosine similarity ∈ [0..1]

### TF-IDF Similarity
- N-gram range: 1-3 (configurable)
- Custom stop-phrases + English stop-words
- Cosine similarity ∈ [0..1]

### Fusion Logic
```python
if Score_Rule exists:
    Computed_Score = max(Score_Rule, Score_Embedding, Score_TFIDF)
    Method_Used = "Fusion"
else:
    Computed_Score = max(Score_Embedding, Score_TFIDF)
    Method_Used = "SBERT" if Score_Embedding >= Score_TFIDF else "TF-IDF"
```

---

## Validation

The tool validates:
- **Orphan children:** Children with all scores below threshold (configurable, default 0.5)
- **Childless parents:** Parents with no children mapped

Warnings are displayed in the UI but do **not** block downloads (per user requirement).

---

## Status

✅ **Completed:**
- [x] Repo + venv setup
- [x] Architecture docs integrated
- [x] Core matching engine (hybrid scoring, validation, extra columns)
- [x] Streamlit UI (filters, validation warnings, Excel/CSV export)
- [x] Dockerfile + docker-compose.yml
- [x] Deployment guide (DEPLOYMENT.md)
- [x] Sample workbook generator

🚀 **Ready for initial user testing and GitHub push.**

---

## References

- [Prompt_UR_Tracing_Tool.md](Prompt_UR_Tracing_Tool.md) — Original feature spec
- [DEPLOYMENT.md](DEPLOYMENT.md) — Deployment instructions
- [docs/](docs/) — MRPC AI Platform architecture (Foundational RAG, Runbook, etc.)

---

## License

Internal MRPC AI Tools project. All rights reserved.
