# ARES - Inference-Time Reasoning Framework

**ARES** improves LLM accuracy on complex reasoning tasks through explicit search and verification.

> Trade compute for correctness. No training required.

## What is ARES?

ARES wraps an existing open-source LLM (Llama, Mixtral, etc.) with:

1. **Multi-candidate generation** - Generate N reasoning paths instead of 1
2. **Rule-based verification** - Reject bad reasoning steps
3. **Beam search** - Use voting + verification to select the best answer

```
Single LLM:         Problem → LLM → Answer (often wrong)

ARES:               Problem → LLM → [5 candidates]
                                  ↓
                            [Verify each]
                                  ↓
                          [Vote + Score]
                                  ↓
                         Best answer (usually right)
```

## Results

| Method | Accuracy | Time |
|--------|----------|------|
| Baseline (single-shot) | 27% | ~10s |
| ARES v1 (5 candidates) | ~80%+ | ~3min |

**The tradeoff: 10x more compute → 3x better accuracy**

## Quick Start

```bash
# 1. Clone and setup
cd ares
pip install -r requirements.txt

# 2. Configure LLM (OpenRouter or Ollama)
cp .env.example .env
# Edit .env with your API key

# 3. Run ARES via CLI
python -m ares solve "What is 15% of 240?"
```

## CLI Usage

```bash
# Solve a problem
python -m ares solve "Your math problem here"

# Solve with options
python -m ares solve "Problem text" --candidates 5 --type math

# Run built-in tests
python -m ares test

# Test specific problem
python -m ares test --id math_006

# Show framework info
python -m ares info
```

## Framework Usage (for developers)

```python
from ares.search import AresSearch

# Create ARES instance
ares = AresSearch(n_candidates=5, temperature=0.8)

# Run on a problem
result = ares.search(
    problem="In a class of 30 students, 18 play soccer...",
    problem_type="math"
)

print(f"ARES answer: {result.predicted_answer}")
print(f"Confidence: {result.best_score:.0%}")
```

## Project Structure

```
ares/
├── ares/
│   ├── llm.py          # LLM provider (Ollama/OpenRouter)
│   ├── generator.py    # Multi-candidate generation
│   ├── verifier.py     # Rule-based verification
│   ├── search.py       # ARES beam search
│   └── problems.py     # Evaluation problems
├── docs/
│   ├── design.md       # Design document
│   ├── eval_tasks.md   # Evaluation tasks
│   └── twitter_posts.md # Build in public posts
├── results/            # Evaluation results
└── test_*.py           # Test scripts
```

## How It Works

### Phase 1: Baseline shows LLMs fail
Single-shot inference on reasoning problems: **27% accuracy**

### Phase 2: Generate multiple candidates
Instead of 1 answer, generate 5. See diversity in responses.

### Phase 3: Verify each candidate
Rule-based checks:
- Is answer a valid number?
- Does reasoning contain math steps?
- Does LLM express self-doubt ("doesn't make sense")?

### Phase 4: Beam search with voting
Combine verification confidence with voting consensus:
```
combined_score = confidence × vote_percentage
```

Pick the answer with highest combined score.

## Limitations (v1)

- **Not real beam search over steps** - We generate complete answers, not step-by-step search
- **Rule-based verifier only** - No learned verification model
- **Slow** - 5 candidates × API latency = minutes per problem
- **Rate limits** - Free API tiers are limiting
- **Math/logic only** - Tested on GSM8K-style problems

## What ARES is NOT

- ❌ A new foundation model
- ❌ A fine-tuned model
- ❌ AGI
- ❌ Guaranteed to be correct
- ❌ Comparable to GPT-4/o1

## v2 Roadmap (Future)

- Monte Carlo Tree Search
- Learned value functions
- Step-by-step reasoning search
- Tool use inside search
- Self-improving verifier

## License

MIT

## Credits

Built in public as a learning project to understand inference-time reasoning.
