"""
ARES - Beam Search over Reasoning Steps

Phase 4: Explore reasoning paths and select best answer.

This is the core of ARES v1:
1. Generate N candidate answers
2. Verify each candidate
3. Use voting + verification to pick the best
4. Compare against baseline single-shot
"""

import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .llm import get_provider
from .generator import generate_candidates, Candidate
from .verifier import Verifier, VerificationResult
from .problems import get_problem_by_id, ALL_PROBLEMS


@dataclass
class SearchResult:
    """Result of running ARES search on a problem."""
    problem_id: str
    problem_type: str
    expected_answer: str
    
    # Candidates generated
    candidates: List[Candidate]
    num_candidates: int
    
    # Best answer selected
    best_candidate: Candidate
    best_score: float
    predicted_answer: str
    
    # Verification details
    all_scores: List[Dict]
    
    # Outcome
    is_correct: bool
    
    # Timing
    elapsed_seconds: float


class AresSearch:
    """
    ARES v1 Beam Search.
    
    Not actual beam search over reasoning *steps* (that's v2),
    but beam search over *complete answers*:
    1. Generate N complete solutions
    2. Score each with verifier
    3. Pick best by voting + verification
    """
    
    def __init__(self, n_candidates: int = 5, temperature: float = 0.8):
        self.n_candidates = n_candidates
        self.temperature = temperature
        self.verifier = Verifier()
    
    def search(
        self, 
        problem: str, 
        problem_type: str = "math",
        expected_answer: str = None,
        problem_id: str = None,
        verbose: bool = True
    ) -> SearchResult:
        """
        Run ARES search on a problem.
        
        Args:
            problem: Problem text
            problem_type: "math" or "logic"
            expected_answer: Ground truth (for evaluation)
            problem_id: Problem ID (for logging)
            verbose: Print progress
        
        Returns:
            SearchResult with prediction and metadata
        """
        start_time = time.time()
        
        if verbose:
            print(f"Generating {self.n_candidates} candidates...")
        
        # Step 1: Generate candidates
        candidates = generate_candidates(
            problem=problem,
            n_candidates=self.n_candidates,
            temperature=self.temperature,
            delay_between=3.0,
            verbose=verbose
        )
        
        if verbose:
            print()
            print("Verifying candidates...")
        
        # Step 2: Verify and score
        result = self.verifier.pick_best_with_details(
            problem=problem,
            candidates=candidates,
            problem_type=problem_type
        )
        
        best_candidate = result["best_candidate"]
        all_scores = result["all_scores"]
        
        # Get best score
        best_score = all_scores[0]["combined_score"] if all_scores else 0.0
        
        # Get predicted answer
        predicted = best_candidate.answer if best_candidate else None
        
        # Check correctness
        is_correct = False
        if predicted and expected_answer:
            pred_norm = predicted.lower().strip()
            exp_norm = expected_answer.lower().strip()
            is_correct = pred_norm == exp_norm
        
        elapsed = time.time() - start_time
        
        return SearchResult(
            problem_id=problem_id or "unknown",
            problem_type=problem_type,
            expected_answer=expected_answer or "",
            candidates=candidates,
            num_candidates=len(candidates),
            best_candidate=best_candidate,
            best_score=best_score,
            predicted_answer=predicted,
            all_scores=all_scores,
            is_correct=is_correct,
            elapsed_seconds=elapsed
        )
    
    def run_eval(
        self, 
        problems: List[Dict] = None, 
        verbose: bool = True
    ) -> Dict:
        """
        Run ARES on all evaluation problems and compare to baseline.
        
        Returns dict with:
            - results: list of SearchResult
            - accuracy: overall accuracy
            - comparison: vs baseline
        """
        if problems is None:
            problems = ALL_PROBLEMS
        
        results = []
        correct = 0
        
        for i, problem in enumerate(problems):
            if verbose:
                print()
                print("=" * 60)
                print(f"Problem {i+1}/{len(problems)}: {problem['id']}")
                print("=" * 60)
                print(problem["problem"][:100] + "...")
                print(f"Expected: {problem['answer']}")
                print()
            
            result = self.search(
                problem=problem["problem"],
                problem_type=problem["type"],
                expected_answer=problem["answer"],
                problem_id=problem["id"],
                verbose=verbose
            )
            
            results.append(result)
            
            if result.is_correct:
                correct += 1
            
            if verbose:
                print()
                print(f"ARES Answer: {result.predicted_answer}")
                print(f"Correct: {'✓' if result.is_correct else '✗'}")
                print(f"Time: {result.elapsed_seconds:.1f}s")
        
        accuracy = correct / len(problems) if problems else 0
        
        summary = {
            "results": results,
            "total": len(problems),
            "correct": correct,
            "accuracy": accuracy,
            "baseline_accuracy": 0.27,  # From Phase 1
        }
        
        if verbose:
            print()
            print("=" * 60)
            print("ARES EVALUATION SUMMARY")
            print("=" * 60)
            print(f"Total problems: {len(problems)}")
            print(f"Correct: {correct}")
            print(f"ARES Accuracy: {accuracy*100:.1f}%")
            print(f"Baseline Accuracy: 27%")
            print(f"Improvement: {(accuracy - 0.27)*100:+.1f}%")
        
        return summary


def run_single_comparison(problem_id: str, verbose: bool = True):
    """
    Run ARES on a single problem and show detailed comparison.
    """
    problem = get_problem_by_id(problem_id)
    if not problem:
        print(f"Problem {problem_id} not found!")
        return
    
    print("=" * 70)
    print("ARES v1 - Single Problem Comparison")
    print("=" * 70)
    print()
    print(f"PROBLEM: {problem_id}")
    print(problem["problem"])
    print()
    print(f"CORRECT ANSWER: {problem['answer']}")
    print()
    
    # Run ARES
    ares = AresSearch(n_candidates=5, temperature=0.8)
    result = ares.search(
        problem=problem["problem"],
        problem_type=problem["type"],
        expected_answer=problem["answer"],
        problem_id=problem_id,
        verbose=True
    )
    
    print()
    print("=" * 70)
    print("ARES DECISION")
    print("=" * 70)
    print()
    
    print("Scoring breakdown:")
    for score in result.all_scores:
        print(f"  Answer '{score['answer']}': votes={score['vote_count']}, "
              f"conf={score['confidence']:.0%}, combined={score['combined_score']:.2f}")
    
    print()
    print(f"ARES picks: {result.predicted_answer}")
    print(f"Correct answer: {result.expected_answer}")
    print(f"Result: {'✅ CORRECT' if result.is_correct else '❌ WRONG'}")
    print(f"Time: {result.elapsed_seconds:.1f}s")
    
    return result


if __name__ == "__main__":
    # Test on the problem where single-shot often fails
    run_single_comparison("math_006")
