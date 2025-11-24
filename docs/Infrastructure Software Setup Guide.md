# Infrastructure Software Setup Guide

## Purpose
This guide provides complete instructions for deploying the MRPC AI Platform
infrastructure using Docker and Docker Compose. It covers environment
preparation, configuration of LiteLLM, Qdrant, and Open-WebUI, and verification
of a working installation.

This guide is for engineers responsible for system setup.  
For **operations and troubleshooting**, see the *Runbook*.  
For **end-user onboarding**, see the *Quick-Start Guide*.

---

## 1. Prerequisites

### Host
- Linux server (AWS RHEL 8/9 or equivalent).
- Recommended: `/data` volume for persistent project files.

### Installed Software
- Docker
- Docker Compose
- Git
- `jq` (for JSON output parsing).

### Network
- Outbound internet access through corporate proxy.
- Open ports:
  - `8080` → Open-WebUI
  - `4000` → LiteLLM
  - `6333/6334` → Qdrant

---

## 2. Directory Structure

Create a dedicated project directory:

```bash
mkdir -p /data/rag-project
cd /data/rag-project
```

Subdirectories and files:
- qdrant-data/ → persistent Qdrant storage.

- litellm-config.yaml → LiteLLM configuration file.

- docker-compose.yml → service definitions.

## 3. Environment Variables

Set the following in a .env file or export them before starting:

```bash
export AZURE_OPENAI_API_KEY=<your-azure-key>
export HTTP_PROXY=http://fprxy1-ra2pr.p06.awsuse1.cloud.philips.com:8082
export HTTPS_PROXY=http://fprxy1-ra2pr.p06.awsuse1.cloud.philips.com:8082
export NO_PROXY=localhost,127.0.0.1,::1,open-webui,litellm,qdrant
```

## 4. LiteLLM Configuration

Create the file /data/rag-project/litellm-config.yaml:

```yaml
model_list:
  - model_name: azure-embedding-large
    litellm_params:
      model: azure/text-embedding-3-large
      api_base: "https://<your-endpoint>.openai.azure.com/"
      api_version: "2024-02-01"
      api_key: os.environ/AZURE_OPENAI_API_KEY
      api_type: azure
      azure_deployment: "text-embedding-3-large"

  - model_name: azure-gpt-4o
    litellm_params:
      model: azure/gpt-4o
      api_base: "https://<your-endpoint>.openai.azure.com/"
      api_version: "2024-12-01-preview"
      api_key: os.environ/AZURE_OPENAI_API_KEY
      api_type: azure
      azure_deployment: "gpt-4o"
```
⚠️ Replace <your-endpoint> with your Azure OpenAI endpoint.
Do not hardcode API keys; always use environment variables.

## 5. Docker Compose Configuration

Create the file /data/rag-project/docker-compose.yml:

```yaml
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    container_name: litellm-proxy
    environment:
      AZURE_OPENAI_API_KEY: ${AZURE_OPENAI_API_KEY}
      HTTP_PROXY: ${HTTP_PROXY}
      HTTPS_PROXY: ${HTTPS_PROXY}
      NO_PROXY: ${NO_PROXY}
    ports:
      - "4000:4000"
    volumes:
      - ./litellm-config.yaml:/app/config.yaml:ro
    command: ["--config", "/app/config.yaml"]
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:v1.15.1
    container_name: qdrant-db
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - /data/rag-project/qdrant-data:/qdrant/storage
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:v0.6.30
    container_name: open-webui
    ports:
      - "8080:8080"
    environment:
      OPENAI_API_BASE_URL: http://litellm:4000
      OPENAI_API_KEY: sk-1234
      RAG_EMBEDDING_ENGINE: openai
      RAG_EMBEDDING_MODEL: azure-embedding-large
      VECTOR_DB: qdrant
      QDRANT_URL: http://qdrant:6333
      ENABLE_ADMIN: "true"
      WEBUI_AUTH: "true"
      ENABLE_SIGNUP: "false"
      WEBUI_EXTRA_PIP_PACKAGES: "qdrant-client>=1.8,<2.0"
      LOG_LEVEL: DEBUG
    volumes:
      - open-webui-data:/app/backend/data
    depends_on:
      - litellm
      - qdrant
    restart: unless-stopped

volumes:
  open-webui-data: {}
```
Key notes:

- Versions are pinned: ```qdrant:v1.15.1```, `open-webui:v0.6.30`.

- Proxy variables defined for all services.

- `WEBUI_AUTH` and `ENABLE_SIGNUP` ensure secure, invite-only login.

- Extra pip package ensures Qdrant client availability.

## 6. Deployment

Start the Services: 

```bash
docker compose up -d
```

Check status:

```bash
docker compose ps
```

## 7. Verification
### 7.1 Logs

```bash
Inspect logs for errors:
docker logs --tail=50 open-webui
docker logs --tail=50 litellm-proxy
docker logs --tail=50 qdrant-db
```

### 7.2 Open-WebUI Access

Open in browser:
```http://<server-ip>:8080/auth```

- First-time login → create an admin account.

- After setup, confirm signups are disabled.

### 7.3 Qdrant Health

Check Qdrant collections:

```bash
docker exec -it open-webui sh -lc 'curl -s http://qdrant:6333/collections | jq .'
```

Expected collections after first file upload:

- `open-webui_files`

- `open-webui_knowledge`

## 8. Handoff

**Runbook** → Operations, troubleshooting, backup/restore.

**Quick-Start Guide** → User onboarding and workspace usage.

## 9. Appendix A – Success Checklist

 - [ ] Project directories created.

 - [ ] LiteLLM config file created.

 - [ ] Docker Compose file with pinned versions.

 - [ ] Proxy variables configured.

 - [ ] Containers deployed and running.

 - [ ] Admin account created at `/auth`.

 - [ ] Qdrant collections verified.

## 10. Appendix B – Environment Variable Reference

| Variable                    | Purpose                                 |
| --------------------------- | --------------------------------------- |
| AZURE\_OPENAI\_API\_KEY     | Azure OpenAI API key                    |
| HTTP\_PROXY / HTTPS\_PROXY  | Corporate proxy routing                 |
| NO\_PROXY                   | Bypass list (internal containers)       |
| VECTOR\_DB                  | Vector DB provider (`qdrant`)           |
| QDRANT\_URL                 | URL for Qdrant service                  |
| ENABLE\_ADMIN               | Ensure admin creation enabled           |
| WEBUI\_AUTH                 | Enforce login system                    |
| ENABLE\_SIGNUP              | Controls whether open signup is allowed |
| WEBUI\_EXTRA\_PIP\_PACKAGES | Ensures qdrant-client is installed      |




