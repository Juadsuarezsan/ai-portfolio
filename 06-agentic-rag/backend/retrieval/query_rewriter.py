"""Query rewriters — Claude prod path + deterministic offline stub."""
from __future__ import annotations


class QueryRewriter:
    """
    Claude generates `n` alternative phrasings of the query.
    Goal: surface chunks that match the question's intent even when the
    user's wording differs from the document's vocabulary.
    """

    SYSTEM_PROMPT = """You are a query-rewriting agent. Given a user question,
return exactly N alternative phrasings as a JSON array of strings.
Make the rewrites lexically diverse: vary domain vocabulary, level of formality,
and granularity. Do NOT answer the question — only rephrase it.

Output: ["...", "...", "..."]"""

    def __init__(self, *, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    async def rewrite(self, query: str, n: int = 3) -> list[str]:
        if not self.api_key or not self.model:
            return StubQueryRewriter().rewrite_sync(query, n)
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage
        import json
        chat = ChatAnthropic(model=self.model, api_key=self.api_key, temperature=0.4, max_tokens=400)
        resp = await chat.ainvoke([
            SystemMessage(content=self.SYSTEM_PROMPT.replace("N", str(n))),
            HumanMessage(content=query),
        ])
        text = resp.content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        return json.loads(text)[:n]


class StubQueryRewriter:
    """Deterministic alternative phrasings — replaces content words with stand-in synonyms."""

    SYNONYMS = {
        "cost": ["price", "expense"],
        "latency": ["delay", "response time"],
        "graphrag": ["graph rag", "knowledge graph rag"],
        "rerank": ["reranking", "cross encoder"],
        "dedup": ["deduplication", "merge duplicates"],
        "memory": ["state", "persistence"],
        "what is": ["definition of", "describe"],
    }

    def rewrite_sync(self, query: str, n: int = 3) -> list[str]:
        out: list[str] = []
        lower = query.lower()
        for term, alts in self.SYNONYMS.items():
            if term in lower:
                for alt in alts:
                    candidate = lower.replace(term, alt)
                    if candidate not in out and candidate != lower:
                        out.append(candidate)
                    if len(out) >= n:
                        return out
        if not out:
            stripped = query.rstrip("?.!")
            out = [query.lower(), stripped, stripped + " — definition"]
        return out[:n]

    async def rewrite(self, query: str, n: int = 3) -> list[str]:
        return self.rewrite_sync(query, n)
