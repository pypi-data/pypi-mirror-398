"""
Baseline evaluation for ARES.
Runs single-shot LLM inference on all problems and records results.
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from .llm import get_provider
from .problems import ALL_PROBLEMS


BASELINE_PROMPT_TEMPLATE = """Solve this problem step by step. Show your reasoning, then give your final answer.

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
            # Clean up common formatting
            answer = answer.rstrip(".")
            return answer
    return None


def normalize_answer(answer: str) -> str:
    """Normalize answer for comparison."""
    if answer is None:
        return ""
    answer = answer.lower().strip()
    # Remove common punctuation
    answer = answer.replace(",", "").replace("$", "").replace("%", "")
    return answer


def check_answer(predicted: str, expected: str) -> bool:
    """Check if predicted answer matches expected."""
    pred_norm = normalize_answer(predicted)
    exp_norm = normalize_answer(expected)
    
    # Exact match
    if pred_norm == exp_norm:
        return True
    
    # Try numeric comparison
    try:
        pred_num = float(pred_norm.replace(" ", ""))
        exp_num = float(exp_norm.replace(" ", ""))
        return abs(pred_num - exp_num) < 0.01
    except:
        pass
    
    # Check if expected is contained in predicted
    if exp_norm in pred_norm:
        return True
    
    return False


def run_baseline(num_runs: int = 3, problems: list = None, verbose: bool = True):
    """
    Run baseline evaluation.
    
    Args:
        num_runs: Number of runs per problem (to measure variance)
        problems: List of problems to evaluate (default: all)
        verbose: Print progress
    
    Returns:
        Dictionary with results
    """
    if problems is None:
        problems = ALL_PROBLEMS
    
    provider = get_provider()
    if not provider.is_available():
        raise RuntimeError("No LLM provider available. Check your .env configuration.")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "num_runs": num_runs,
        "provider": provider.__class__.__name__,
        "problems": []
    }
    
    total_correct = 0
    total_attempts = 0
    
    for problem in problems:
        if verbose:
            print(f"\n{'='*60}")
            print(f"Problem: {problem['id']} (difficulty: {problem['difficulty']})")
            print(f"{'='*60}")
        
        problem_result = {
            "id": problem["id"],
            "type": problem["type"],
            "difficulty": problem["difficulty"],
            "expected_answer": problem["answer"],
            "runs": []
        }
        
        correct_count = 0
        
        for run_idx in range(num_runs):
            if verbose:
                print(f"\n--- Run {run_idx + 1}/{num_runs} ---")
            
            prompt = BASELINE_PROMPT_TEMPLATE.format(problem=problem["problem"])
            
            start_time = time.time()
            try:
                response = provider.generate(prompt, temperature=0.7)
                elapsed = time.time() - start_time
                
                predicted = extract_answer(response)
                is_correct = check_answer(predicted, problem["answer"])
                
                if is_correct:
                    correct_count += 1
                    total_correct += 1
                
                total_attempts += 1
                
                run_result = {
                    "run_idx": run_idx,
                    "response": response,
                    "predicted_answer": predicted,
                    "is_correct": is_correct,
                    "elapsed_seconds": elapsed
                }
                problem_result["runs"].append(run_result)
                
                if verbose:
                    print(f"Predicted: {predicted}")
                    print(f"Expected:  {problem['answer']}")
                    print(f"Correct:   {'✓' if is_correct else '✗'}")
                    print(f"Time:      {elapsed:.2f}s")
                    
            except Exception as e:
                if verbose:
                    print(f"Error: {e}")
                problem_result["runs"].append({
                    "run_idx": run_idx,
                    "error": str(e)
                })
                total_attempts += 1
        
        problem_result["accuracy"] = correct_count / num_runs
        problem_result["variance"] = correct_count != num_runs  # Did results vary?
        
        results["problems"].append(problem_result)
        
        if verbose:
            print(f"\nProblem accuracy: {correct_count}/{num_runs} = {problem_result['accuracy']*100:.1f}%")
    
    # Summary
    results["summary"] = {
        "total_problems": len(problems),
        "total_attempts": total_attempts,
        "total_correct": total_correct,
        "overall_accuracy": total_correct / total_attempts if total_attempts > 0 else 0,
        "problems_with_variance": sum(1 for p in results["problems"] if p["variance"])
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print("BASELINE SUMMARY")
        print(f"{'='*60}")
        print(f"Overall accuracy: {results['summary']['overall_accuracy']*100:.1f}%")
        print(f"Problems with variance: {results['summary']['problems_with_variance']}/{len(problems)}")
    
    return results


def save_results(results: dict, output_path: str = None):
    """Save results to JSON file."""
    if output_path is None:
        output_path = f"results/baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return output_path


if __name__ == "__main__":
    print("ARES Baseline Evaluation")
    print("=" * 60)
    
    results = run_baseline(num_runs=3)
    output_path = save_results(results)
    print(f"\nResults saved to: {output_path}")
