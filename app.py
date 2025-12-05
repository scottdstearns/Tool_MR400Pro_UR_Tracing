import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from matching import (
    AzureEmbeddingConfig,
    EmbeddingProvider,
    MatchingConfig,
    load_excel,
    rank_top_k,
    validate_trace_coverage,
    results_to_excel_bytes,
)

load_dotenv()

st.set_page_config(page_title="MR400 Pro Requirement Tracer", layout="wide", initial_sidebar_state="expanded")

# Show version
try:
    with open("VERSION", "r") as f:
        version = f.read().strip()
except:
    version = "unknown"

st.title("🔗 MR400 Pro Legacy → Canonical Requirement Matcher")
st.caption(f"Upload a workbook, map sheets/columns, and compute hybrid matches (semantic + lexical + domain rules). **Version: {version}**")

# ========== FILE UPLOAD ==========
uploaded_file = st.sidebar.file_uploader("📁 Upload Excel workbook", type=["xlsx"])
if not uploaded_file:
    st.info("👈 Upload an Excel workbook to begin.")
    st.stop()

try:
    excel = pd.ExcelFile(uploaded_file)
    sheet_names = excel.sheet_names
except Exception as exc:
    st.error(f"❌ Unable to read workbook: {exc}")
    st.stop()

# ========== SHEET SELECTION ==========
st.sidebar.subheader("📊 Sheet Selection")
child_sheet = st.sidebar.selectbox("Child (legacy) sheet", sheet_names, key="child_sheet")
parent_sheet = st.sidebar.selectbox(
    "Parent (canonical) sheet",
    sheet_names,
    index=min(1, len(sheet_names) - 1),
    key="parent_sheet"
)

if child_sheet == parent_sheet:
    st.sidebar.warning("⚠️ Select different sheets for children and parents.")
    st.stop()

child_df, parent_df = load_excel(uploaded_file, child_sheet, parent_sheet)

