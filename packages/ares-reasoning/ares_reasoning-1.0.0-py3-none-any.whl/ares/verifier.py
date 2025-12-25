"""
Verifier Module for ARES.

Phase 3: Reject bad reasoning steps.
This module provides rule-based verification for math and logic problems.
"""

import re
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class VerificationResult:
    """Result of verifying a candidate answer."""
    is_valid: bool
    confidence: float  # 0.0 to 1.0
    reason: str
    checks_passed: List[str]
    checks_failed: List[str]


class MathVerifier:
    """
    Rule-based verifier for math problems.
    
    Checks:
    1. Answer is a valid number
    2. Reasoning contains calculation steps
    3. No obvious arithmetic errors detected
    4. Answer makes sense (not negative for count problems, etc.)
    """
    
    def verify(self, problem: str, reasoning: str, answer: str) -> VerificationResult:
        """Verify a math problem answer."""
        checks_passed = []
        checks_failed = []
        
        # Check 1: Answer is a valid number or fraction
        is_numeric = self._is_valid_number(answer)
        if is_numeric:
            checks_passed.append("answer_is_numeric")
        else:
            checks_failed.append("answer_not_numeric")
        
        # Check 2: Reasoning contains math operations
        has_math = self._has_math_operations(reasoning)
        if has_math:
            checks_passed.append("reasoning_has_math")
        else:
            checks_failed.append("no_math_in_reasoning")
        
        # Check 3: Check for impossible negative results in counting problems
        if self._is_counting_problem(problem):
            numeric_answer = self._extract_number(answer)
            if numeric_answer is not None and numeric_answer < 0:
                checks_failed.append("negative_count_impossible")
            else:
                checks_passed.append("count_is_non_negative")
        
        # Check 4: Check for "doesn't make sense" phrases (LLM self-doubt)
        if self._has_self_doubt(reasoning):
            checks_failed.append("llm_expressed_doubt")
        else:
            checks_passed.append("no_self_doubt")
        
        # Check 5: Verify calculation consistency (basic check)
        calc_consistent = self._check_calculation_consistency(reasoning, answer)
        if calc_consistent:
            checks_passed.append("calculation_consistent")
        else:
            checks_failed.append("calculation_inconsistent")
        
        # Calculate confidence
        total_checks = len(checks_passed) + len(checks_failed)
        confidence = len(checks_passed) / total_checks if total_checks > 0 else 0.0
        
        # Determine validity
        is_valid = len(checks_failed) == 0 or (confidence >= 0.6 and "answer_not_numeric" not in checks_failed)
        
        reason = f"Passed {len(checks_passed)}/{total_checks} checks"
        if checks_failed:
            reason += f". Failed: {', '.join(checks_failed)}"
        
        return VerificationResult(
            is_valid=is_valid,
            confidence=confidence,
            reason=reason,
            checks_passed=checks_passed,
            checks_failed=checks_failed
        )
    
    def _is_valid_number(self, answer: str) -> bool:
        """Check if answer is a valid number or fraction."""
        if not answer:
            return False
        
        # Clean the answer
        clean = answer.strip().replace(",", "").replace("$", "").replace("%", "")
        clean = clean.replace(" ", "")
        
        # Check for fraction
        if "/" in clean:
            parts = clean.split("/")
            if len(parts) == 2:
                try:
                    float(parts[0])
                    float(parts[1])
                    return True
                except:
                    pass
        
        # Check for regular number
        try:
            float(clean)
            return True
        except:
            return False
    
    def _extract_number(self, answer: str) -> Optional[float]:
        """Extract numeric value from answer."""
        if not answer:
            return None
        
        clean = answer.strip().replace(",", "").replace("$", "").replace("%", "")
        clean = clean.replace(" ", "")
        
        # Handle fraction
        if "/" in clean:
            parts = clean.split("/")
            if len(parts) == 2:
                try:
                    return float(parts[0]) / float(parts[1])
                except:
                    return None
        
        try:
            return float(clean)
        except:
            return None
    
    def _has_math_operations(self, reasoning: str) -> bool:
        """Check if reasoning contains mathematical operations."""
        math_patterns = [
            r'\d+\s*[\+\-\*\/\×\÷]\s*\d+',  # Basic operations
            r'\d+\s*=\s*\d+',  # Equations
            r'total|sum|difference|product|quotient',  # Math words
        ]
        
        for pattern in math_patterns:
            if re.search(pattern, reasoning, re.IGNORECASE):
                return True
        return False
    
    def _is_counting_problem(self, problem: str) -> bool:
        """Detect if this is a counting problem where negative answers are impossible."""
        counting_keywords = [
            "how many", "total", "count", "number of", 
            "students", "people", "items", "trees"
        ]
        problem_lower = problem.lower()
        return any(kw in problem_lower for kw in counting_keywords)
    
    def _has_self_doubt(self, reasoning: str) -> bool:
        """Detect if LLM expressed doubt about its own reasoning."""
        doubt_phrases = [
            "doesn't make sense",
            "does not make sense",
            "this is incorrect",
            "this can't be right",
            "impossible",
            "let me reconsider",
            "wait, that's wrong"
        ]
        reasoning_lower = reasoning.lower()
        return any(phrase in reasoning_lower for phrase in doubt_phrases)
    
    def _check_calculation_consistency(self, reasoning: str, answer: str) -> bool:
        """Basic check: does the final answer appear in the reasoning?"""
        if not answer:
            return False
        
        # Extract the numeric part of the answer
        numeric = self._extract_number(answer)
        if numeric is None:
            return True  # Can't check, assume ok
        
        # Check if this number appears near the end of reasoning
        lines = reasoning.strip().split("\n")
        last_few_lines = " ".join(lines[-5:]) if len(lines) >= 5 else reasoning
        
        # Look for the answer value in final lines
        answer_str = str(int(numeric)) if numeric == int(numeric) else str(numeric)
        return answer_str in last_few_lines


