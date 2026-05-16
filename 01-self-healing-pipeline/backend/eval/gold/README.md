# Gold Set — Critic Calibration

Hand-labeled cases used by `python -m eval.calibrate` to measure critic-vs-human
agreement (Cohen's κ). The current seed is **5 cases**; the design target in the
project README is **50**. Add more by dropping new `case_XXX.json` files here.

## Mix in the seed

| Case | Type | What fails (human's view) |
|------|------|----------------------------|
| case_001 | invoice | nothing — clean pass |
| case_002 | invoice | accuracy — single-digit tax_id error |
| case_003 | invoice | completeness — missing currency field |
| case_004 | invoice | consistency + accuracy — total ≠ subtotal + tax |
| case_005 | invoice | format — non-ISO date string |

The mix is deliberate: each principle has at least one case where it is
expected to fire. A critic that *never* fails a principle still gets
the principle's κ pushed down by these cases.

## Schema

See `backend/eval/schemas.py` (`GoldCase`). Required fields:

```jsonc
{
  "id": "case_NNN",
  "document_type": "invoice | contract | purchase_order | receipt | generic",
  "content": "raw document text the extractor would see",
  "extraction": { ... what the extractor produced ... },
  "structural_check": { "sum_matches_total": true, "line_items_present": true },
  "human_verdict": {
    "principles": {
      "completeness": { "score": 0.0–1.0, "notes": "..." },
      "accuracy":     { "score": 0.0–1.0, "notes": "..." },
      "consistency":  { "score": 0.0–1.0, "notes": "..." },
      "format":       { "score": 0.0–1.0, "notes": "..." }
    },
    "overall_pass": true | false,
    "reviewer": "initials",
    "reviewed_at": "YYYY-MM-DD"
  }
}
```

`overall_pass` is the reviewer's gestalt verdict — it does **not** have to
equal `mean(scores) >= pass_threshold`. The calibrator compares it directly
to the critic's `passes` boolean.

## When to add cases

- After any production failure that the critic *missed*: codify it as a case
  with the correct verdict so future critic regressions are caught.
- After any disagreement reviewed from the `critic_disagreements` table where
  the human-was-right: promote that row into a gold case here.
- Quarterly: re-balance the distribution across document types and failure
  principles so no principle is under-represented.

## What NOT to do

- Don't include PII. Use realistic-but-synthetic vendors and IDs.
- Don't let `mean(human_scores) > threshold` and `overall_pass = false` drift
  apart without a `notes` explaining why — that's the kind of inconsistency
  that pollutes κ.
- Don't let one principle dominate (>70% of cases failing the same principle).
  Cohen's κ is sensitive to imbalanced marginals.
