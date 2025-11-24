
# Open-WebUI + LiteLLM (Azure) + Qdrant — Runbook (R\&D)

## Purpose and Scope

This runbook provides step-by-step instructions for deploying, operating, and maintaining
an Open-WebUI + LiteLLM (Azure) + Qdrant stack in the R&D engineering environment.

The document is intended for engineers and administrators who need to:

- Deploy and configure the stack using Docker Compose and environment variables.
- Manage authentication in invite-only mode (with temporary signup when required).
- Operate and maintain the vector database (Qdrant) and application database (Open-WebUI).
- Perform common operational tasks: backups, restores, upgrades, user management,
  key rotation, and vector store resets.
- Troubleshoot common failure modes (proxy issues, mismatched versions, FAISS vs Qdrant).
- Verify end-to-end functionality through smoke tests.

The scope is limited to **infrastructure deployment and operations**.  You will need familiarity with the Linux command line interface. Contact a local administrator (MRPC Orlando) or Philips Group IT-GIS-Cloud Orchestration for access to the AWS EC2 server private key pair (.pem) and root password. Reference  the following: 
- Instance Name: EC2USE1LM0015.AWSUSE1.CLOUD.PHILIPS.COM
- IP Address: 161.88.75.204
  

Application-level usage for end-users is covered separately in the **User Quick-Start Guide**.


**Stack (pinned now):**

* Open-WebUI: `ghcr.io/open-webui/open-webui:v0.6.30`
* Qdrant: `qdrant/qdrant:v1.15.1`
* LiteLLM proxy: `ghcr.io/berriai/litellm:main-stable`
* Embeddings: Azure `text-embedding-3-large` via LiteLLM (3072-dim)

**Key Behaviors**

* **Knowledge** (Workspace → Knowledge) writes to **Qdrant**
* **Documents** page is a local index (don’t expect Qdrant writes from there)
* Qdrant collections (multitenant on): `open-webui_knowledge`, `open-webui_files`

---

## 0) One-time: Files & Paths

**Compose dir:** `/data/rag-project`
**Qdrant data (bind mount):** `/data/rag-project/qdrant-data`
**Open-WebUI DB (named volume):** `rag-project_open-webui-data`

---

## 1) Deploy / Recreate

> Make sure `.env` contains your real Azure key:
> `AZURE_OPENAI_API_KEY=...`

```bash
cd /data/rag-project

# Validate compose and env substitution
docker compose config >/dev/null && echo "Compose YAML OK"

# Recreate whole stack (safe)
docker compose up -d --force-recreate

# Check containers
docker compose ps
```

**Success criteria**

* `litellm-proxy`, `qdrant-db`, `open-webui` are **Up**
* No crash loops in `docker logs open-webui`

---

## 2) First Login (Invite-only, temp signup)

> We run **invite-only** by default. For first admin, temporarily enable signup.

**Edit `docker-compose.yml` → `open-webui.environment`:**

```
ENABLE_SIGNUP: "true"
WEBUI_AUTH: "True"
ENABLE_ADMIN: "true"
```

```bash
docker compose up -d --force-recreate open-webui
```

Open **`http://<server-ip>:8080/auth`** → **Create Admin Account**.

Then revert to invite-only:

```bash
# Edit compose: ENABLE_SIGNUP: "false"
docker compose up -d open-webui
```

**Success criteria**

* You can log in as Admin
* Later users cannot self-signup (you add them under **Admin → Users**)

---

## 3) LiteLLM ↔ Azure Sanity

```bash
# From UI container: chat completion through LiteLLM
docker exec -it open-webui sh -lc '
cat <<JSON | curl -s http://litellm:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-1234" -H "Content-Type: application/json" \
  -d @- | jq .choices[0].message.content
{
  "model": "azure-gpt-4o",
  "messages": [{"role":"user","content":"say hello"}]
}
JSON'
```

**Success criteria**

* JSON with assistant “hello” content

---

## 4) Qdrant ↔ Open-WebUI (multitenant ON)

We keep multitenancy **enabled** (recommended at your scale).

**Ensure these envs are present in compose (already in your file):**

```
VECTOR_DB: qdrant
RAG_VECTOR_STORE: qdrant
RAG_VECTOR_DB: qdrant
QDRANT_URI: http://qdrant:6333
QDRANT_URL: http://qdrant:6333
QDRANT_HOST: qdrant
QDRANT_PORT: "6333"
WEBUI_EXTRA_PIP_PACKAGES: "qdrant-client>=1.8,<2.0"
ENABLE_QDRANT_MULTITENANCY_MODE: "true"
```

