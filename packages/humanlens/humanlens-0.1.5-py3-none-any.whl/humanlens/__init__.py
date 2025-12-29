"""
humanlens
---------

A lightweight fairness and compliance auditing toolkit for AI/ML models.

Provides:
  • CLI interface (future) →  `humanlens data.csv`
  • Python API            →  `import humanlens as hl`

Main functions exposed:
  - show_model_catalog()                  : Optional UI selector for model type
  - test()                                : Run fairness + compliance audit
  - run_fairness_audit()                  : Core fairness audit engine
  - save_results()                        : Save standardized JSON audit report
  - submit_for_review()                   : Mock governance approval workflow
  - compare_from_raw_csv()                : Compare fairness across two datasets
  - get_group_metrics()                   : Binary per-group confusion-matrix metrics
  - get_group_metrics_multiclass_ovr()    : Multiclass (OVR) per-group metrics
  - get_group_metrics_regression()        : Regression per-group error metrics
  - print_group_table()                   : Pretty table printer (binary-style table)

Optional (extras):
  - rag_analyze(), rag_evaluate()         : RAGAS-based evaluation (install with: humanlens[rag])
"""

from .core import (
    test,
    run_fairness_audit,
    save_results,
    show_model_catalog,
    submit_for_review,
    compare_from_raw_csv,
    get_group_metrics,
    get_group_metrics_multiclass_ovr,
    get_group_metrics_regression,
    print_group_table,
)

# -----------------------------
# Optional RAG (extras) import
# -----------------------------
# Keeps `import humanlens` working even when ragas/langchain/openai aren't installed.
try:
    from .rag import rag_evaluate, rag_analyze  # noqa: F401

    _RAG_AVAILABLE = True
except Exception:
    rag_evaluate = None  # type: ignore
    rag_analyze = None  # type: ignore
    _RAG_AVAILABLE = False


__all__ = [
    "test",
    "run_fairness_audit",
    "save_results",
    "show_model_catalog",
    "submit_for_review",
    "compare_from_raw_csv",
    "get_group_metrics",
    "get_group_metrics_multiclass_ovr",
    "get_group_metrics_regression",
    "print_group_table",
    # RAG exports (only usable if extras installed)
    "rag_evaluate",
    "rag_analyze",
]

__version__ = "0.1.5"