class LogicVerifier:
    """
    Rule-based verifier for logic problems.
    
    Checks:
    1. Answer format matches expected pattern
    2. All entities from problem are accounted for
    3. No contradictions in the answer
    """
    
    def verify(self, problem: str, reasoning: str, answer: str) -> VerificationResult:
        """Verify a logic problem answer."""
        checks_passed = []
        checks_failed = []
        
        # Check 1: Answer exists and is not empty
        if answer and len(answer.strip()) > 0:
            checks_passed.append("answer_provided")
        else:
            checks_failed.append("no_answer")
        
        # Check 2: Reasoning shows step-by-step logic
        if self._has_logical_steps(reasoning):
            checks_passed.append("has_logical_steps")
        else:
            checks_failed.append("no_logical_steps")
        
        # Check 3: No self-contradiction detected
        if not self._has_contradiction(reasoning):
            checks_passed.append("no_contradiction")
        else:
            checks_failed.append("self_contradiction")
        
        # Check 4: Answer contains expected elements
        if self._answer_has_structure(answer):
            checks_passed.append("answer_structured")
        else:
            checks_failed.append("answer_unstructured")
        
        # Calculate confidence
        total_checks = len(checks_passed) + len(checks_failed)
        confidence = len(checks_passed) / total_checks if total_checks > 0 else 0.0
        
        is_valid = confidence >= 0.5 and "no_answer" not in checks_failed
        
        reason = f"Passed {len(checks_passed)}/{total_checks} checks"
        if checks_failed:
            reason += f". Failed: {', '.join(checks_failed)}"
        
        return VerificationResult(
            is_valid=is_valid,
            confidence=confidence,
            reason=reason,
            checks_passed=checks_passed,
            checks_failed=checks_failed
        )
    
    def _has_logical_steps(self, reasoning: str) -> bool:
        """Check if reasoning shows logical deduction."""
        logic_patterns = [
            r'if\s+.+\s+then',
            r'therefore',
            r'this means',
            r'since\s+.+\s*,',
            r'because',
            r'we know that',
            r'must be',
            r'cannot be'
        ]
        
        for pattern in logic_patterns:
            if re.search(pattern, reasoning, re.IGNORECASE):
                return True
        return False
    
    def _has_contradiction(self, reasoning: str) -> bool:
        """Detect self-contradiction in reasoning."""
        contradiction_phrases = [
            "but wait",
            "this contradicts",
            "that's not possible",
            "this is wrong",
            "let me start over"
        ]
        reasoning_lower = reasoning.lower()
        return any(phrase in reasoning_lower for phrase in contradiction_phrases)
    
    def _answer_has_structure(self, answer: str) -> bool:
        """Check if answer has expected structure (colons, commas, etc.)."""
        if not answer:
            return False
        # Logic answers often have format like "Alice:cat, Bob:dog"
        return ":" in answer or "," in answer or len(answer.split()) >= 2