```bash
docker compose up -d --force-recreate open-webui
```

**Success criteria**

* `docker logs open-webui` shows **VECTOR\_DB: qdrant** on boot
* `qdrant_client` is importable:

  ```bash
  docker exec -it open-webui sh -lc 'python - << "PY"
  ```

import importlib, pkgutil;print("qdrant\_client", "OK" if pkgutil.find\_loader("qdrant\_client") else "MISSING")
PY'

````
→ prints `qdrant_client OK`

---

## 5) Knowledge Ingest (writes to Qdrant)

**UI path:** Workspace → **Knowledge** → **+ Create Knowledge** → **Upload** a small `.txt`  
(Do **not** use “Documents” for Qdrant testing.)

**Observe ingest logs**
```bash
docker logs -f open-webui | egrep -i "qdrant|embedding|error|traceback"
````

**List collections**

```bash
docker exec -it open-webui sh -lc 'curl -s http://qdrant:6333/collections | jq .'
```

**Success criteria**

* Ingest log shows `HTTP Request: PUT .../collections/open-webui_knowledge` and upserts
* Collections include:

  * `open-webui_knowledge`
  * `open-webui_files`
    (plus any earlier `owui_smoke` you created)

> ⚠ Seeing **one** FAISS warning at **startup** is harmless. There should be **no FAISS** mention during the Knowledge ingest step.

---

## 6) Proxy / Network

### 6.1 Keep container egress via corp proxy (compose envs)

Already set in your compose (keep both UPPER & lower):

```
HTTP_PROXY:  http://fprxy1-ra2pr.p06.awsuse1.cloud.philips.com:8082
HTTPS_PROXY: http://fprxy1-ra2pr.p06.awsuse1.cloud.philips.com:8082
NO_PROXY: "localhost,127.0.0.1,::1,open-webui,litellm,qdrant"
http_proxy:  http://fprxy1-ra2pr.p06.awsuse1.cloud.philips.com:8082
https_proxy: http://fprxy1-ra2pr.p06.awsuse1.cloud.philips.com:8082
no_proxy: "localhost,127.0.0.1,::1,open-webui,litellm,qdrant"
```

**Success criteria**

* `pip` installs inside the UI container succeed (you already installed `qdrant-client`)
* LiteLLM outbound to Azure works

### 6.2 SSH tunnel (optional, clean remote access)

From your laptop:

```bash
ssh -N -L 8080:localhost:8080 ec2-user@<server-ip>
```

Open **[http://localhost:8080/](http://localhost:8080/)** in your browser.

**Success criteria**

* UI loads via local `localhost:8080`

### 6.3 API via proxy (example)

From within the UI container (respects env proxy):

```bash
docker exec -it open-webui sh -lc 'curl -s http://litellm:4000/v1/models | jq .'
```

---

## 7) Backup / Restore

### 7.1 Qdrant data (bind mount)

**Backup**

```bash
# Cold backup recommended (stop qdrant to flush)
docker stop qdrant-db

tar -C /data/rag-project/qdrant-data -czf /data/rag-project/qdrant-backup_$(date +%F_%H%M).tgz .

