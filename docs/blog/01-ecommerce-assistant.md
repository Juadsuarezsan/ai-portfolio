# Building a conversational e-commerce assistant that doesn't suck at retrieval

Most AI engineering portfolios show a single-pass RAG over a paragraph of FAQ
content and call it a day. Production conversational commerce — Rappi, Mercado
Libre, Walmart, Instacart, Amazon — looks nothing like that. The system has to
nail four things at once:

1. Find the right product among 50K SKUs given fuzzy natural-language queries.
2. Carry conversation state across turns ("add the second one to my cart").
3. Decide when *not* to answer: refund requests over $100, sensitive
   categories, explicit escalation.
4. Stay fast and cheap enough to serve at scale (think $0.01 per turn, not $0.10).

This is what Project 1 of my portfolio attacks.

## The retrieval problem

The naive answer is "embed everything, cosine search, top 5, done." Try that
on a query like *"healthy breakfast for kids"* against a real product catalog
and you'll get cereal AND oatmeal AND granola bars AND yogurt — but also
adult protein shakes that happen to have a child mascot, baby formula, and an
oddly-relevant box of paperclips.

What actually works in production is **hybrid retrieval**:

- **BM25** for the exact-keyword half — picks up brand names ("Heinz"), SKU
  codes, exact-volume phrasing ("397 grams").
- **Dense vector search** for semantic intent — picks up *"healthy"* even
  when no product name contains the word.
- **Reciprocal Rank Fusion** to merge the two ranked lists. No learnable
  weights, no tuning headache, robust by construction.
- **Cross-encoder reranking** on top 20 → top 5. This is the cheap step that
  buys real precision gains because the cross-encoder sees query AND
  document jointly, not separately.

In the eval harness I built, hybrid + reranking beats either component alone
on every metric — Precision@5, Recall@10, MRR, nDCG@10.

## The conversation problem

A real customer says *"two of the second one please"* and expects the system
to know that "the second one" refers to the second product in the previous
turn's results. The system needs:

- Per-session state (cart contents, last shown products)
- An intent router that doesn't conflate "search again" with "act on a prior
  result"
- Explicit handlers for cart_op / order_status / refund / escalate

LangGraph maps cleanly to this: each node is a typed transition, the state
type is one TypedDict per project, and you can render the graph as a diagram
your manager can actually read.

## The escalation problem

The most production-correct part of the system is also the boring part. Any
refund over $100, any sensitive department (alcohol, tobacco, pharmacy,
babies), and any explicit user request all force escalation. The agent
never tries to handle a borderline case "on confidence" — the policy is
written in code in `refund_handler.py`:

```python
def evaluate_refund(*, total_usd, department, threshold_usd):
    if total_usd > threshold_usd:
        return RefundDecision(requires_escalation=True, ...)
    if department.lower() in SENSITIVE_DEPARTMENTS:
        return RefundDecision(requires_escalation=True, ...)
    return RefundDecision(can_auto_process=True, ...)
```

A human reviewing this in 6 months can audit the policy without reading
prompt strings.

## Cost & latency

| Step | Latency | Cost |
|---|---|---|
| Intent router (Claude) | ~600 ms | $0.0008 |
| Hybrid retrieval | ~150 ms | $0 (local) |
| Reranking | ~80 ms | $0.001 (Cohere) |
| Synthesizer (Claude) | ~1200 ms | $0.004 |
| **Total** | **~2 s** | **~$0.006** |

At a 50¢-per-conversation budget and an average of 3 turns, the unit
economics work. That's the level of math hiring managers want to see, not
the GitHub stars.

## What's next

Real Instacart data (instead of the 280-product synthetic catalog), 100
hand-labeled eval queries (instead of 30), and a real Streamlit Cloud
deployment so anyone can poke at it without cloning. Code lives at
[github.com/Juadsuarezsan/ai-portfolio/01-ecommerce-assistant](https://github.com/Juadsuarezsan/ai-portfolio).
