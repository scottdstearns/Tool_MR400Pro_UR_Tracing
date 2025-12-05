"""Hybrid requirement-matching logic for the MR400 Pro tracing tool."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
from typing import Iterable, Literal, Sequence

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI
import httpx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Make sentence-transformers optional (only needed for SBERT fallback)
try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    SentenceTransformer = None

load_dotenv()

DEFAULT_STOP_PHRASES = [
    "the user shall be able to",
    "the user shall",
    "shall be able",
    "as a clinical user",
    "the monitor shall",
]


@dataclass(slots=True)
class AzureEmbeddingConfig:
    api_key: str
    endpoint: str
    api_version: str
    deployment_name: str
    model_name: str


@dataclass(slots=True)
class MatchingConfig:
    top_k: int = 3
    ngram_range: tuple[int, int] = (1, 3)
    stop_phrases: Sequence[str] = tuple(DEFAULT_STOP_PHRASES)
    rules_enabled: bool = True
    lexical_max_features: int | None = None
    lexical_stop_phrases: Sequence[str] = tuple(DEFAULT_STOP_PHRASES)
    sbert_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    lexicon_path: str = "domain_lexicon.json"


class EmbeddingProvider:
    def __init__(
        self,
        azure_config: AzureEmbeddingConfig | None,
        fallback_model_name: str,
        use_litellm_proxy: bool = False,
        proxy_base_url: str | None = None,
        proxy_api_key: str | None = None,
    ) -> None:
        self.azure_config = azure_config
        self.fallback_model_name = fallback_model_name
        self.use_litellm_proxy = use_litellm_proxy
        self.proxy_base_url = proxy_base_url
        self.proxy_api_key = proxy_api_key
        self._sbert: SentenceTransformer | None = None

    def _ensure_sbert(self):
        if not SBERT_AVAILABLE:
            raise RuntimeError(
                "SBERT fallback requested but sentence-transformers is not installed. "
                "Please use Azure OpenAI embeddings or install sentence-transformers."
            )
        if self._sbert is None:
            self._sbert = SentenceTransformer(self.fallback_model_name)
        return self._sbert

    def embed(self, texts: Sequence[str], method: Literal["azure", "sbert"] = "azure") -> np.ndarray:
        if method == "azure" and self.azure_config:
            import sys
            print(f"🔧 DEBUG: matching.py version v5 - explicit proxy config", file=sys.stderr)
            
            # Save proxy settings to configure explicitly
            proxy_url = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
            print(f"🔧 DEBUG: Using proxy: {proxy_url if proxy_url else 'None (direct connection)'}", file=sys.stderr)
            
            http_client = None
            try:
                # Create httpx client with explicit proxy configuration
                # This avoids the 'proxies' keyword error while still using the proxy
                if proxy_url:
                    http_client = httpx.Client(
                        timeout=120.0,  # Increased timeout for proxy
                        transport=httpx.HTTPTransport(retries=3),
                        proxies=proxy_url,  # Explicit proxy string, not dict
                    )
                else:
                    http_client = httpx.Client(
                        timeout=60.0,
                        transport=httpx.HTTPTransport(retries=3),
                    )
                print(f"🔧 DEBUG: httpx client created successfully with proxy support", file=sys.stderr)
                
                client: OpenAI
                if self.use_litellm_proxy and self.proxy_base_url and self.proxy_api_key:
                    print(f"🔧 DEBUG: Using LiteLLM proxy path", file=sys.stderr)
                    client = OpenAI(
                        base_url=self.proxy_base_url,
                        api_key=self.proxy_api_key,
                        http_client=http_client,
                    )
                else:
                    print(f"🔧 DEBUG: Using direct Azure OpenAI - no proxy", file=sys.stderr)
                    print(f"🔧 DEBUG: Azure endpoint: {self.azure_config.endpoint}", file=sys.stderr)
                    client = AzureOpenAI(
                        api_key=self.azure_config.api_key,
                        azure_endpoint=self.azure_config.endpoint,
                        api_version=self.azure_config.api_version,
                        http_client=http_client,
                    )

                print(f"🔧 DEBUG: Client created, calling embeddings API...", file=sys.stderr)
                resp = client.embeddings.create(
                    model=self.azure_config.deployment_name,
                    input=list(texts),
                )
                print(f"🔧 DEBUG: Got {len(resp.data)} embeddings successfully", file=sys.stderr)
                return np.array([item.embedding for item in resp.data], dtype=np.float32)
            except Exception as e:
                print(f"🔧 DEBUG: Error during embedding: {e}", file=sys.stderr)
                raise
            finally:
                # Close http client if created
                if http_client:
                    http_client.close()
                print(f"🔧 DEBUG: Cleaned up http client", file=sys.stderr)

        model = self._ensure_sbert()
        return model.encode(list(texts), convert_to_numpy=True)


def load_excel(file_path: str | Path, child_sheet: str, parent_sheet: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    xls = pd.ExcelFile(file_path)
    return xls.parse(child_sheet), xls.parse(parent_sheet)


def preprocess_text(text: str, stop_phrases: Sequence[str] = DEFAULT_STOP_PHRASES) -> str:
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    lowered = text.lower()
    for phrase in stop_phrases:
        lowered = lowered.replace(phrase, " ")
    return " ".join(lowered.split())


def load_lexicon(path: str | Path) -> dict[str, list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k.upper(): [tok.lower() for tok in v] for k, v in data.items()}


def compute_rule_score(child_text: str, parent_text: str, lexicon: dict[str, list[str]]):
    child_tokens = preprocess_text(child_text).split()
    parent_tokens = preprocess_text(parent_text).split()
    child_set = set(child_tokens)
    parent_set = set(parent_tokens)
    matched_groups: list[str] = []
    for group, keywords in lexicon.items():
        if any(keyword in child_set for keyword in keywords) and any(keyword in parent_set for keyword in keywords):
            matched_groups.append(group)
    if matched_groups:
        return 0.85, matched_groups
    return None, matched_groups


def compute_embedding_similarity(
    child_embeddings: np.ndarray,
    parent_embeddings: np.ndarray,
) -> np.ndarray:
    if child_embeddings.size == 0 or parent_embeddings.size == 0:
        return np.zeros((child_embeddings.shape[0], parent_embeddings.shape[0]))
    child_norm = child_embeddings / np.linalg.norm(child_embeddings, axis=1, keepdims=True)
    parent_norm = parent_embeddings / np.linalg.norm(parent_embeddings, axis=1, keepdims=True)
    return child_norm @ parent_norm.T


def compute_tfidf_similarity(child_texts: Sequence[str], parent_texts: Sequence[str], config: MatchingConfig) -> np.ndarray:
    corpus = list(child_texts) + list(parent_texts)
    vectorizer = TfidfVectorizer(
        ngram_range=config.ngram_range,
        stop_words="english",
        max_features=config.lexical_max_features,
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    child_matrix = tfidf_matrix[: len(child_texts)]
    parent_matrix = tfidf_matrix[len(child_texts) :]
    return cosine_similarity(child_matrix, parent_matrix)


def compute_fusion_score(rule_score, embed_score, tfidf_score):
    if rule_score is not None:
        computed = max(rule_score, embed_score, tfidf_score)
        method = "Fusion"
    else:
        if embed_score >= tfidf_score:
            computed = embed_score
            method = "SBERT"
        else:
            computed = tfidf_score
            method = "TF-IDF"
    return computed, method


def rank_top_k(
    children_df: pd.DataFrame,
    parents_df: pd.DataFrame,
    config: MatchingConfig,
    emb_provider: EmbeddingProvider,
    extra_child_cols: list[str] | None = None,
    extra_parent_cols: list[str] | None = None,
):
    """
    Rank top-K parent matches for each child using hybrid scoring.
    Returns DataFrame with scores and optional extra columns from source data.
    """
    extra_child_cols = extra_child_cols or []
    extra_parent_cols = extra_parent_cols or []
    
    lexicon = load_lexicon(config.lexicon_path)
    
    # Preprocess for matching
    child_texts = children_df["Child_Text"].fillna("").astype(str).map(preprocess_text)
    parent_texts = parents_df["Parent_Text"].fillna("").astype(str).map(preprocess_text)

    # Batch embeddings
    child_emb = emb_provider.embed(child_texts, method="azure")
    parent_emb = emb_provider.embed(parent_texts, method="azure")
    embed_matrix = compute_embedding_similarity(child_emb, parent_emb)
    tfidf_matrix = compute_tfidf_similarity(child_texts, parent_texts, config)

    rows = []
    for child_idx, child_row in children_df.iterrows():
        # Handle empty child text
        if not child_row["Child_Text"] or str(child_row["Child_Text"]).strip() == "":
            # Placeholder row for empty children
            row = {
                "Child_ID": child_row["Child_ID"],
                "Child_Text": "",
                "Parent_ID": "",
                "Parent_Text": "",
                "Score_Rule": 0.0,
                "Score_Embedding": 0.0,
                "Score_TFIDF": 0.0,
                "Computed_Score": 0.0,
                "Method_Used": "N/A",
                "Matched_Groups": "",
            }
            for col in extra_child_cols:
                row[f"Child_{col}"] = child_row.get(col, "")
            for col in extra_parent_cols:
                row[f"Parent_{col}"] = ""
            rows.append(row)
            continue
            
        embed_scores = embed_matrix[child_idx]
        tfidf_scores = tfidf_matrix[child_idx]
        
        # Get top-K by fusion score instead of just embedding
        fusion_scores = []
        for parent_idx in range(len(parents_df)):
            parent_row = parents_df.iloc[parent_idx]
            rule_score, _ = (None, [])
            if config.rules_enabled:
                rule_score, _ = compute_rule_score(
                    child_row["Child_Text"], parent_row["Parent_Text"], lexicon
                )
            fusion_score, _ = compute_fusion_score(
                rule_score,
                float(embed_scores[parent_idx]),
                float(tfidf_scores[parent_idx]),
            )
            fusion_scores.append(fusion_score)
        
        best_parent_indices = np.argsort(-np.array(fusion_scores))[: config.top_k]
        
        for parent_idx in best_parent_indices:
            parent_row = parents_df.iloc[parent_idx]
            rule_score, matched_groups = (None, [])
            if config.rules_enabled:
                rule_score, matched_groups = compute_rule_score(
                    child_row["Child_Text"], parent_row["Parent_Text"], lexicon
                )
            fusion_score, method = compute_fusion_score(
                rule_score,
                float(embed_scores[parent_idx]),
                float(tfidf_scores[parent_idx]),
            )
            
            row = {
                "Child_ID": child_row["Child_ID"],
                "Child_Text": child_row["Child_Text"],
                "Parent_ID": parent_row["Parent_ID"],
                "Parent_Text": parent_row["Parent_Text"],
                "Score_Rule": rule_score if rule_score is not None else 0.0,
                "Score_Embedding": float(embed_scores[parent_idx]),
                "Score_TFIDF": float(tfidf_scores[parent_idx]),
                "Computed_Score": fusion_score,
                "Method_Used": method,
                "Matched_Groups": ", ".join(matched_groups),
            }
            
            # Add extra columns
            for col in extra_child_cols:
                row[f"Child_{col}"] = child_row.get(col, "")
            for col in extra_parent_cols:
                row[f"Parent_{col}"] = parent_row.get(col, "")
                
            rows.append(row)
            
    return pd.DataFrame(rows)


def validate_trace_coverage(results_df: pd.DataFrame, children_df: pd.DataFrame, parents_df: pd.DataFrame, min_score_threshold: float = 0.5):
    """
    Validate trace matrix:
    - Identify children with no high-confidence parents
    - Identify parents with no children mapped
    Returns dict with warnings/stats.
    """
    validation = {
        "orphan_children": [],
        "childless_parents": [],
        "total_children": len(children_df),
        "total_parents": len(parents_df),
        "total_traces": len(results_df),
    }
    
    # Find children with all scores below threshold
    for child_id in children_df["Child_ID"].unique():
        child_traces = results_df[results_df["Child_ID"] == child_id]
        if child_traces.empty or child_traces["Computed_Score"].max() < min_score_threshold:
            validation["orphan_children"].append(child_id)
    
    # Find parents with no children mapped
    mapped_parents = set(results_df["Parent_ID"].unique())
    all_parents = set(parents_df["Parent_ID"].unique())
    validation["childless_parents"] = list(all_parents - mapped_parents)
    
    return validation


def write_to_excel(output_df: pd.DataFrame, file_path: str | Path, sheet_name: str = "Trace_Matrix_Scores") -> None:
    """Write DataFrame to Excel with proper sheet naming."""
    file_path = Path(file_path)
    mode = "a" if file_path.exists() else "w"
    with pd.ExcelWriter(file_path, engine="openpyxl", mode=mode, if_sheet_exists="replace") as writer:
        output_df.to_excel(writer, sheet_name=sheet_name, index=False)


def results_to_excel_bytes(output_df: pd.DataFrame, sheet_name: str = "Trace_Matrix_Scores") -> bytes:
    """Convert DataFrame to Excel bytes for Streamlit download."""
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        output_df.to_excel(writer, sheet_name=sheet_name, index=False)
    return buffer.getvalue()