docker start qdrant-db
ls -lh /data/rag-project/qdrant-backup_*.tgz
```

**Restore**

```bash
docker stop qdrant-db
rm -rf /data/rag-project/qdrant-data/*
tar -C /data/rag-project/qdrant-data -xzf /path/to/qdrant-backup_xxx.tgz
docker start qdrant-db
```

**Success criteria**

* `docker logs qdrant-db` shows normal startup
* Collections list returns (same as before)

### 7.2 Open-WebUI DB (named volume)

**Backup**

```bash
docker run --rm -v rag-project_open-webui-data:/data -v "$PWD:/backup" alpine \
  sh -lc 'tar -C /data -czf /backup/openwebui-db-backup_$(date +%F_%H%M).tgz . && ls -lh /backup/*.tgz'
```

**Restore**

```bash
docker compose stop open-webui
docker volume rm rag-project_open-webui-data
docker run --rm -v rag-project_open-webui-data:/data -v /path/to/backupdir:/backup alpine \
  sh -lc 'rm -rf /data/* && tar -C /data -xzf /backup/openwebui-db-backup_xxx.tgz'
docker compose up -d open-webui
```

**Success criteria**

* UI loads; you can log in
* Knowledge list appears

---

## 8) Operations SOPs

### 8.1 Add a user (invite-only)

* **Admin → Users → + Add**
* Set role (User / Admin)

**Success criteria**: user shows in list with correct role

### 8.2 Rotate API Key (per user)

* **Admin → Users → (your user) → Settings → Account → API keys → regenerate**

**Success criteria**: new key works for API calls; old key rejected

### 8.3 Reset vector storage / Reindex

* **Admin → Documents → “Reset Vector Storage” → Confirm** (clears vector index mappings; does **not** delete Qdrant collections)
* Re-upload to rebuild

**Success criteria**: fresh ingest logs & Qdrant upserts

### 8.4 Smoke tests (end-to-end)

**Chat path**

```bash
docker exec -it open-webui sh -lc '
cat <<JSON | curl -s http://litellm:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-1234" -H "Content-Type: application/json" \
  -d @- | jq .choices[0].message.content
{
  "model": "azure-gpt-4o",
  "messages": [{"role":"user","content":"status check"}]
}
JSON'
```

**Embeddings path**

```bash
docker exec -it open-webui sh -lc '
curl -s http://litellm:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" -H "Content-Type: application/json" \
  -d "{\"input\":[\"hello\"],\"model\":\"azure-embedding-large\"}" | jq .data[0].embedding | head -n1'
```

**Qdrant collections**

```bash
docker exec -it open-webui sh -lc 'curl -s http://qdrant:6333/collections | jq .'
```

**Success criteria**

* Chat responds; embeddings array arrives; Qdrant shows collections

---

## 9) Troubleshooting (fast cues)

* **FAISS messages during ingest**
  Cause: uploading via **Documents** page or RAG still bound to local index.
  Fix: use **Workspace → Knowledge**; ensure envs set; `ENABLE_QDRANT_MULTITENANCY_MODE=true`.

* **No collections appear after Knowledge upload**
  Check:

  ```bash
  docker exec -it open-webui sh -lc 'python - << "PY"
  ```

import importlib, pkgutil;print("qdrant\_client", "OK" if pkgutil.find\_loader("qdrant\_client") else "MISSING")
PY'

```
→ If `MISSING`, ensure `WEBUI_EXTRA_PIP_PACKAGES` is present; restart UI.

- **Qdrant client/server mismatch**  
Align client ≈ server ±1 minor. You’re on **client 1.15.x** & **server v1.15.1** ✔️.

- **Auth lockout with empty DB**  
Enable temporarily:
```

ENABLE\_SIGNUP: "true"
WEBUI\_AUTH: "True"
ENABLE\_ADMIN: "true"

````
Recreate UI, sign up first admin, then set `ENABLE_SIGNUP: "false"`.

- **Proxy errors / pip hangs**  
Confirm in-container:
```bash
docker exec -it open-webui sh -lc 'env | grep -i proxy'
````

Keep both UPPER/lower case and a clean `NO_PROXY` for `open-webui, litellm, qdrant, localhost, 127.0.0.1`.

---

## 10) Upgrades / Maintenance

**Safe upgrade order**

1. `docker compose pull qdrant open-webui litellm`
2. **Backups** (Qdrant + Open-WebUI DB)
3. `docker compose up -d qdrant`
4. `docker compose up -d litellm`
5. `docker compose up -d open-webui`
6. Re-run smoke tests

**Success criteria**

* No migration errors in `open-webui` logs
* Knowledge ingest still creates/upserts points
* Chat/embeddings work via LiteLLM

---

## 11) Steelman: Multitenant vs One-collection-per-KB

**Multitenant (what you have; recommended)**

* ✅ Fewer collections; shared HNSW graph = good performance as you scale
* ✅ Simpler ops (backups, compaction)
* ⚠ Must keep **same embedding dim** across KBs (you’re 3072d now)
* Use when: uniform model, many KBs, want simple ops and good recall/latency

**One collection per KB**

* ✅ Independent lifecycle, index params, and even different dimensions (if routing accordingly)
* ⚠ More operational overhead; fragmentation can hurt performance
* Use when: different embedding models per KB, strict isolation, or bespoke index configs


