# Triaging customer support tickets: combining a cheap classifier with an expensive reasoner

Customer support is the use case that pays Intercom, Zendesk, Freshdesk and
HubSpot's bills. The pattern is universal: a ticket arrives, the company has
five minutes to react, and 60% of those tickets are already-solved problems
with already-documented resolutions. You don't need ChatGPT for those. You
need a system that recognizes them, drafts the answer in your voice, and
escalates the 40% that genuinely require a human.

Project 2 of my portfolio is exactly this triage system.

## The two-model trick

A classifier that knows 27 intent labels is cheap, fast, and good enough on
80% of tickets — *if* you train it on the right data. The Bitext customer
support dataset (27K tickets pre-labeled) plus LoRA fine-tuning on
DistilBERT-base gets you to ~92% macro-F1 with about 20 minutes of GPU.
DistilBERT inference runs locally in ~30 ms per ticket, no API call needed.

But you can't ship a classifier alone. The other 20% of tickets — the angry
ones, the bug reports, the cross-cutting refund-plus-shipping-question
multi-intent cases — need reasoning. That's where Claude comes in, but only
for the priority/sentiment scoring step and the response drafter.

The combined architecture:

```
Ticket → DistilBERT intent classifier (30ms, $0)
       → Claude priority+sentiment+urgency (1s, $0.002)
       → Qdrant similar-ticket retrieval (50ms, $0)
       → Claude drafter (1.2s, $0.004, grounded in similar resolutions)
       → Decision: auto-resolve / suggest / escalate (deterministic rules)
```

Total per ticket: ~2.5s, ~$0.006. That's an order of magnitude cheaper than
"throw the whole ticket at GPT-4 with a 2000-token prompt."

## The decision logic — the part that actually matters

The thing that makes this system production-deployable isn't the model
quality. It's the **decision logic** that decides whether the system handles
the ticket itself or hands it to a human. From `triage_decision.py`:

```python
# Hard rules first — never auto-resolve these
if top_intent in ("complaint", "contact_human_agent"):
    return TriageDecision(decision="escalate", ...)
if urgency_score >= 0.9:
    return TriageDecision(decision="escalate", ...)

# Then the confidence-band routing
score = 0.5*intent_conf + 0.4*similarity + 0.1 - penalty
if score >= 0.85: return "auto_resolve"
if score < 0.60:  return "escalate"
return "suggest"
```

Three things this gets right:
1. **Hard rules beat any soft scoring** for the cases where the cost of
   being wrong is asymmetric. A complaint that gets auto-resolved is a
   churn event.
2. **Negative sentiment penalizes confidence**. The system is more cautious
   with an angry customer than a neutral one.
3. **The "suggest" band exists**. A human reviewer sees the draft + the
   confidence score and clicks accept/edit. This is where 60% of real
   support teams actually land — not full auto, not full manual.

## The fine-tune part you can't skip

If you don't fine-tune the classifier and rely on zero-shot Claude for
intent, you'll spend ~$0.003 per ticket and run at ~1.5s. Multiply by 100K
monthly tickets = $300/mo just for intent classification.

A LoRA fine-tune on DistilBERT runs in 20 min on a Colab T4, drops cost to
near-zero, and publishes cleanly to HuggingFace Hub as a model card. That
artifact alone — a model card with benchmarks against 3 baselines, training
config, and a confusion matrix — is the kind of thing that ends up on
your CV.

## What's next

Run the LoRA fine-tune (notebook in repo), publish the model to HF Hub,
deploy the Next.js Kanban frontend to Vercel, run the full 200-conversation
eval over Twitter Customer Support data. Code at
[github.com/Juadsuarezsan/ai-portfolio/02-support-triage](https://github.com/Juadsuarezsan/ai-portfolio).
