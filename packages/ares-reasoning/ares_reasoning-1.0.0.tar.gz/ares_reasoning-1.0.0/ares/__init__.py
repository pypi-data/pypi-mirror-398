"""
ares - Inference-Time Reasoning Framework

Improves LLM accuracy through explicit search and verification.
Trade compute for correctness. No training required.

Usage:
    from ares.search import AresSearch
    
    ares = AresSearch(n_candidates=5)
    result = ares.search("Your problem here", problem_type="math")
    print(result.predicted_answer)

CLI:
    ares solve "Your problem here"
    ares test
    ares info
"""

__version__ = "1.0.0"
__author__ = "ARES Team"

from .search import AresSearch
from .generator import generate_candidates, Candidate
from .verifier import Verifier, VerificationResult

__all__ = [
    "AresSearch",
    "generate_candidates", 
    "Candidate",
    "Verifier",
    "VerificationResult",
]
