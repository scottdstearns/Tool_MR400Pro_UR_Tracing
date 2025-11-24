## ✅ Cursor Prompt: Build a Streamlit App for Legacy → Canonical Requirement Matching

**Goal:**  
Create a **Streamlit application** that matches **legacy user requirements** (children) to **canonical user needs** (parents) using a **hybrid algorithm** that combines:

*   **Semantic similarity** (default: Azure OpenAI `text-embedding-3-large`; fallback: SBERT `all-MiniLM-L6-v2`)
*   **Lexical similarity** (TF‑IDF with custom stop‑phrases and tri‑grams)
*   **Rule-based domain keyword matching**
*   **Fusion logic** for scoring and ranking (Top‑K = 3 per child)

***

### **Data Sources**

*   **Workbook:** `MR400Pro_Canonical_UserNeeds.xlsx`
*   **Children (legacy):** Sheet `Combined URs`
    *   `Requirement ID` → `Child_ID`
    *   `Description` → `Child_Text`
*   **Parents (canonical):** Sheet `Canonical_User_Needs`
    *   `new_doors_id` → `Parent_ID`
    *   `Title` → `Parent_Title` (fallback to `User Requirement`)
    *   `User Requirement` → `Parent_Text`

The user will be able to upload or drag and drop the input file. The ui will allow the user to identify which tab/sheet has the orphan/children (legacy) requirements and which has the candidate parent requirements. Once the source data sheets are identified, a preview is provided. The user will then be able to do column mapping - to identify the id's and requirement text columns for both the children and the candidate parent requirements. The user will be able to optionally include additional columns from the input document in the output document. The UI will allow user selectable controls - for example Top-N matches in the output. The tool will validate that every child requirement is traced to a candidate parent AND that every parent has one or more child requirements mapped to it...so, no orphans and no childless parents after the tracing is complete. 

**Edge Cases:**

*   Children with empty `Description` → output placeholder row.
*   Duplicate or blank IDs → preserve as-is.

***

### **UI Requirements**

*   **Sidebar Controls:**
    *   Upload Excel file
    *   Select sheets and columns (defaults pre-filled)
    *   Configure algorithm options:
        *   Embedding model:
            *   Default: **Azure OpenAI `text-embedding-3-large`** (expected best for this use case)
            *   Optional: SBERT fallback (`sentence-transformers/all-MiniLM-L6-v2`)
        *   TF‑IDF n-gram range (default: 1–3)
        *   Stop‑phrases (editable list)
        *   Top‑K (default: 3)
        *   Toggle Rules on/off
*   **Main Panel:**
    *   Display Top‑K matches per child in a table:
        *   Columns:  
            `Child_ID`, `Child_Text`, `Parent_ID`, `Parent_Title`,  
            `Score_Rule`, `Score_Embedding`, `Score_TFIDF`,  
            `Computed_Score`, `Method_Used`, `Matched_Groups`
    *   Download results as Excel (`Trace_Matrix_Scores_SBERT` sheet)
    *   Filter by score threshold or method type

***

### **Algorithm Details**

#### **Preprocessing**

*   Remove boilerplate phrases:  
    `"the user shall be able to"`, `"the user shall"`, `"shall be able"`, `"as a clinical user"`, `"the monitor shall"`
*   Normalize whitespace
*   Lemmatize tokens for TF‑IDF (spaCy or NLTK)
*   Keep domain tokens (SpO₂, mmHg, MAC)

#### **Rule-Based Matching**

*   Keyword groups (with acronyms explained):
    *   **ALM (alarm):** alarm, IEC 60601-1-8
    *   **ECG:** electrocardiogram, QRS, electrode, lead
    *   **SpO₂:** oxygen saturation, desaturation, perfusion
    *   **NIBP / NBP:** non-invasive blood pressure (both acronyms refer to same parameter), cuff
    *   **IBP:** invasive blood pressure, arterial
    *   **CO₂:** capnography, EtCO₂, FiCO₂, apnea, respiration
    *   **TEMP:** temperature, Celsius, Fahrenheit, probe
    *   **AGENT:** anesthetic agents, MAC, N₂O, FiO₂, Halothane, Isoflurane, Sevoflurane, Desflurane, Enflurane
    *   **MRI:** MRI, magnet, Zone 3/4, gauss, conditional, bore
    *   **PWR (power):** battery, AC power, charger, power button
    *   **CONN (connectivity):** wireless, communication, pairing, remote monitor, PIC iX, module
    *   **SRV (service):** service, maintenance, FRU, diagnostics, logs, update, firmware, software, warranty

