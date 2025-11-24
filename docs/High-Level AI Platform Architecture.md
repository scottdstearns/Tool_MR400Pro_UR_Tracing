# MRPC — High-Level AI Platform Architecture

## 1. Overview
This document describes the high-level architecture for the MRPC AI Platform.  
It presents a layered view that separates the **Foundational RAG Platform** from the **Agentic Application Layer**, enabling a stable base for knowledge management and rapid delivery of specialized AI tools and agents.

**Layers**
- **Foundational RAG Platform** — Open-WebUI + LiteLLM (Azure) + Qdrant; provides “RAG as a Service” and an OpenAI-compatible API for apps.  
- **Agentic Application Layer** — coordinator and specialized tool agents that consume the platform to deliver end-user value (e.g., Requirements Analysis, Risk Management, V&V).

---

## 2. Foundational RAG Platform (summary)
**Components**
- **Open-WebUI** — chat UI, knowledge management, admin; exposes OpenAI-compatible API endpoints.  
- **LiteLLM (Proxy)** — routes chat/embedding requests to Azure OpenAI deployments; normalizes API/version differences.  
- **Qdrant Vector DB** — persistent vector store; multi-tenant collections (`open-webui_knowledge`, `open-webui_files`) for project isolation.

**Key behaviors**
- **Knowledge** (Workspace → Knowledge) writes embeddings to Qdrant.  
- **Documents** page is local index (non-Qdrant).  
- Open-WebUI runs invite-only auth by default (admin-managed users).

For component-level data flows and the canonical diagram, see **Foundational Architecture Overview for RAG Tools**.

---

## 3. Agentic Application Layer
The agentic layer turns the platform into end-user capabilities.

**Elements**
- **Coordinator App** — plans multi-step tasks, calls specialized agents, synthesizes results for the user.  
- **Specialized Tool Agents** — narrow-scope RAG apps (e.g., Requirements Analysis, Risk Management, V&V) with curated KBs; invoked by coordinator or directly by apps.

**Typical flow**
1. Coordinator receives a high-level goal (e.g., “Review this document and identify key risks”).  
2. Chooses tools/agents (Requirements Analysis + Risk Agent), invokes them in sequence with appropriate KBs.  
3. Aggregates responses and returns a structured result to the user.

---

## 4. Integration Points (for App Teams)
- **Open-WebUI API (OpenAI-compatible)**  
  - `POST /v1/chat/completions` — chat/completions via LiteLLM → Azure GPT (e.g., `gpt-4o`).  
  - Knowledge context is selected via UI (KB binding) or app flow that targets the right KB(s).  
- **LiteLLM Proxy**  
  - Internal service (`http://litellm:4000`) translating to Azure OpenAI deployments (chat + embeddings).  
- **Qdrant**  
  - Internal service (`http://qdrant:6333`) used by the platform for vector storage/retrieval; external apps shouldn’t talk to Qdrant directly unless building custom pipelines.

**Outcome**: application teams consume a **single stable API surface** while the platform hides vector DB and vendor nuances.

---

## 5. Non-Functional Concerns

### 5.1 Security & Auth
- **Invite-only** account creation (admin-managed); leverage RBAC and group controls within Open-WebUI for workspace access.  
- For enterprise SSO/RBAC, plan integration with LDAP/AD or IdP as the platform moves to managed environments.

### 5.2 Networking & Proxy
- All containers run with corporate **HTTP(S)\_PROXY** and **NO\_PROXY** for local services; this is required for dependency resolution and Azure connectivity.

### 5.3 Scaling & Deployment Path
- **Current**: Docker Compose on AWS RHEL (single-node, persistent volumes).  
- **When to move to AKS (Kubernetes)**: high availability, SSO, policy, multi-team scale.  
  - Required shifts: **SQLite → PostgreSQL** for backend DB; **Redis** for sessions; shared **WEBUI\_SECRET\_KEY** across pods.  
  - HTTPS via Ingress + Cert-Manager; follow enterprise guidance for certificate automation and ingress security.

---

## 6. Data Flows (Ingestion & Query)
- **Ingestion**: upload → chunk → embed (`text-embedding-3-large`) → store vectors in Qdrant collection.  
- **Query**: user prompt → embed query → retrieve top-K vectors → augment prompt → chat completion (`gpt-4o`/`gpt-5`) → result to UI.  
(See Foundational Architecture diagram for the canonical sequence.)

---

## 7. Collections & Multitenancy
- Default multi-tenant approach:  
  - `open-webui_knowledge` — knowledge vectors  
  - `open-webui_files` — file-level vectors  
- Each project/KB is tenant-scoped via payload filters. Split into dedicated collections only when you need different embedding dims, index params, or strict lifecycle isolation.

---

## 8. Roadmap Linkage (Crawl → Walk → Run)
- **Crawl (✅ complete)** — platform deployed and verified.  
- **Walk** — deliver *Requirements Evaluation* app (Streamlit) that calls the Open-WebUI API and uses curated KBs.  
- **Run** — coordinator-driven multi-agent orchestration and additional tools (risk analysis, traceability).  
(See *Implementation Plan* for execution by phase:contentReference[oaicite:19]{index=19}.)

---

## 9. References
- **Foundational Architecture Overview for RAG Tools** — component-level diagram & flows.  
- **Open-WebUI App Deployment Report** — enterprise deployment guidance (HTTPS, AKS, Postgres/Redis, SSO/RBAC).  
- **MRPC AI Infrastructure Runbook** — operations, backups, smoke tests.  
- **MRPC Open-WebUI Quick-Start Guide** — user onboarding.  
