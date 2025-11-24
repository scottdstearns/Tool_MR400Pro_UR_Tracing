# Deployment Guide — MR400 Pro UR Tracing

This guide covers deploying the **Tool_MR400Pro_UR_Tracing** on the MRPC AI Platform (AWS EC2, Docker, LiteLLM proxy).

---

## Prerequisites

- **MRPC AI Platform** running (Open-WebUI + LiteLLM + Qdrant) per [Infrastructure Software Setup Guide](docs/Infrastructure%20Software%20Setup%20Guide.md)
- Docker & Docker Compose installed on target EC2 instance
- Access to Azure OpenAI embeddings endpoint (`text-embedding-3-large`)
- Corporate proxy settings (if applicable)

---

## Quick Start (Local Development)

```bash
# Clone repo
git clone https://github.com/scottdstearns/Tool_MR400Pro_UR_Tracing.git
cd Tool_MR400Pro_UR_Tracing

# Set up virtual environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with Azure keys and endpoints

# Run locally
streamlit run app.py
```

Open http://localhost:8501

---

## Docker Deployment (EC2)

### 1. Prepare Environment

SSH into the EC2 instance:

```bash
ssh -i /path/to/key.pem ec2-user@161.88.75.204
```

Clone the repo into `/data/`:

```bash
cd /data
git clone https://github.com/scottdstearns/Tool_MR400Pro_UR_Tracing.git
cd Tool_MR400Pro_UR_Tracing
```

### 2. Configure `.env`

```bash
cp .env.example .env
nano .env
```

Populate with your Azure OpenAI credentials:

```env
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Proxy (if required)
HTTP_PROXY=http://fprxy1-ra2pr.p06.awsuse1.cloud.philips.com:8082
HTTPS_PROXY=http://fprxy1-ra2pr.p06.awsuse1.cloud.philips.com:8082
NO_PROXY=localhost,127.0.0.1,::1,open-webui,litellm,qdrant
```

### 3. Build & Run

Ensure the `mrpc-ai-network` Docker network exists (created during platform setup):

```bash
docker network ls | grep mrpc-ai-network
```

If missing, create it:

```bash
docker network create mrpc-ai-network
```

Build and start the service:

```bash
docker compose up -d --build
```

Check logs:

```bash
docker logs -f mr400pro-tracer
```

### 4. Access the App

The app is exposed on **port 8503**:

```
http://161.88.75.204:8503
```

Or via SSH tunnel from your local machine:

```bash
ssh -N -L 8503:localhost:8503 ec2-user@161.88.75.204
```

Then open: http://localhost:8503

---

## Integration with LiteLLM Proxy (Optional)

If you want to use the existing LiteLLM proxy instead of direct Azure calls, update `.env`:

```env
OPENAI_BASE_URL=http://litellm:4000/v1
OPENAI_API_KEY=sk-1234
```

Then modify `app.py` to instantiate `EmbeddingProvider` with:

```python
emb_provider = EmbeddingProvider(
    azure_config=None,  # Disable direct Azure
    fallback_model_name=config.sbert_model_name,
    use_litellm_proxy=True,
    proxy_base_url=os.getenv("OPENAI_BASE_URL"),
    proxy_api_key=os.getenv("OPENAI_API_KEY"),
)
```

---

## Operational Notes

### Health Check

```bash
curl http://localhost:8503/_stcore/health
```

### Restart Service

```bash
docker compose restart mr400pro-tracer
```

### View Logs

```bash
docker logs --tail=100 -f mr400pro-tracer
```

### Update Deployment

```bash
cd /data/Tool_MR400Pro_UR_Tracing
git pull origin main
docker compose up -d --build
```

---

## Troubleshooting

### Import Errors (numpy conflict)

Ensure `requirements.txt` pins `numpy==1.26.4` (compatible with spacy/thinc).

### Azure Embedding Timeouts

- Check proxy settings in `.env`
- Verify Azure quota/rate limits

### SBERT Fallback Not Working

The SBERT model downloads on first run. Ensure the container has internet access.

---

## Security Considerations

- **Never commit `.env` to version control** (already in `.gitignore`)
- Rotate Azure API keys periodically
- Use invite-only access via Open-WebUI if exposing to team

---

## References

- [MRPC AI Infrastructure Runbook](docs/MRPC%20AI%20Infrastructure%20Runbook.md)
- [Foundational Architecture Overview](docs/Foundational%20Architecture%20Overview%20for%20RAG%20Tools.md)
- [High-Level AI Platform Architecture](docs/High-Level%20AI%20Platform%20Architecture.md)

---

**Questions?** Contact the MRPC AI Tools team.