**Score\_Rule:**  
If child and parent both match any group → `Score_Rule = 0.85` and record `Matched_Groups`.

***

#### **Semantic Similarity**

*   Use **Azure OpenAI embeddings** (`text-embedding-3-large`) by default.
*   Compute cosine similarity ∈ \[0..1].
*   SBERT fallback option (`sentence-transformers/all-MiniLM-L6-v2`).

#### **TF‑IDF Similarity**

*   `ngram_range=(1,3)`
*   Custom stop‑phrases + English stop‑words
*   Cosine similarity ∈ \[0..1]

***

### **Fusion Logic**

**What does “if Score\_Rule exists” mean?**  
It means: if the rule-based check found a domain keyword match, then `Score_Rule` is set to 0.85.  
In that case, we prioritize it in the fusion step:

```python
if Score_Rule is not None:
    Computed_Score = max(Score_Rule, Score_Embedding, Score_TFIDF)
    Method_Used = "Fusion"
else:
    Computed_Score = max(Score_Embedding, Score_TFIDF)
    Method_Used = "SBERT" if Score_Embedding >= Score_TFIDF else "TF-IDF"
```

***

### **Functions to Implement**

1.  `load_excel(file_path, child_sheet, parent_sheet)` → returns `children_df`, `parents_df`
2.  `preprocess_text(text, stop_phrases)` → cleans boilerplate, normalizes, lemmatizes
3.  `compute_rule_score(child_text, parent_text)` → returns `(score, matched_groups)`
4.  `compute_embedding_similarity(child_text, parent_text)` → Azure OpenAI or SBERT cosine similarity
5.  `compute_tfidf_similarity(child_text, parent_text)` → scikit-learn TF‑IDF + cosine
6.  `compute_fusion_score(rule_score, embed_score, tfidf_score)` → returns `(computed_score, method)`
7.  `rank_top_k(children_df, parents_df, k)` → returns DataFrame with Top‑K matches per child
8.  `write_to_excel(output_df, file_path, sheet_name)` → appends new sheet without overwriting others
9.  Streamlit UI functions:
    *   `sidebar_controls()`
    *   `display_results(df)`
    *   `download_button(df)`

***

### **Tech Stack**

*   Python 3.10+
*   Streamlit for UI
*   pandas, openpyxl for Excel I/O
*   scikit-learn for TF‑IDF
*   sentence-transformers (optional SBERT fallback)
*   Azure OpenAI SDK for embeddings
*   spaCy or NLTK for lemmatization

***

### **Deliverables**

*   `app.py` (Streamlit)
*   `matching.py` (core logic)
*   `domain_lexicon.json` (seeded with synonyms for each group)
*   `requirements.txt`
*   README with setup instructions and environment variables for Azure OpenAI keys

***

### **Example Domain Lexicon JSON**

```json
{
  "alarm": ["alarm light", "visual indicator", "acknowledge alarm"],
  "co2": ["respiration rate", "apnea detection", "capnogram"],
  "connectivity": ["pairing", "link status", "PICiX", "remote monitor"],
  "nibp": ["NBP", "non-invasive BP", "blood pressure cuff"]
}
```

***

### **Example UI Layout**

*   **Sidebar:** File upload, sheet selection, algorithm settings
*   **Main:** Table of Top‑K matches, download button, filters

***

### **Clarifications**

Ask any clarifying questions that you need to in order to produce this tracing tool. 
Use this application as an example for building the new tool: https://github.com/scottdstearns/Tool_RequirementsTracing.git

