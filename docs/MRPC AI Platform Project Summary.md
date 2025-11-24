# MRPC AI Platform Project Summary

## 1. Purpose
The MRPC AI Platform provides a **stable, multi-tenant RAG foundation** for building specialized AI tools and agentic applications.  
It accelerates engineering workflows by combining **Open-WebUI** for user interaction, **LiteLLM** for Azure model proxying, and **Qdrant** for vector storage.

---

## 2. Roadmap (Crawl → Walk → Run)
- **Crawl (✅ complete)** — platform deployed, end-to-end RAG flow proven.  
- **Walk** — one or more production-grade apps (Requirements Evaluation, Risk Analysis) consuming the platform.  
- **Run** — Coordinator + multi-agent orchestration; scale to multiple teams and enterprise AKS deployment with Postgres, Redis, and SSO/RBAC.

---


## 3. Current State (Crawl Phase ✅)
- **Platform deployed** on AWS EC2 (RHEL) with Docker Compose.  
- **Components**:
  - **Open-WebUI v0.6.30** — chat interface, knowledge/document management, admin controls.  
  - **LiteLLM (Proxy)** — OpenAI-compatible API proxy to Azure OpenAI (chat + embeddings).  
  - **Azure OpenAI** — GPT-4o / GPT-5 (chat), text-embedding-3-large (embeddings).  
  - **Qdrant v1.15.1** — persistent vector database with multi-tenant collections (`open-webui_files`, `open-webui_knowledge`).  
- **Security**: Invite-only account creation (admin-managed).  
- **Networking**: Configured for enterprise proxy and `NO_PROXY` for local service resolution.  
- **Verification complete**: Ingestion, embeddings, storage, retrieval, and chat augmentation flows validated end-to-end.

---

## 4. Next Phase (Walk)
- Deliver the first **Requirements Evaluation App**:  
  - Built in Streamlit.  
  - Calls Open-WebUI API (`/v1/chat/completions`).  
  - Uses curated project-specific KBs.  
- Formalize **backup, restore, and monitoring practices** from the Runbook.  
- Capture usage metrics and feedback to guide “Run” phase.

---

## 5. Strategic Value
- Provides **one stable OpenAI-compatible API surface** to app teams.  
- Hides complexity of embeddings, vector storage, and Azure integration.  
- Creates a **repeatable foundation** for multi-tenant AI apps with security, scale, and flexibility.  
- Positions MRPC for **enterprise adoption** by aligning with AKS, Postgres, Redis, and corporate auth in the Run phase.

---
