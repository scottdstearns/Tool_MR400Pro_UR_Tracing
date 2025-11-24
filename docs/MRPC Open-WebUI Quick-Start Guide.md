# Open-WebUI Quick-Start Guide

## Purpose
This guide shows R&D engineers how to log in, create Knowledge Bases (KBs),
upload documents, and query them through Open-WebUI.

---

## 1. Login
- URL: `http://<server-ip>:8080/`
- Use the credentials provided by an Admin (invite-only).
- ✅ Success: you see the Workspace dashboard.

---

## 2. Select a Model
- Default models available:
  - **azure-gpt-4o** (chat/completions)
  - **azure-gpt-5** (chat/completions, if enabled by admin)
- Choose the desired model in the top bar of the chat window.
- ✅ Success: model name shows in the chat input header.

---

## 3. Create a Knowledge Base
- Go to **Workspace → Knowledge**.
- Click **+ Create Knowledge**.
- Enter a name (e.g., `ProjectA-KB`), then **Save**.
- ✅ Success: new KB appears in the Knowledge list.

---

## 4. Upload Documents
- Open your KB and click **Upload**.
- Supported formats: `.txt`, `.pdf`, `.docx`, `.md`, `.csv` (small test file first).
- Files are chunked and embedded into Qdrant automatically.
- ✅ Success: file shows in the KB list; Admins can confirm in logs.

---

## 5. Ask Questions Using a KB
- Start a new **Chat**.
- In the right panel, select your KB under **Knowledge**.
- Type a natural-language question about the uploaded docs.
- ✅ Success: answer references your KB content.

---

## 6. File Limits & Practices
- Prefer text-heavy, searchable documents.
- PDFs with images/scans must have embedded text (no OCR in pipeline).
- Upload in small batches to simplify troubleshooting.

---

## 7. Getting Help
- **Login issues** → contact your Admin (invite-only system).
- **KB not searchable** → check with Admin that ingest reached Qdrant.
- **Model errors** → verify you selected `azure-gpt-4o` or `azure-gpt-5`.

---

## Success Cues
- You can log in and see the Workspace.
- Your KB exists and contains uploaded docs.
- Queries return grounded answers from your KB.
