from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    person = "person"
    organization = "organization"
    project = "project"
    concept = "concept"
    event = "event"
    document = "document"
    date = "date"
    amount = "amount"


class Entity(BaseModel):
    id: str = Field(..., description="Stable id — slugified canonical name")
    name: str
    type: EntityType
    properties: dict[str, Any] = Field(default_factory=dict)
    aliases: list[str] = Field(default_factory=list)


class Relationship(BaseModel):
    source_id: str
    target_id: str
    type: str = Field(..., description="UPPER_SNAKE_CASE relation, e.g. WORKS_ON, OWNS, DEPENDS_ON")
    properties: dict[str, Any] = Field(default_factory=dict)


class ExtractedKnowledge(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]


class EntityExtractor:
    """
    Calls Claude with a strict system prompt to extract entities and relationships
    from a document chunk. Returns ExtractedKnowledge (Pydantic-validated).
    """

    SYSTEM_PROMPT = """You extract structured knowledge from business documents.
Return ONLY a JSON object matching this schema:
{
  "entities": [
    {"id": "alice-johnson", "name": "Alice Johnson", "type": "person",
     "properties": {"role": "CTO"}, "aliases": ["A. Johnson"]}
  ],
  "relationships": [
    {"source_id": "alice-johnson", "target_id": "project-atlas",
     "type": "OWNS", "properties": {"since": "2024-03-01"}}
  ]
}

Rules:
- entity.id = lowercase, dash-separated, deterministic across documents.
- Use existing ids if the entity is the same person/org/project — do not duplicate.
- relationship.type = UPPER_SNAKE_CASE verb phrase.
- Skip entities you cannot ground in the text.
"""

    def __init__(self, *, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    async def extract(self, *, document_text: str, document_id: str) -> ExtractedKnowledge:
        """Production path. Calls Claude with the strict system prompt."""
        if not self.api_key or not self.model:
            raise RuntimeError("EntityExtractor.extract requires model + api_key. Use extract_stub for offline.")
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage
        import json
        chat = ChatAnthropic(model=self.model, api_key=self.api_key, temperature=0, max_tokens=2048)
        resp = await chat.ainvoke([
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=f"<document id={document_id}>\n{document_text}\n</document>"),
        ])
        text = resp.content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        raw = json.loads(text)
        return ExtractedKnowledge(**raw)

    @staticmethod
    def extract_stub(*, structured: dict) -> ExtractedKnowledge:
        """Offline path: caller supplies the already-extracted structure (e.g. from a fixture)."""
        return ExtractedKnowledge(**structured)