# ========== PREVIEW ==========
with st.expander("📋 Preview Data", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        st.caption(f"**Children:** {child_sheet} ({len(child_df)} rows)")
        st.dataframe(child_df.head(5), use_container_width=True)
    with c2:
        st.caption(f"**Parents:** {parent_sheet} ({len(parent_df)} rows)")
        st.dataframe(parent_df.head(5), use_container_width=True)

# ========== COLUMN MAPPING ==========
st.sidebar.subheader("🔗 Column Mapping")
child_id_col = st.sidebar.selectbox("Child ID column", child_df.columns, key="child_id")
child_text_col = st.sidebar.selectbox("Child Text column", child_df.columns, key="child_text")
parent_id_col = st.sidebar.selectbox("Parent ID column", parent_df.columns, key="parent_id")
parent_text_col = st.sidebar.selectbox("Parent Text column", parent_df.columns, key="parent_text")

# Optional extra columns
st.sidebar.subheader("➕ Extra Columns (Optional)")
st.sidebar.caption("Select additional columns to include in output (e.g., short descriptions, status, etc.)")
child_extra_options = [c for c in child_df.columns if c not in (child_id_col, child_text_col)]
parent_extra_options = [c for c in parent_df.columns if c not in (parent_id_col, parent_text_col)]

extra_child_cols = st.sidebar.multiselect("Child extra columns", child_extra_options, key="child_extra")
extra_parent_cols = st.sidebar.multiselect("Parent extra columns", parent_extra_options, key="parent_extra")

# ========== ALGORITHM CONTROLS ==========
st.sidebar.subheader("⚙️ Algorithm Controls")
top_k = st.sidebar.number_input("Top-K matches per child", min_value=1, max_value=10, value=3, key="top_k")
ngram_max = st.sidebar.slider("TF-IDF max n-gram", min_value=1, max_value=3, value=3, key="ngram")
stop_phrases_input = st.sidebar.text_area(
    "Stop phrases (comma-separated)",
    value=", ".join(MatchingConfig().stop_phrases),
    key="stop_phrases",
    height=100,
)
rules_enabled = st.sidebar.checkbox("Enable domain rule boosts", value=True, key="rules")
score_threshold = st.sidebar.slider(
    "Min confidence threshold (for validation)",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    key="threshold"
)

# ========== COMPUTE MATCHES ==========
if st.button("🚀 Compute Matches", type="primary", use_container_width=True):
    # Validate column selections first
    if child_id_col == child_text_col:
        st.error("❌ Child ID and Child Text cannot be the same column")
        st.stop()
    if parent_id_col == parent_text_col:
        st.error("❌ Parent ID and Parent Text cannot be the same column")
        st.stop()
    
    # Rename columns for matching
    work_child = child_df.copy()
    work_child = work_child.rename(columns={child_id_col: "Child_ID", child_text_col: "Child_Text"})
    
    # Ensure required columns exist in child
    if "Child_ID" not in work_child.columns or "Child_Text" not in work_child.columns:
        st.error(f"❌ Child dataframe missing required columns after mapping")
        st.error(f"Expected: Child_ID, Child_Text")
        st.error(f"Got: {list(work_child.columns)}")
        st.error(f"Mapping: {child_id_col} → Child_ID, {child_text_col} → Child_Text")
        st.stop()
    
    work_parent = parent_df.copy()
    work_parent = work_parent.rename(
        columns={
            parent_id_col: "Parent_ID",
            parent_text_col: "Parent_Text",
        }
    )
    
    # Ensure required columns exist in parent
    if "Parent_ID" not in work_parent.columns or "Parent_Text" not in work_parent.columns:
        st.error(f"❌ Parent dataframe missing required columns after mapping")
        st.error(f"Expected: Parent_ID, Parent_Text")
        st.error(f"Got: {list(work_parent.columns)}")
        st.error(f"Mapping: {parent_id_col} → Parent_ID, {parent_text_col} → Parent_Text")
        st.stop()

    config = MatchingConfig(
        top_k=top_k,
        ngram_range=(1, ngram_max),
        stop_phrases=[phrase.strip() for phrase in stop_phrases_input.split(",") if phrase.strip()],
        rules_enabled=rules_enabled,
    )

    # Check if using LiteLLM proxy or direct Azure OpenAI
    use_litellm = bool(os.getenv("OPENAI_BASE_URL"))
    
    if use_litellm:
        st.info("ℹ️ Using LiteLLM proxy for embeddings")
        azure_config = None
        emb_provider = EmbeddingProvider(
            azure_config=None,
            fallback_model_name=os.getenv("SBERT_MODEL_NAME", config.sbert_model_name),
            use_litellm_proxy=True,
            proxy_base_url=os.getenv("OPENAI_BASE_URL"),
            proxy_api_key=os.getenv("OPENAI_API_KEY", "sk-1234"),
        )
    else:
        st.info("ℹ️ Using direct Azure OpenAI for embeddings")
        azure_config = AzureEmbeddingConfig(
            api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            deployment_name=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"),
            model_name=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
        )
        emb_provider = EmbeddingProvider(
            azure_config=azure_config,
            fallback_model_name=os.getenv("SBERT_MODEL_NAME", config.sbert_model_name),
        )

    # Debug: show what columns we have after renaming
    with st.expander("🔍 Debug: Column Mapping", expanded=False):
        st.write("**Child columns after mapping:**", list(work_child.columns))
        st.write("**Parent columns after mapping:**", list(work_parent.columns))
    
    with st.spinner("🔄 Running hybrid matching (embeddings + TF-IDF + rules)..."):
        try:
            results = rank_top_k(
                work_child,
                work_parent,
                config,
                emb_provider,
                extra_child_cols=extra_child_cols,
                extra_parent_cols=extra_parent_cols,
            )
        except Exception as e:
            import traceback
            st.error(f"❌ Matching failed: {e}")
            with st.expander("Full error trace"):
                st.code(traceback.format_exc())
            st.stop()

    # Validation
    validation = validate_trace_coverage(results, work_child, work_parent, min_score_threshold=score_threshold)
    
    st.success(f"✅ Generated {len(results)} trace rows")
    
    # Validation warnings
    if validation["orphan_children"]:
        st.warning(
            f"⚠️ **{len(validation['orphan_children'])} children** have no high-confidence parents "
            f"(all scores < {score_threshold:.2f}): {', '.join(map(str, validation['orphan_children'][:10]))}"
            + ("..." if len(validation['orphan_children']) > 10 else "")
        )
    
    if validation["childless_parents"]:
        st.warning(
            f"⚠️ **{len(validation['childless_parents'])} parents** have no children mapped: "
            f"{', '.join(map(str, validation['childless_parents'][:10]))}"
            + ("..." if len(validation['childless_parents']) > 10 else "")
        )
    
    # Display results
    st.subheader("📊 Results")
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_method = st.selectbox("Filter by method", ["All", "Fusion", "SBERT", "TF-IDF", "N/A"], key="filter_method")
    with col2:
        min_score_filter = st.slider("Min computed score", 0.0, 1.0, 0.0, 0.05, key="min_score")
    with col3:
        show_top_n = st.number_input("Show top N rows", min_value=10, max_value=len(results), value=min(100, len(results)), step=10, key="show_n")
    
    # Apply filters
    filtered = results.copy()
    if filter_method != "All":
        filtered = filtered[filtered["Method_Used"] == filter_method]
    filtered = filtered[filtered["Computed_Score"] >= min_score_filter]
    filtered = filtered.head(show_top_n)
    
    st.dataframe(filtered, use_container_width=True, height=400)
    
    # Download buttons
    st.subheader("💾 Download Results")
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        excel_bytes = results_to_excel_bytes(results, sheet_name="Trace_Matrix_Scores")
        st.download_button(
            label="📥 Download Excel",
            data=excel_bytes,
            file_name="trace_matrix_scores.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    
    with col_dl2:
        st.download_button(
            label="📥 Download CSV",
            data=results.to_csv(index=False).encode("utf-8"),
            file_name="trace_matrix_scores.csv",
            mime="text/csv",
            use_container_width=True,
        )
