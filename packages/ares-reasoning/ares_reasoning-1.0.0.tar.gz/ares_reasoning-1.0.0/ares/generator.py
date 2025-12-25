"""
Multi-Candidate Generator for ARES.

Phase 2: Instead of generating one answer, generate N candidates.
This gives us multiple reasoning paths to evaluate.
"""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass

from .llm import get_provider


@dataclass
class Candidate:
    """A single candidate answer with its reasoning."""
    index: int
    response: str
    answer: Optional[str]
    reasoning: str
    
    def __repr__(self):
        return f"Candidate({self.index}: {self.answer})"


MULTI_CANDIDATE_PROMPT = """Solve this problem step by step. Show your reasoning, then give your final answer.

Problem: {problem}

Think through this carefully. At the end, write your final answer on a new line starting with "ANSWER: "
"""


def extract_answer(response: str) -> Optional[str]:
    """Extract the answer from the LLM response."""
    lines = response.strip().split("\n")
    for line in reversed(lines):
        line = line.strip()
        if line.upper().startswith("ANSWER:"):
            answer = line[7:].strip()
            answer = answer.rstrip(".")
            return answer
    return None


def extract_reasoning(response: str) -> str:
    """Extract just the reasoning (before the answer)."""
    lines = response.strip().split("\n")
    reasoning_lines = []
    for line in lines:
        if line.upper().startswith("ANSWER:"):
            break
        reasoning_lines.append(line)
    return "\n".join(reasoning_lines)


def generate_candidates(
    problem: str,
    n_candidates: int = 5,
    temperature: float = 0.8,
    delay_between: float = 2.0,
    verbose: bool = True
) -> List[Candidate]:
    """
    Generate N candidate solutions for a problem.
    
    Args:
        problem: The problem text
        n_candidates: How many candidates to generate
        temperature: Higher = more diverse (0.7-1.0 recommended)
        delay_between: Seconds between API calls (for rate limits)
        verbose: Print progress
    
    Returns:
        List of Candidate objects
    """
    provider = get_provider()
    prompt = MULTI_CANDIDATE_PROMPT.format(problem=problem)
    
    candidates = []
    
    for i in range(n_candidates):
        if verbose:
            print(f"Generating candidate {i+1}/{n_candidates}...")
        
        try:
            response = provider.generate(prompt, temperature=temperature)
            
            answer = extract_answer(response)
            reasoning = extract_reasoning(response)
            
            candidate = Candidate(
                index=i,
                response=response,
                answer=answer,
                reasoning=reasoning
            )
            candidates.append(candidate)
            
            if verbose:
                print(f"  → Answer: {answer}")
            
        except Exception as e:
            if verbose:
                print(f"  → Error: {e}")
            # Still add a failed candidate so we know it failed
            candidates.append(Candidate(
                index=i,
                response=f"ERROR: {e}",
                answer=None,
                reasoning=""
            ))
        
        # Rate limit protection
        if i < n_candidates - 1:
            time.sleep(delay_between)
    
    return candidates


def analyze_candidates(candidates: List[Candidate]) -> Dict:
    """
    Analyze the diversity and agreement among candidates.
    
    Returns dict with:
        - unique_answers: set of distinct answers
        - agreement_ratio: fraction with most common answer
        - most_common: the most frequent answer
        - distribution: count of each answer
    """
    answers = [c.answer for c in candidates if c.answer is not None]
    
    if not answers:
        return {
            "unique_answers": set(),
            "agreement_ratio": 0.0,
            "most_common": None,
            "distribution": {}
        }
    
    # Count each answer
    distribution = {}
    for ans in answers:
        # Normalize for comparison
        ans_norm = ans.lower().strip()
        distribution[ans_norm] = distribution.get(ans_norm, 0) + 1
    
    # Find most common
    most_common = max(distribution.keys(), key=lambda x: distribution[x])
    agreement_ratio = distribution[most_common] / len(answers)
    
    return {
        "unique_answers": set(distribution.keys()),
        "agreement_ratio": agreement_ratio,
        "most_common": most_common,
        "distribution": distribution,
        "total_valid": len(answers),
        "total_generated": len(candidates)
    }


def generate_and_analyze(
    problem: str,
    n_candidates: int = 5,
    temperature: float = 0.8,
    verbose: bool = True
) -> Dict:
    """
    Generate candidates and analyze them in one call.
    
    Returns dict with candidates and analysis.
    """
    candidates = generate_candidates(
        problem=problem,
        n_candidates=n_candidates,
        temperature=temperature,
        verbose=verbose
    )
    
    analysis = analyze_candidates(candidates)
    
    if verbose:
        print()
        print("=" * 50)
        print("ANALYSIS")
        print("=" * 50)
        print(f"Unique answers: {len(analysis['unique_answers'])}")
        print(f"Distribution: {analysis['distribution']}")
        print(f"Most common: {analysis['most_common']}")
        print(f"Agreement: {analysis['agreement_ratio']*100:.0f}%")
    
    return {
        "candidates": candidates,
        "analysis": analysis
    }


if __name__ == "__main__":
    # Test on the soccer/basketball problem
    from .problems import get_problem_by_id
    
    problem = get_problem_by_id("math_006")
    print(f"Testing on: {problem['id']}")
    print(f"Correct answer: {problem['answer']}")
    print()
    
    result = generate_and_analyze(
        problem=problem["problem"],
        n_candidates=5,
        temperature=0.8
    )
    
    print()
    print("Candidates generated:", len(result["candidates"]))
    for c in result["candidates"]:
        print(f"  [{c.index}] {c.answer}")
