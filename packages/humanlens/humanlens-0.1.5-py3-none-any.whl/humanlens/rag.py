# humanlens/rag.py
# =====================================================
# HumanLens RAG Evaluation (RAGAS) — schema aligned to your RAGAS build
#
# Your RAGAS validation requires:
#   - user_input
#   - retrieved_contexts
#
# Input JSON records:
#   user_input, response, retrieved_contexts
#
# You specified: retrieved_contexts is reference.
#
# IMPORTANT FIXES / IMPROVEMENTS
# - Use LangChain OpenAIEmbeddings (embed_query/embed_documents) ✅
# - Friendly error if rag extras are not installed
# - Friendly error if OPENAI_API_KEY missing
# - Optional env overrides:
#     HL_EVAL_LLM, HL_EMBED_MODEL
# - Optional: reduce RAGAS "requested 3 generations" warning by forcing n=1
# =====================================================

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import pandas as pd

# --- Optional dependency guard (so core install works) ---
try:
    from ragas import evaluate
    from ragas.metrics import (
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
        answer_correctness,
    )
    from ragas.dataset_schema import EvaluationDataset
    from ragas.llms import LangchainLLMWrapper
except ImportError as e:
    raise ImportError(
        "RAG evaluation requires extra dependencies.\n"
        "Install with: pip install \"humanlens[rag]\""
    ) from e

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError as e:
    raise ImportError(
        "RAG evaluation requires langchain-openai.\n"
        "Install with: pip install \"humanlens[rag]\""
    ) from e


def _as_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    return s if s else None


def _load_json_rows(json_path: str) -> List[Dict[str, Any]]:
    with open(json_path, "r") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise ValueError("Expected JSON file to contain a list of records.")
    return raw


def _as_list_str(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        out: List[str] = []
        for item in x:
            s = _as_str(item)
            if s:
                out.append(s)
        return out
    s = _as_str(x)
    return [s] if s else []


def _to_samples(json_path: str) -> List[Dict[str, Any]]:
    """
    Build dicts that match the schema your installed RAGAS expects:
      - user_input: str
      - response: str
      - retrieved_contexts: list[str]
      - reference: str   (required by some metrics in your build)
    """
    raw = _load_json_rows(json_path)
    samples: List[Dict[str, Any]] = []

    for r in raw:
        user_input = _as_str(r.get("user_input"))
        response = _as_str(r.get("response"))
        retrieved_ctx_list = _as_list_str(r.get("retrieved_contexts"))

        # You said retrieved_contexts is reference
        reference = "\n".join(retrieved_ctx_list).strip() if retrieved_ctx_list else None

        if not user_input or not response or not reference:
            continue

        samples.append(
            {
                "user_input": user_input,
                "response": response,
                "retrieved_contexts": retrieved_ctx_list,
                "reference": reference,
                # Optional metadata (kept for slicing later)
                "race": _as_str(r.get("race")),
                "gender": _as_str(r.get("gender")),
                "age": r.get("age"),
            }
        )

    if not samples:
        raise ValueError(
            "No valid samples found. Each record must include:\n"
            "  - user_input\n"
            "  - response\n"
            "  - retrieved_contexts (string or list)\n"
        )

    return samples


def rag_analyze(
    json_path: str,
    run_name: str | None = None,
    suppress_display: bool = False,
):
    # Fail fast if key missing (RAGAS metrics are LLM/embeddings-backed)
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set.\n"
            "Set it with:\n"
            "  export OPENAI_API_KEY='sk-...'\n"
        )

    # Dataset (required by your ragas build)
    samples = _to_samples(json_path)
    dataset = EvaluationDataset.from_list(samples)

    # Evaluator LLM
    eval_model = os.getenv("HL_EVAL_LLM", "gpt-4o-mini")

    # Force n=1 to avoid noisy warning:
    # "LLM returned 1 generations instead of requested 3"
    # Some LangChain versions don't accept n=; model_kwargs works broadly.
    llm_lc = ChatOpenAI(
        model=eval_model,
        temperature=0,
        model_kwargs={"n": 1},
    )
    llm = LangchainLLMWrapper(llm_lc)

    # Embeddings (LangChain) — has embed_query/embed_documents ✅
    embed_model = os.getenv("HL_EMBED_MODEL", "text-embedding-3-small")
    embeddings = OpenAIEmbeddings(model=embed_model)

    metrics = [
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
        answer_correctness,
    ]

    results = evaluate(
        dataset,
        metrics=metrics,
        llm=llm,
        embeddings=embeddings,
    )

    scores = results.to_pandas()

    summary = {
        "run_name": run_name or "rag_eval",
        "num_samples": int(len(scores)),
        "eval_model": eval_model,
        "embed_model": embed_model,
        "metrics_mean": scores.mean(numeric_only=True).to_dict(),
        "metrics_std": scores.std(numeric_only=True).to_dict(),
        "notes": (
            "Schema uses user_input/response/retrieved_contexts (as required by installed RAGAS). "
            "reference == joined retrieved_contexts (as requested)."
        ),
    }

    if not suppress_display:
        print("\n===============================")
        print(" RAG Evaluation Summary (RAGAS)")
        print("===============================\n")
        print(pd.DataFrame([summary["metrics_mean"]]).T.rename(columns={0: "mean"}))

    return {
        "summary": summary,
        "per_sample": scores.to_dict(orient="records"),
    }


def rag_evaluate(json_path: str, **kwargs):
    return rag_analyze(json_path, **kwargs)
