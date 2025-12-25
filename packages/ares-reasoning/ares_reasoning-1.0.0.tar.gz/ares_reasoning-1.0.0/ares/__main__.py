"""
ARES Command Line Interface

Usage:
    python -m ares solve "Your problem here"
    python -m ares solve --problem "Your problem here" --candidates 5
    python -m ares test                    # Run on built-in test problems
    python -m ares info                    # Show framework info

This CLI calls the ARES framework - no duplicated logic.
"""

import argparse
import sys
import time

from .search import AresSearch
from .problems import get_problem_by_id, ALL_PROBLEMS


def cmd_solve(args):
    """Solve a problem using ARES."""
    
    problem = args.problem
    if not problem:
        print("Error: No problem provided")
        print("Usage: python -m ares solve \"Your math problem here\"")
        sys.exit(1)
    
    print("=" * 60)
    print("ares v1 - Inference-Time Reasoning")
    print("=" * 60)
    print()
    print(f"Problem: {problem}")
    print(f"Candidates: {args.candidates}")
    print(f"Type: {args.type}")
    print()
    
    # Call the framework
    ares = AresSearch(n_candidates=args.candidates, temperature=args.temperature)
    
    print("Generating candidates...")
    result = ares.search(
        problem=problem,
        problem_type=args.type,
        verbose=not args.quiet
    )
    
    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)
    print()
    print(f"Answer: {result.predicted_answer}")
    print(f"Confidence: {result.best_score:.0%}")
    print(f"Candidates generated: {result.num_candidates}")
    print(f"Time: {result.elapsed_seconds:.1f}s")
    print()
    
    if args.verbose:
        print("Scoring breakdown:")
        for score in result.all_scores:
            print(f"  '{score['answer']}': votes={score['vote_count']}, "
                  f"confidence={score['confidence']:.0%}, "
                  f"combined={score['combined_score']:.2f}")


def cmd_test(args):
    """Run ARES on built-in test problems."""
    
    print("=" * 60)
    print("ARES v1 - Running Test Suite")
    print("=" * 60)
    print()
    
    # Select problems
    if args.id:
        problem = get_problem_by_id(args.id)
        if not problem:
            print(f"Error: Problem '{args.id}' not found")
            print(f"Available: {[p['id'] for p in ALL_PROBLEMS]}")
            sys.exit(1)
        problems = [problem]
    else:
        # Default: first 3 problems (quick test)
        problems = ALL_PROBLEMS[:3]
    
    print(f"Testing on {len(problems)} problem(s)...")
    print()
    
    ares = AresSearch(n_candidates=args.candidates, temperature=0.8)
    
    correct = 0
    total = 0
    
    for problem in problems:
        print(f"--- {problem['id']} ---")
        print(f"Problem: {problem['problem'][:60]}...")
        print(f"Expected: {problem['answer']}")
        
        result = ares.search(
            problem=problem["problem"],
            problem_type=problem["type"],
            expected_answer=problem["answer"],
            problem_id=problem["id"],
            verbose=False
        )
        
        total += 1
        if result.is_correct:
            correct += 1
            print(f"ARES: {result.predicted_answer} ✓")
        else:
            print(f"ARES: {result.predicted_answer} ✗")
        
        print()
    
    print("=" * 60)
    print(f"ARES Accuracy: {correct}/{total} ({correct/total*100:.0f}%)")
    print(f"Baseline (single-shot): ~27%")
    print("=" * 60)


def cmd_info(args):
    """Show ARES framework information."""
    
    print("""
ARES v1 - Inference-Time Reasoning Framework
=============================================

What is ARES?
  ARES wraps an existing LLM with search + verification
  to improve accuracy on reasoning tasks.

Components:
  - generator.py   : Multi-candidate generation
  - verifier.py    : Rule-based verification
  - search.py      : Beam search (voting + verification)
  - llm.py         : LLM provider abstraction

Usage:
  python -m ares solve "Your problem here"
  python -m ares test
  python -m ares test --id math_006
  python -m ares info

Results:
  Baseline accuracy: ~27%
  ARES accuracy:     ~80%+

The tradeoff: 10x compute for 3x accuracy.

License: MIT
""")


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        prog="ares",
        description="ARES - Inference-Time Reasoning Framework"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # solve command
    solve_parser = subparsers.add_parser("solve", help="Solve a problem")
    solve_parser.add_argument("problem", nargs="?", help="The problem to solve")
    solve_parser.add_argument("-p", "--problem", dest="problem_flag", help="Problem (alternative)")
    solve_parser.add_argument("-n", "--candidates", type=int, default=5, help="Number of candidates (default: 5)")
    solve_parser.add_argument("-t", "--type", choices=["math", "logic"], default="math", help="Problem type")
    solve_parser.add_argument("--temperature", type=float, default=0.8, help="LLM temperature")
    solve_parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output")
    solve_parser.add_argument("-v", "--verbose", action="store_true", help="Detailed output")
    
    # test command
    test_parser = subparsers.add_parser("test", help="Run on test problems")
    test_parser.add_argument("--id", help="Specific problem ID to test")
    test_parser.add_argument("-n", "--candidates", type=int, default=5, help="Number of candidates")
    
    # info command
    info_parser = subparsers.add_parser("info", help="Show framework info")
    
    args = parser.parse_args()
    
    # Handle problem from flag if not positional
    if hasattr(args, 'problem_flag') and args.problem_flag and not args.problem:
        args.problem = args.problem_flag
    
    if args.command == "solve":
        cmd_solve(args)
    elif args.command == "test":
        cmd_test(args)
    elif args.command == "info":
        cmd_info(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
