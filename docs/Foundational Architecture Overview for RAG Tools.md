# Foundational Architecture Overview for RAG Tools

## Purpose
This document provides a clear, high-level overview of the architecture for the
Retrieval-Augmented Generation (RAG) tools used in the MRPC AI Platform. It
outlines system components, their interactions, and key architectural decisions.

This serves as a reference for engineers, architects, and technical stakeholders.

---

## 1. Core Components

### 1.1 LiteLLM Proxy
- Role: Abstracts calls to Azure OpenAI models.
- Provides consistent API for embeddings and chat completions.
- Configured with:
  - `azure-embedding-large`
  - `azure-gpt-4o` (primary model)
  - Optional: `azure-gpt-5` for extended tasks.

### 1.2 Qdrant Vector Database
- Role: Persistent vector storage for embeddings.
- Stores and retrieves document vectors used in RAG pipelines.
- Supports multi-tenant collections:
  - `open-webui_files`
  - `open-webui_knowledge`

### 1.3 Open-WebUI
- Role: Web-based interface for users to interact with the system.
- Provides:
  - Chat interface
  - Knowledge base management
  - Admin controls (invite-only auth)

### 1.4 Infrastructure
- All services containerized with Docker Compose.
- Networked via an internal Docker bridge.
- Proxy-aware for corporate environment.

---

## 2. Data Flow Overview

### 2.1 Document Ingestion
1. User uploads file via Open-WebUI.
2. File is chunked, embedded via LiteLLM (Azure OpenAI).
3. Embeddings stored in Qdrant collections.

### 2.2 Query Flow
1. User query enters Open-WebUI.
2. Embedding generated via LiteLLM.
3. Qdrant retrieves nearest vectors (context).
4. OpenAI model produces augmented response.

---

## 3. Architectural Decisions

- **Vector DB**: Qdrant chosen for performance and open-source maturity.
- **Embedding Engine**: Azure-hosted `text-embedding-3-large` ensures scale and compliance.
- **UI**: Open-WebUI selected for flexibility, active development, and integration ease.
- **Isolation**: All services run in separate containers, simplifying deployment and upgrades.
- **Security**: Authentication enforced at Open-WebUI layer (invite-only).

---

## 4. Trade-offs and Considerations

- **Multi-tenant vs. single collection**:
  - Multi-tenant provides isolation and clarity but may increase management overhead.
  - Single collection reduces complexity but risks data mixing across knowledge bases.
- **Azure dependency**:
  - Provides enterprise-grade compliance.
  - Ties core functionality to Azure availability and quota management.
- **Proxy environment**:
  - Requires explicit proxy settings across containers.
  - Added complexity, but unavoidable in corporate networks.

---

## 5. Integration Points

- **Admin Panel** (Open-WebUI):
  - Controls model access.
  - Manages authentication and user roles.
- **API Endpoints**:
  - LiteLLM exposed on port 4000.
  - Qdrant exposed on ports 6333/6334.
  - Open-WebUI exposed on port 8080 (`/auth` for login).
- **Future Extensions**:
  - Pipeline integrations.
  - External connectors for ingestion (SharePoint, Slack, etc.).

---

## 6. Diagram (Conceptual)

![Software Architecture](./Software_Architecture_Concepts_01.png)


---

## 7. References

- *Infrastructure Software Setup Guide* – for installation details.  
- *Runbook* – for operational procedures.  
- *Quick-Start Guide* – for end-user onboarding.  