class Verifier:
    """
    Main verifier that routes to appropriate sub-verifier.
    """
    
    def __init__(self):
        self.math_verifier = MathVerifier()
        self.logic_verifier = LogicVerifier()
    
    def verify(
        self, 
        problem: str, 
        reasoning: str, 
        answer: str, 
        problem_type: str = "math"
    ) -> VerificationResult:
        """
        Verify an answer.
        
        Args:
            problem: The original problem text
            reasoning: The LLM's reasoning steps
            answer: The final answer
            problem_type: "math" or "logic"
        
        Returns:
            VerificationResult with validity and confidence
        """
        if problem_type == "logic":
            return self.logic_verifier.verify(problem, reasoning, answer)
        else:
            return self.math_verifier.verify(problem, reasoning, answer)
    
    def verify_candidates(
        self, 
        problem: str, 
        candidates: list, 
        problem_type: str = "math"
    ) -> list:
        """
        Verify all candidates and return sorted by confidence.
        
        Returns list of (candidate, verification_result) tuples,
        sorted by confidence descending.
        """
        results = []
        for candidate in candidates:
            result = self.verify(
                problem=problem,
                reasoning=candidate.reasoning,
                answer=candidate.answer,
                problem_type=problem_type
            )
            results.append((candidate, result))
        
        # Sort by confidence (highest first)
        results.sort(key=lambda x: x[1].confidence, reverse=True)
        return results
    
    def pick_best(
        self, 
        problem: str, 
        candidates: list, 
        problem_type: str = "math"
    ) -> Tuple[any, VerificationResult]:
        """
        Pick the best candidate using VOTING + VERIFICATION.
        
        Strategy:
        1. Count votes for each unique answer
        2. Calculate combined score = verification_confidence × vote_fraction
        3. Pick highest combined score
        
        Returns (best_candidate, verification_result)
        """
        if not candidates:
            return None, None
        
        # First, verify all candidates
        verified = self.verify_candidates(problem, candidates, problem_type)
        
        # Count votes for each answer
        answer_counts = {}
        answer_candidates = {}
        for candidate, result in verified:
            if candidate.answer:
                ans_norm = candidate.answer.lower().strip()
                answer_counts[ans_norm] = answer_counts.get(ans_norm, 0) + 1
                if ans_norm not in answer_candidates:
                    answer_candidates[ans_norm] = (candidate, result)
        
        total_votes = sum(answer_counts.values())
        
        if total_votes == 0:
            # No valid answers, return first candidate
            return verified[0] if verified else (None, None)
        
        # Calculate combined score for each answer
        best_score = -1
        best_candidate = None
        best_result = None
        
        for ans, count in answer_counts.items():
            vote_fraction = count / total_votes
            candidate, result = answer_candidates[ans]
            
            # Combined score: verification confidence × vote agreement
            combined_score = result.confidence * vote_fraction
            
            if combined_score > best_score:
                best_score = combined_score
                best_candidate = candidate
                best_result = result
        
        return best_candidate, best_result
    
    def pick_best_with_details(
        self, 
        problem: str, 
        candidates: list, 
        problem_type: str = "math"
    ) -> dict:
        """
        Pick best candidate and return detailed scoring info.
        
        Returns dict with:
            - best_candidate
            - best_result
            - all_scores: list of (answer, vote_count, vote_pct, confidence, combined_score)
        """
        if not candidates:
            return {"best_candidate": None, "best_result": None, "all_scores": []}
        
        # Verify all candidates
        verified = self.verify_candidates(problem, candidates, problem_type)
        
        # Count votes
        answer_counts = {}
        answer_candidates = {}
        for candidate, result in verified:
            if candidate.answer:
                ans_norm = candidate.answer.lower().strip()
                answer_counts[ans_norm] = answer_counts.get(ans_norm, 0) + 1
                # Keep the highest confidence candidate for this answer
                if ans_norm not in answer_candidates or result.confidence > answer_candidates[ans_norm][1].confidence:
                    answer_candidates[ans_norm] = (candidate, result)
        
        total_votes = sum(answer_counts.values())
        
        # Calculate all scores
        all_scores = []
        best_score = -1
        best_candidate = None
        best_result = None
        
        for ans, count in answer_counts.items():
            vote_pct = count / total_votes if total_votes > 0 else 0
            candidate, result = answer_candidates[ans]
            combined = result.confidence * vote_pct
            
            all_scores.append({
                "answer": ans,
                "vote_count": count,
                "vote_pct": vote_pct,
                "confidence": result.confidence,
                "combined_score": combined
            })
            
            if combined > best_score:
                best_score = combined
                best_candidate = candidate
                best_result = result
        
        # Sort by combined score
        all_scores.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return {
            "best_candidate": best_candidate,
            "best_result": best_result,
            "all_scores": all_scores
        }


if __name__ == "__main__":
    # Test the verifier
    from .generator import Candidate
    
    verifier = Verifier()
    
    # Test case 1: Good math answer
    print("=" * 60)
    print("TEST 1: Good math answer")
    print("=" * 60)
    
    result = verifier.verify(
        problem="A farmer has 12 + 24 = ? trees",
        reasoning="First, 12 trees. Then 24 more. Total = 12 + 24 = 36 trees.",
        answer="36",
        problem_type="math"
    )
    print(f"Valid: {result.is_valid}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Reason: {result.reason}")
    
    # Test case 2: Bad math answer (LLM doubt)
    print()
    print("=" * 60)
    print("TEST 2: LLM expressed self-doubt")
    print("=" * 60)
    
    result = verifier.verify(
        problem="Emma pays $20 for $21 of goods",
        reasoning="Total = $21. Change = $20 - $21 = -$1. Wait, this doesn't make sense...",
        answer="-1",
        problem_type="math"
    )
    print(f"Valid: {result.is_valid}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Reason: {result.reason}")
