# Portafolio AI Engineer — Specs Completas y Definition of Done

Documento maestro de especificaciones técnicas para nueve proyectos profundos orientados a roles de AI Engineer mid-senior en industria. Cubre el noventa y nueve por ciento del territorio de AI Engineering en 2026: RAG, fine-tuning, agentes, Document AI, multimodal, Computer Use, Code AI, AI Safety, GraphRAG y Voice AI. Cada proyecto está diseñado para entregarse a Claude Code como brief técnico completo.

**Stack base común**:

- Python 3.11+
- LangChain 0.3+ y LangGraph 0.2+
- Anthropic Claude Sonnet 4.5 como LLM principal
- FastAPI 0.115+ para backends
- PostgreSQL 16 + pgvector para estado y audit
- Docker + Docker Compose para reproducibilidad
- LangSmith o Langfuse para observability
- Pytest + pytest-cov para tests
- Ruff + Black para linting y formato
- mypy para verificación de tipos
- GitHub Actions para CI

Demos visuales hechas con **Claude Design** (claude.ai/design) y exportadas como HTML estático al repo.

---

# DEFINITION OF DONE — Checklist universal para cada proyecto

Este checklist es el criterio de aceptación obligatorio para considerar cualquier proyecto del portafolio terminado. Claude Code y agentes similares de implementación tienen el sesgo de declarar tareas completas cuando el código apenas funciona en el camino feliz. Esto existe para forzar verificación real. **Ningún proyecto se declara listo hasta que pasa los doce bloques siguientes con evidencia verificable.**

## Bloque 1 — Calidad de código y arquitectura

- [ ] Estructura de carpetas implementada según el spec del proyecto correspondiente
- [ ] Type hints en el cien por ciento del código Python, verificado con `mypy --strict src/` sin errores
- [ ] Docstrings en todas las funciones públicas, clases y módulos, en estilo Google o NumPy consistente
- [ ] Separación de capas implementada: configuración separada del dominio, dominio separado del I/O, I/O separado de la API HTTP
- [ ] Configuración externalizada en variables de entorno, con archivo `.env.example` documentado y `.env` en gitignore
- [ ] Cero secretos hardcodeados, verificado con `gitleaks detect --no-banner` sin findings
- [ ] Manejo explícito de errores: cero `except:` o `except Exception:` sin re-raise, cero silent failures
- [ ] Logging estructurado implementado con `loguru` o `structlog`, cero `print()` en código de producción
- [ ] Archivo `requirements.txt` con versiones pinneadas exactas (`==`, no `>=`) o `pyproject.toml` con `uv` o `poetry`
- [ ] Versión de Python declarada en `pyproject.toml` o `.python-version` y verificada (recomendado 3.11+)
- [ ] Timeouts explícitos en todas las llamadas a APIs externas, sin defaults infinitos
- [ ] Retries con exponential backoff implementados con `tenacity` para llamadas a LLM y APIs externas
- [ ] Cero código comentado de prueba, cero `TODO` sin issue de GitHub asociado, cero `print('debug')` olvidados

## Bloque 2 — Testing

- [ ] Tests unitarios para cada módulo de dominio principal (no para I/O)
- [ ] Al menos un test de integración end-to-end que cubra el flujo principal del proyecto
- [ ] Coverage mínimo del setenta por ciento medido con `pytest --cov=src --cov-report=term-missing`
- [ ] Tests deterministas: random seeds fijos declarados en `tests/conftest.py`
- [ ] Mocks de Claude API, vector DB y otras dependencias externas implementados con `pytest-mock` o `responses`
- [ ] Fixtures reutilizables centralizadas en `tests/conftest.py`, no duplicadas entre archivos
- [ ] Al menos tres tests de casos edge documentados: input vacío, input oversized, input malformed
- [ ] GitHub Actions workflow `.github/workflows/ci.yml` corriendo tests en cada push a main y en PRs
- [ ] CI también corre `ruff check`, `black --check`, y `mypy --strict`
- [ ] Badge de CI status visible en el README

## Bloque 3 — Datos y reproducibilidad de datos

- [ ] Script `scripts/download_data.py` que descarga el dataset original con un solo comando
- [ ] URL exacta del dataset original declarada en el README con su licencia
- [ ] Schema del dataset documentado en `docs/data_schema.md` con tipos, rangos y descripciones por columna
- [ ] Preprocessing reproducible: comando único regenera los datos procesados desde los crudos
- [ ] Train/val/test splits con random seed fijo declarado y commiteado
- [ ] Versionamiento de datos: hash SHA-256 del dataset procesado guardado en `data/MANIFEST.txt`
- [ ] Si el dataset crudo pesa más de cien megabytes, está en `.gitignore` con instrucciones claras de descarga
- [ ] Datos sintéticos generados con LLM están marcados explícitamente, no mezclados con reales sin etiqueta

## Bloque 4 — Evaluación rigurosa

- [ ] Eval set construido con tamaño mínimo declarado en la spec del proyecto, típicamente cien o más casos
- [ ] Ground truth construido manualmente o validado contra fuente confiable, no generado sintéticamente sin verificación humana
- [ ] Métricas usadas son estándar de la industria del proyecto (RAGAS para RAG, F1 macro para classification, WER para voz, etcétera), no métricas custom sin justificación
- [ ] Al menos dos baselines comparados: típicamente zero-shot LLM sin tu pipeline, y al menos una alternativa razonable como no-AI o single-pass
- [ ] Al menos un ablation study sobre el componente principal del sistema, mostrando contribución incremental
- [ ] Resultados publicados en tabla comparativa en el README con todos los baselines
- [ ] Análisis de errores escrito: los diez casos donde el sistema falla peor, con hipótesis de la causa
- [ ] Si usás LLM-as-judge: rubrica explícita declarada en código con criterios numerados y ejemplos, no instrucciones vagas tipo "rate from 1 to 10"
- [ ] Resultados reproducibles: `python -m eval.run` regenera la tabla exacta sin intervención manual
- [ ] Latencia y costo medidos y reportados, no solo accuracy

## Bloque 5 — Observability

- [ ] Logging estructurado configurado con niveles correctos (DEBUG, INFO, WARNING, ERROR)
- [ ] LangSmith o Langfuse configurado y recibiendo traces de cada request
- [ ] Cada request loggea: trace_id único, latencia total, tokens de input y output, costo en dólares
- [ ] Dashboard de observability accesible mostrando últimas cien requests con métricas
- [ ] Traces públicas en LangSmith compartidas donde aplique: mínimo treinta ejemplos accesibles vía link público
- [ ] Para proyectos con agentes: cada nodo del grafo loggea su estado de entrada y salida

## Bloque 6 — Documentación del README

- [ ] README escrito desde cero, no contiene texto copiado del enunciado original ni de templates
- [ ] Sección "Qué hace este proyecto" explicada en dos o tres oraciones entendibles por no-técnicos
- [ ] Sección "Caso de uso industrial" explicando para qué tipo de empresa real esto sirve, con ejemplos concretos
- [ ] Sección "Arquitectura" con diagrama visual en PNG o SVG generado en Claude Design
- [ ] Sección "Métricas y resultados" con tabla comparativa contra baselines
- [ ] Sección "Quickstart" con tres a cinco comandos que permiten reproducir el proyecto desde cero
- [ ] Sección "Decisiones técnicas" justificando al menos cinco elecciones clave, por ejemplo por qué Qdrant y no Chroma, por qué DistilBERT y no BERT base, etcétera
- [ ] Sección "Limitaciones conocidas" honesta, enumera dónde el sistema falla o no escala
- [ ] Sección "Trabajo futuro" priorizado con tres a cinco mejoras planeadas
- [ ] GIF animado o screenshots del demo en uso embebidos en el README
- [ ] Link al deploy público destacado en la parte superior del README
- [ ] Badges de CI status, coverage, license y deploy status visibles
- [ ] Licencia declarada en archivo `LICENSE` separado (MIT o Apache 2.0 recomendado)

## Bloque 7 — Demo y deploy

- [ ] Demo deployada y accesible públicamente en URL persistente (HF Spaces, Vercel, Streamlit Cloud o Railway)
- [ ] Datos pre-cargados al abrir la página, el visitante ve algo de inmediato sin subir nada
- [ ] Al menos cinco queries o casos pre-baked accesibles con un click desde la UI
- [ ] Latencia p95 en producción medida y por debajo de diez segundos, idealmente por debajo de cinco
- [ ] Manejo de errores en frontend: spinner durante procesamiento, mensaje claro si algo falla
- [ ] UI con styling profesional, no Streamlit con tema default ni HTML sin CSS
- [ ] Responsive en mobile, probado en viewport de 375 píxeles de ancho
- [ ] Link prominente al repo de GitHub desde la demo y al revés

## Bloque 8 — Reproducibilidad de infraestructura

- [ ] `docker-compose up` levanta el stack completo con un solo comando, sin pasos manuales adicionales
- [ ] `.env.example` con todas las variables de entorno documentadas con su propósito
- [ ] Modelos LLM pinneados a versión específica usando IDs exactos como `claude-sonnet-4-5-20250929`, nunca `claude-latest` o sin versión
- [ ] Versiones de embeddings, rerankers y otras APIs pinneadas explícitamente
- [ ] Notebook `notebooks/demo.ipynb` que reproduce el flujo end-to-end con outputs visibles
- [ ] Comando único para correr evaluación completa, típicamente `make eval` o `python -m eval.run`
- [ ] Healthcheck endpoint en el API: `GET /health` devuelve 200 si el sistema está operativo

## Bloque 9 — Git y versionamiento

- [ ] Mínimo treinta commits con mensajes descriptivos siguiendo convenciones tipo Conventional Commits
- [ ] Branch `main` protegida en GitHub, todas las features llegan vía pull request
- [ ] Tag `v0.1.0` al primer milestone funcional, tag `v1.0.0` al release final
- [ ] Releases creadas en GitHub para cada tag con release notes explicando qué incluye
- [ ] Historia de git limpia, sin merge commits caóticos ni reverts sin explicar
- [ ] `.gitignore` cubre `__pycache__`, `.env`, `*.pyc`, `data/raw/`, `models/checkpoints/`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`
- [ ] Cero archivos binarios trackeados excepto fixtures pequeñas menores a un megabyte
- [ ] Cero archivos `.pickle`, `.bin`, `.parquet` grandes trackeados en el repo

## Bloque 10 — Seguridad y producción

- [ ] Secrets fuera del repo y fuera de logs, verificado con `gitleaks scan`
- [ ] Rate limiting implementado si la API está expuesta públicamente, usando `slowapi` para FastAPI
- [ ] Validación de inputs con Pydantic en todos los endpoints, devolviendo 422 con mensaje claro si falla
- [ ] Sanitización de outputs implementada si el sistema renderea HTML o markdown
- [ ] Si maneja PII: redacción automática implementada y validada con tests
- [ ] HTTPS forzado en deploy, manejado por la plataforma de hosting
- [ ] CORS configurado restrictivamente con origins específicos, nunca `*` en producción

## Bloque 11 — Performance básica

- [ ] Caching implementado donde tiene sentido: Redis para sesiones, in-memory para configuraciones
- [ ] `async/await` usado en endpoints I/O-bound de FastAPI
- [ ] Batch processing implementado para operaciones masivas como generación de embeddings o evaluación
- [ ] Connection pooling configurado para Postgres usando `asyncpg` o `psycopg3`
- [ ] Profiling básico documentado en `docs/performance.md`: dónde está el bottleneck principal y por qué

## Bloque 12 — Comunicación del proyecto

- [ ] Blog post o technical write-up de mínimo mil quinientas palabras publicado en Medium, Dev.to, o blog propio
- [ ] Post en LinkedIn anunciando el proyecto con link al repo y a la demo
- [ ] Si publicaste un modelo fine-tuneado: model card profesional en HuggingFace Hub con benchmarks, casos de uso, limitaciones y license
- [ ] Si publicaste un dataset curado: dataset card en HuggingFace Datasets con schema, splits y licencia
- [ ] Tu nombre completo, email profesional y link a LinkedIn declarados en el README

## Verificaciones anti-superficialidad

Antes de declarar el proyecto terminado, validar las siguientes preguntas con honestidad. Si la respuesta a cualquiera de ellas es "no" o "no sé", el proyecto **no** está listo independientemente de los checks anteriores.

- Una persona externa al proyecto, con perfil técnico similar al tuyo, puede clonar el repo y reproducir los resultados publicados siguiendo únicamente el README, sin pedirte ayuda y sin acceso a tu máquina
- Si en una entrevista te preguntan por qué elegiste la tecnología X sobre Y, tenés una respuesta documentada en el README o en `docs/decisions.md` con criterios concretos, no opiniones vagas
- Si te preguntan cuál es la mayor debilidad técnica del sistema, tenés una respuesta honesta documentada en la sección de limitaciones conocidas
- Si te preguntan cómo escalarías esto a cien veces más usuarios o documentos, tenés una respuesta razonada documentada en `docs/scalability.md`
- Si te preguntan cuánto costaría operar esto en producción con mil usuarios mensuales, tenés un cálculo aproximado documentado con supuestos explícitos
- Las métricas que reportás en el README las podés regenerar ahora mismo corriendo un comando, no fueron resultados de una corrida única no reproducible

Cada proyecto agrega además su propio bloque de criterios específicos al final de su sección, que se suma a este checklist universal.

---

# PROYECTO 1 — Conversational E-commerce Assistant

## Caso de uso

Asistente conversacional para un supermercado online. El cliente pregunta en lenguaje natural por productos, los agrega al carrito, gestiona devoluciones, y el sistema decide cuándo escalar a humano. Resuelve el caso de uso número uno de e-commerce conversational AI. Toda empresa B2C con catálogo grande lo necesita: Rappi, Mercado Libre, Walmart, Instacart, Amazon.

## Dataset

**Instacart Market Basket Analysis** (Kaggle, gratis, libre uso académico y de portfolio):

- URL: `https://www.kaggle.com/competitions/instacart-market-basket-analysis/data`
- 49.688 productos con campos `product_name`, `aisle`, `department`
- 3.4 millones de órdenes con `order_id`, `user_id`, `product_id`, `add_to_cart_order`
- Jerarquía de 21 departments con 134 aisles
- Licencia: uso libre para fines no comerciales

**Complemento opcional**: Open Food Facts (`https://world.openfoodfacts.org/data`) para datos nutricionales reales si querés agregar queries tipo "healthy breakfast".

## Stack técnico

- Vector DB principal: Qdrant 1.11+ corriendo en Docker
- Vector DB comparativos: pgvector 0.7+ y Chroma 0.5+
- Embeddings: Voyage AI `voyage-3` ($0.12 por millón de tokens) o `sentence-transformers/all-MiniLM-L6-v2` local gratis
- Reranker: Cohere Rerank v3 (`rerank-english-v3.0`, $1 por mil queries) o `cross-encoder/ms-marco-MiniLM-L-6-v2` local
- Búsqueda híbrida: rank-bm25 para sparse + dense vector + Reciprocal Rank Fusion
- LLM principal: Claude Sonnet 4.5 vía Anthropic API
- Orquestación: LangGraph con StateGraph
- Estado: PostgreSQL 16 para carts, orders, audit log
- Cache de sesión: Redis 7 con TTL configurable
- Frontend de demo: Streamlit Community Cloud
- Eval framework: RAGAS (`ragas` 0.2+)

## Arquitectura del flujo

```
Usuario pregunta
   │
   ▼
[Intent Router] Claude con structured output
   │ classifica entre: product_search | cart_op | order_status | refund | escalate
   │
   ├──► [Semantic Retriever]
   │      ├─ BM25 sobre product_name + aisle + department
   │      ├─ Dense vector search en Qdrant
   │      ├─ RRF fusion → top 20
   │      └─ Cohere rerank → top 5
   │
   ├──► [Structured Retriever] SQL sobre Postgres
   │      └─ filtros por precio, categoría, disponibilidad
   │
   ├──► [Cart Manager] Pydantic models stateful
   │      └─ add, remove, update_quantity, view, clear
   │
   ├──► [Refund Handler]
   │      └─ policy check, si valor > $100 USD o categoría sensible → escala
   │
   └──► [Synthesizer] Claude
          └─ respuesta con citas a productos específicos por product_id
```

## Métricas y evaluación

Construir manualmente `eval/queries.jsonl` con cien queries clasificados en cuatro categorías. Treinta queries de lookup directo del tipo "Heinz ketchup 397 gramos". Treinta queries semánticos del tipo "healthy breakfast for kids" o "lactose-free alternatives". Veinte queries comparativos del tipo "cheaper version of X" o "best rated cereals under $5". Veinte queries multi-turn que incluyen referencias a cart context de turnos anteriores. Para cada query, declarar la lista de `product_id` relevantes con score de relevance entre uno y tres.

**Métricas obligatorias**:

- Retrieval: Precision@5, Recall@10, MRR, nDCG@10
- RAG con RAGAS: Faithfulness, Answer Relevance, Context Precision, Context Recall
- Conversacional: Task completion rate medido con LLM-as-judge sobre cincuenta conversaciones simuladas, turn count promedio para completar tareas
- Sistema: Latencia p50 y p95, costo promedio por conversación en dólares

**Tabla comparativa obligatoria en README**:

| Vector DB | Precision@5 | Recall@10 | nDCG@10 | Latencia p95 | Costo/1K queries |
|---|---|---|---|---|---|
| Qdrant | | | | | |
| pgvector | | | | | |
| Chroma | | | | | |

## Estructura del repo

```
e-commerce-assistant/
├── README.md
├── LICENSE
├── docker-compose.yml
├── .github/workflows/ci.yml
├── pyproject.toml
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── ingestion/
│   ├── retrieval/
│   ├── agents/
│   ├── api/
│   └── eval/
├── data/
│   ├── raw/         (gitignored)
│   ├── processed/
│   ├── eval/queries.jsonl
│   └── MANIFEST.txt
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_benchmark_vectordbs.ipynb
│   └── 03_ragas_eval.ipynb
├── scripts/
│   └── download_data.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── streamlit_app.py
├── claude_design/
└── docs/
    ├── architecture.md
    ├── data_schema.md
    ├── decisions.md
    └── scalability.md
```

## Definition of Done específico del Proyecto 1

- [ ] Eval set de cien queries con ground truth manual completado
- [ ] Benchmark de los tres vector DBs con todas las métricas reportadas en la tabla del README
- [ ] Diferencia entre BM25-only, dense-only, y híbrido reportada como ablation
- [ ] Diferencia con y sin reranking reportada como ablation
- [ ] Demo desplegada en Streamlit Community Cloud con queries pre-baked
- [ ] Conversación multi-turn de al menos seis turnos demostrada en GIF del README
- [ ] Supervisor escalation con policy explícita documentada en `docs/decisions.md`

---

# PROYECTO 2 — Customer Support Triage Agent

## Caso de uso

Sistema automatizado de triage para tickets de soporte. Llega un ticket por email, Slack o chat, el agente clasifica intent y prioridad, busca soluciones en base de conocimiento de tickets resueltos, intenta auto-resolver o decide escalar a humano con justificación. Caso de uso pedido por todos los SaaS con soporte: Intercom, Zendesk, Freshdesk, HubSpot.

## Datasets

**Bitext Customer Service Tagged Dataset** (Hugging Face, libre):

- URL: `https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset`
- 26.872 queries pre-etiquetadas con 27 intents
- Campos: `instruction`, `intent`, `category`

**Customer Support on Twitter** (Kaggle, libre):

- URL: `https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter`
- 3 millones de tweets entre brands y clientes
- Campos: `tweet_id`, `author_id`, `inbound`, `response_tweet_id`, `text`

Usar Bitext para training del classifier y Twitter para evaluación end-to-end multi-turn.

## Stack técnico

- Classifier fine-tuneado: `distilbert-base-uncased` o `roberta-base` con HuggingFace Transformers + PEFT/LoRA
- Modelo final publicado en HuggingFace Hub con model card profesional
- LLM principal: Claude Sonnet 4.5 para reasoning y generación de respuesta
- Embeddings para similar-ticket retrieval: `sentence-transformers/all-mpnet-base-v2`
- Vector DB: Qdrant
- Orquestación: LangGraph
- Estado: PostgreSQL para tickets, resolutions, audit log
- Frontend: Next.js 14 con shadcn/ui para el Kanban
- Observability: LangSmith con traces públicas

## Arquitectura del flujo

```
Ticket entra (email/chat/Slack)
   │
   ▼
[Intent Classifier] DistilBERT fine-tuneado sobre Bitext
   │ → intent + confidence (cero a uno)
   │
   ▼
[Sentiment + Priority Analyzer] Claude structured output
   │ → sentiment ∈ {neg, neu, pos}, priority ∈ {P0..P3}, urgency_score
   │
   ▼
[Similar Tickets Retriever] Qdrant semantic search
   │ → top 5 tickets resueltos con sus resolutions
   │
   ▼
[Solution Drafter] Claude
   │ → respuesta sugerida basada en resolutions previas
   │
   ▼
[Confidence Estimator] reglas + LLM
   │ score = f(intent_conf, sentiment, similarity_score, priority)
   │
   ├─ score > 0.85 → AUTO-RESOLVE
   ├─ score entre 0.6 y 0.85 → SUGGEST (humano revisa)
   └─ score < 0.6 → ESCALATE
   │
   ▼
[Audit Logger] Postgres
   → registra decisión, scores, timestamps, outputs
```

## Métricas y evaluación

**Splits**: Bitext con 80% train, 10% validation, 10% test estratificado por intent. Twitter con muestra de doscientas conversaciones para eval end-to-end.

**Métricas obligatorias**:

- Classifier: F1 por intent en las 27 clases, macro-F1 global, matriz de confusión visualizada
- Triage: auto-resolution rate medido como porcentaje de tickets cerrados sin humano, false-escalation rate, false auto-resolve rate
- Response quality: LLM-as-judge sobre cien respuestas generadas con rubrica de helpfulness, tone, correctness
- Sistema: Latencia p50/p95, costo por ticket

**Tabla comparativa obligatoria**:

| Sistema | Macro-F1 | Auto-resolve | Latencia p95 | Costo/ticket |
|---|---|---|---|---|
| Zero-shot Claude | | | | |
| DistilBERT fine-tuneado solo | | — | | |
| Híbrido (este sistema) | | | | |

## Estructura del repo

```
support-triage-agent/
├── README.md
├── LICENSE
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── src/
│   ├── classifier/      (fine-tuning con LoRA)
│   ├── agents/          (nodos LangGraph)
│   ├── retrieval/
│   ├── api/
│   └── eval/
├── data/
│   ├── bitext/
│   ├── twitter/
│   └── eval/test_set.jsonl
├── notebooks/
│   ├── 01_classifier_training.ipynb
│   ├── 02_eval_pipeline.ipynb
│   └── 03_baselines_comparison.ipynb
├── models/              (gitignored, modelos en HF Hub)
├── frontend/            (Next.js Kanban UI)
├── tests/
├── claude_design/
└── docs/
```

## Definition of Done específico del Proyecto 2

- [ ] DistilBERT fine-tuneado publicado en HuggingFace Hub con model card completa
- [ ] Comparativa de los tres sistemas (zero-shot, classifier-only, híbrido) reportada en README
- [ ] Matriz de confusión visualizada e incluida en el README
- [ ] Demo desplegada con el Kanban mostrando tickets pre-cargados pasando por estados
- [ ] Galería de traces públicas en LangSmith con mínimo treinta ejemplos linkeados
- [ ] Análisis de los diez intents donde el classifier falla más, documentado en `docs/error_analysis.md`

---

# PROYECTO 3 — B2B Sales Intelligence Agent

## Caso de uso

Dada una lista de empresas target B2B, el agente investiga cada una (web público y noticias), arma un perfil estructurado, genera un email de outreach personalizado. Es el caso de uso detrás de Apollo.io, Clay.com, Outreach.io. AI Engineers que saben armar esto son ultra-demandados en sales-tech.

## Dataset

**Y Combinator Companies** (datos públicos):

- URL: `https://www.ycombinator.com/companies`
- Aproximadamente 5.000 empresas con metadata estructurada
- Campos: `name`, `batch`, `industry`, `status`, `location`, `founded`, `team_size`, `description`, `website`
- Alternativa: dataset open-source `yc-oss/yc-companies` en GitHub

**Tavily API** para web search agent-friendly: `https://tavily.com`, mil búsquedas gratis por mes, $0.001 por búsqueda después.

**HackerNews Algolia API** para news mentions: `https://hn.algolia.com/api`, gratis sin auth.

## Stack técnico

- LLM: Claude Sonnet 4.5
- Web search: Tavily API
- HTML parsing: `httpx` + `selectolax` (más rápido que BeautifulSoup)
- Structured outputs: Pydantic v2 para schemas `CompanyProfile`, `OutreachEmail`
- Orquestación: LangGraph con agent loop planner-executor-reflector
- Estado: PostgreSQL
- Frontend: Next.js 14 con gallery view de cards
- Observability: LangSmith

## Arquitectura del flujo

```
Para cada empresa en la lista target:
   │
   ▼
[Planner] Claude
   │ → plan: qué información buscar
   │
   ▼
[Executor loop] LangGraph
   │
   ├──► Tavily search ("Acme Corp recent funding 2026")
   ├──► HN search ("Acme Corp")
   ├──► Website fetch (homepage, /about, /careers)
   │
   └──► [Reflector] Claude
          ├─ ¿info suficiente?
          ├─ ¿contradicciones?
          └─ si no → executor con queries refinados
   │
   ▼
[Profile Builder] Claude + Pydantic
   → CompanyProfile estructurado
   │
   ▼
[Personalization Extractor] Claude
   → hooks: pain point + signal reciente
   │
   ▼
[Email Writer] Claude
   → email con subject, greeting, hook, value prop, CTA
   │
   ▼
[Quality Scorer] LLM-as-judge
   → scores: personalization, accuracy, CTA clarity
```

## Métricas y evaluación

Conjunto de prueba: doscientas empresas YC con ground truth metadata.

- Information accuracy: precision/recall sobre campos extraídos vs ground truth YC
- Personalization score: LLM-as-judge con Claude Opus como juez sobre cien emails
- Tool call efficiency: avg tool calls por empresa, distribución
- Latencia y costo por empresa procesada

**Tabla comparativa**:

| Sistema | Accuracy | Personalization | Latencia | Costo/empresa |
|---|---|---|---|---|
| Template only | — | | 2s | $0.001 |
| Single-search + email | | | 8s | $0.010 |
| Agent loop con reflection (este) | | | 18s | $0.040 |

## Definition of Done específico del Proyecto 3

- [ ] Procesamiento batch de cien empresas YC completado con outputs guardados
- [ ] Demo con gallery view de las cien empresas pre-procesadas
- [ ] Comparación contra los dos baselines documentada con números
- [ ] Galería de LangSmith traces públicas con treinta agent loops compartidos
- [ ] Análisis de costo vs calidad documentado: en qué punto agregar más reflection deja de mejorar

---

# PROYECTO 4 — Document Intelligence Pipeline

## Caso de uso

Sistema de Intelligent Document Processing para extraer información estructurada de documentos complejos como contratos, reportes financieros, formularios médicos y expedientes. Procesa PDFs con tablas, layouts multi-columna, firmas y elementos escaneados. Es el caso de uso central de legal-tech, fintech, healthcare, consultoría e insurance-tech. Empresas como Hyperscience, Rossum y Klarity están valuadas en cientos de millones por resolver esto.

## Dataset

**FUNSD** (Form Understanding in Noisy Scanned Documents):

- URL: `https://guillaumejaume.github.io/FUNSD/`
- 199 formularios escaneados anotados con entidades y relaciones
- Ground truth de campos extraídos: questions, answers, headers, other

**DocVQA** (Document Visual Question Answering):

- URL: `https://www.docvqa.org/datasets/docvqa`
- 12.767 documentos con 50.000 preguntas-respuesta
- Mix de tipos: forms, tables, lists, layouts complejos

**PubLayNet** (para layout analysis):

- URL: `https://github.com/ibm-aur-nlp/PubLayNet`
- 360.000 imágenes de páginas de papers con bounding boxes anotados

**Opcional para tablas complejas**: TabFact, FinTabNet (financial tables).

## Stack técnico

- Parsing principal: `unstructured` 0.16+ o `docling` (IBM, 2024)
- OCR para escaneos: Tesseract 5 o PaddleOCR
- VLM para documentos difíciles: Claude Sonnet 4.5 con vision input
- Table extraction: Camelot o Table Transformer (TATR)
- Layout detection: LayoutParser o detectron2
- Structured outputs: Pydantic v2 con schemas por tipo de documento
- LLM para reasoning sobre extracción: Claude Sonnet 4.5
- Validación: regex + LLM-as-judge
- Storage: PostgreSQL para documentos procesados y outputs
- Frontend: Next.js con previewer de PDF lado a lado del JSON extraído
- Observability: LangSmith

## Arquitectura del flujo

```
PDF entra
   │
   ▼
[Document Classifier] Claude Vision
   │ → tipo de documento: contract | invoice | form | report
   │
   ▼
[Layout Analyzer]
   │ ├─ texto plano → unstructured/docling
   │ ├─ escaneado → OCR (Tesseract o PaddleOCR)
   │ └─ documento difícil → Claude Vision directo
   │
   ▼
[Table Extractor]
   │ → Camelot para PDFs con texto
   │ → Table Transformer para tablas en imagen
   │
   ▼
[Field Extractor] Claude + Pydantic schema por tipo
   │ → JSON estructurado validado
   │
   ▼
[Validator]
   │ ├─ validaciones regex (NITs, fechas, montos)
   │ ├─ validaciones cross-field (subtotal + IVA = total)
   │ └─ LLM-as-judge para coherencia
   │
   ▼
[Confidence Scorer]
   │ score por campo + score global del documento
   │
   ├─ score > 0.9 → auto-aprobar
   ├─ score 0.7-0.9 → enviar a revisión humana
   └─ score < 0.7 → reproceso con VLM más caro
```

## Métricas y evaluación

- Field-level F1: precision y recall por tipo de campo extraído contra ground truth de FUNSD/DocVQA
- Document-level accuracy: porcentaje de documentos donde todos los campos críticos se extraen correctamente
- Table extraction accuracy: cell-level F1 sobre tablas de FinTabNet
- Layout detection mAP sobre PubLayNet
- Latencia y costo por documento procesado
- Comparativa: solo unstructured vs unstructured + VLM fallback vs VLM directo

**Tabla obligatoria**:

| Pipeline | Field F1 | Doc Accuracy | Table F1 | Latencia | Costo/doc |
|---|---|---|---|---|---|
| Unstructured only | | | | | |
| Unstructured + Claude Vision fallback (este) | | | | | |
| Claude Vision directo | | | | | |

## Estructura del repo

```
document-intelligence/
├── README.md
├── LICENSE
├── docker-compose.yml
├── pyproject.toml
├── src/
│   ├── classifier/
│   ├── parsers/        (unstructured, OCR, VLM)
│   ├── extractors/     (per document type)
│   ├── validators/
│   ├── api/
│   └── eval/
├── data/
│   ├── funsd/
│   ├── docvqa/
│   └── eval/test_set.jsonl
├── schemas/            (Pydantic models por tipo de doc)
├── notebooks/
├── frontend/           (Next.js con PDF viewer)
├── tests/
├── claude_design/
└── docs/
```

## Definition of Done específico del Proyecto 4

- [ ] Pipeline funciona sobre los tres tipos de input: texto plano, escaneado, layout complejo
- [ ] Field-level F1 reportado sobre FUNSD test set
- [ ] Document-level accuracy reportado sobre DocVQA
- [ ] Table extraction evaluado sobre FinTabNet o equivalente
- [ ] Demo permite subir un PDF de muestra y ver extracción en tiempo real con confidence scores
- [ ] Galería de diez documentos pre-procesados de distintos tipos accesible desde la demo
- [ ] Comparativa de pipelines documentada con números reproducibles

---

# PROYECTO 5 — Computer Use Agent

## Caso de uso

Agente autónomo que opera una interfaz de computadora virtualizada para automatizar workflows reales sin acceso a APIs. Recibe screenshots de la pantalla, decide acciones (clicks, keyboard input, scroll), ejecuta sobre la máquina virtual, recibe el nuevo screenshot. Es la frontera empujada por Anthropic en 2024-2026 con su feature Computer Use. Casos de uso reales: extracción de datos de sistemas legacy sin API, RPA inteligente, testing automatizado de webapps, agentes que reservan o compran online, automatización de back-office en banca y seguros.

## Dataset

Este proyecto no usa un dataset pre-existente, construye su propio eval set. Sin embargo, se usan benchmarks públicos para comparación:

**OSWorld benchmark**: `https://os-world.github.io/`

- Benchmark estándar de Computer Use con 369 tareas reales en Ubuntu
- Métricas: success rate, steps to completion

**WebArena**: `https://webarena.dev/`

- Benchmark sobre webapps reales (e-commerce, forum, gitlab)
- 812 tareas con ground truth

**Setup de eval propio**: definir veinte tareas reproducibles sobre una VM con Ubuntu, por ejemplo extraer datos de una webapp legacy, completar un formulario en LibreOffice, navegar un sitio web sin API.

## Stack técnico

- Computer Use API: Anthropic Claude Sonnet 4.5 con tool `computer_20250124` o `computer_20241022`
- VM: Docker container con Ubuntu 22.04 + xvfb para display virtual + VNC
- Streaming de screenshots: scrot o gnome-screenshot
- Input automation: xdotool para mouse y keyboard
- Orquestación: LangGraph con state que incluye historial de screenshots
- Storage: PostgreSQL para action logs, S3 o filesystem para screenshots
- Frontend: Next.js con visor del VNC en vivo
- Observability: LangSmith con traces de cada acción

## Arquitectura del flujo

```
Usuario describe tarea: "Extraé las ventas de Q3 del sistema legacy y guardalas en un CSV"
   │
   ▼
[Planner] Claude
   │ → plan inicial de pasos
   │
   ▼
LOOP DE ACCIÓN:
   │
   ├──► [Screenshot capture] scrot sobre Xvfb
   │
   ├──► [Vision + Reasoning] Claude Sonnet con tool computer_use
   │      → next action: click(x, y) | type(text) | key(combo) | scroll
   │
   ├──► [Action Executor] xdotool
   │
   ├──► [Verifier] Claude
   │      ¿se completó el paso esperado?
   │      ¿hay algún diálogo inesperado?
   │
   ├──► [State Updater] LangGraph state
   │      → progreso, screenshots históricos, errores
   │
   └──► continue hasta task_complete o max_steps
   │
   ▼
[Final Validator] Claude
   → verifica que el output cumple la tarea original
   │
   ▼
[Audit Log] PostgreSQL
   → todas las acciones, screenshots, decisiones
```

## Métricas y evaluación

- Task success rate sobre veinte tareas custom definidas
- Steps to completion: promedio y distribución
- Recovery rate: porcentaje de tareas donde el agente se equivocó pero corrigió
- Latencia end-to-end por tarea
- Costo por tarea (cada screenshot consume tokens de visión)
- Comparativa contra OSWorld baseline si aplica

**Tabla obligatoria**:

| Categoría de tarea | Success Rate | Avg Steps | Latencia | Costo/tarea |
|---|---|---|---|---|
| Form filling | | | | |
| Data extraction | | | | |
| Web navigation | | | | |
| Multi-step workflow | | | | |

## Definition of Done específico del Proyecto 5

- [ ] VM Docker reproducible levanta con `docker compose up`
- [ ] Veinte tareas custom definidas con ground truth de éxito
- [ ] Success rate reportado por categoría
- [ ] Demo permite seleccionar una tarea pre-definida y ver al agente ejecutándola en streaming
- [ ] Galería de cinco videos grabados (MP4 en repo o YouTube unlisted) de ejecuciones reales
- [ ] Safety layer documentada: lista de acciones bloqueadas (rm -rf, sudo, etcétera)

---

# PROYECTO 6 — Code Review Agent

## Caso de uso

Agente que analiza pull requests, detecta bugs reales, sugiere refactorizaciones, escribe tests faltantes, y comenta inline en el diff. Caso de uso enorme: GitHub Copilot Workspace, Cursor, Codium, Codacy, Sourcegraph Cody invierten cientos de millones acá. Roles dedicados de "AI Engineer for Developer Tools" en empresas como Anthropic, Sourcegraph, Replit, Cursor pagan paquetes premium.

## Dataset

**SWE-bench**: `https://www.swebench.com/`

- 2.294 issues reales de GitHub repos populares (django, sympy, scikit-learn, etc.)
- Cada uno con: descripción del bug, código antes, código del fix correcto, tests pasando
- Ground truth de qué archivos modificar y cómo

**SWE-bench Lite**: subset de 300 issues más manejables

**CodeReviewer dataset** (Microsoft Research): `https://github.com/microsoft/CodeBERT/tree/master/CodeReviewer`

- 642.000 pares (diff, comentario de review humano)
- Para benchmark de calidad de comentarios

## Stack técnico

- LLM: Claude Sonnet 4.5 (mejor en code por ahora, junto con GPT-4)
- Parsing de código: tree-sitter para AST de múltiples lenguajes
- Análisis estático: pylint, ruff, mypy para Python; ESLint para JS/TS
- Diff parsing: unidiff o difflib
- GitHub integration: PyGithub para leer PRs y postear comentarios
- Orquestación: LangGraph con nodos por tipo de análisis
- Storage: PostgreSQL para reviews históricos
- Frontend: Next.js con diff viewer (react-diff-viewer)
- Observability: LangSmith

## Arquitectura del flujo

```
PR llega (webhook GitHub o input manual)
   │
   ▼
[PR Analyzer] PyGithub
   │ → archivos cambiados, líneas modificadas, contexto del PR
   │
   ▼
[Context Builder]
   │ ├─ AST del código modificado con tree-sitter
   │ ├─ archivos relacionados (importados, importadores)
   │ ├─ historia git relevante
   │ └─ issue linkeado al PR
   │
   ▼
[Multi-aspect Analyzers] (en paralelo)
   │
   ├──► [Bug Detector] Claude + análisis estático
   │      → posibles bugs con severidad y línea exacta
   │
   ├──► [Style Checker] ruff/eslint + Claude
   │      → issues de estilo y consistencia
   │
   ├──► [Test Gap Analyzer] Claude
   │      → funciones modificadas sin tests
   │
   ├──► [Security Scanner] semgrep + Claude
   │      → patrones de seguridad
   │
   └──► [Performance Reviewer] Claude
          → posibles ineficiencias
   │
   ▼
[Comment Synthesizer] Claude
   → comentarios inline con: location, severity, suggestion, justificación
   │
   ▼
[Priority Filter]
   → top N comentarios por severidad para no saturar al developer
   │
   ▼
[Output] post a GitHub o devolver JSON
```

## Métricas y evaluación

- Bug detection F1 sobre SWE-bench Lite (recall: cuántos bugs reales detectó, precision: cuántos de los flags fueron bugs reales)
- Test gap detection accuracy sobre archivos con coverage conocido
- Comment quality: LLM-as-judge sobre cien comentarios generados con rubrica de actionability, specificity, correctness
- False positive rate: cuántos comentarios generados son ruido
- Latencia por PR (varía mucho con tamaño)
- Costo por PR analizado

**Tabla obligatoria**:

| Sistema | Bug Recall | Bug Precision | Comment Quality | FP rate | Costo/PR |
|---|---|---|---|---|---|
| Linter only (ruff) | | | | | $0 |
| Claude single-pass | | | | | |
| Pipeline completo (este) | | | | | |

## Definition of Done específico del Proyecto 6

- [ ] Pipeline corre sobre los 300 issues de SWE-bench Lite
- [ ] Bug detection F1 reportado contra ground truth de fixes
- [ ] Comment quality evaluado con LLM-as-judge sobre cien casos
- [ ] Demo permite pegar un diff o link a un PR público y ver review generada
- [ ] Galería de diez reviews reales sobre PRs públicos famosos accesible desde la demo
- [ ] GitHub Action publicada en marketplace que permita usar el agente en repos reales
- [ ] Comparativa de costo vs calidad documentada: cuándo vale la pena vs ruff sólo

---

# PROYECTO 7 — AI Safety y Red Teaming Framework

## Caso de uso

Framework de evaluación de seguridad para sistemas LLM en producción. Detecta vulnerabilidades comunes (prompt injection, jailbreaks, data leakage, hallucinations), implementa guardrails, y produce reports de seguridad alineados con OWASP LLM Top 10. Caso de uso indispensable para industrias reguladas: banca, seguros, salud, gobierno, defensa, compliance. Roles de AI Safety Engineer y MLSec en empresas como Robust Intelligence, Lakera, Protect AI, HiddenLayer pagan paquetes top-tier.

## Dataset

**HarmBench**: `https://github.com/centerforaisafety/HarmBench`

- 400 prompts adversariales etiquetados con categoría de daño
- Ground truth de comportamiento esperado (refusal)

**JailbreakBench**: `https://jailbreakbench.github.io/`

- 100 comportamientos prohibidos con jailbreaks conocidos
- Métricas estándar de robustez

**ToxicChat**: `https://huggingface.co/datasets/lmsys/toxic-chat`

- 10.000 user-prompts reales etiquetados como tóxicos o no

**PII detection benchmarks**: usar dataset CONLL2003 o construir uno sintético con `presidio` data generator.

**OWASP LLM Top 10**: `https://owasp.org/www-project-top-10-for-large-language-model-applications/`

## Stack técnico

- LLM: Claude Sonnet 4.5 como sistema bajo testeo y como red-teamer
- Guardrails framework: `guardrails-ai` o `nvidia-nemo-guardrails`
- PII detection: Microsoft Presidio
- Toxicity detection: `unitary/toxic-bert` desde HuggingFace
- Prompt injection detection: `protectai/deberta-v3-base-prompt-injection`
- Red teaming framework: `giskard` o `garak`
- Scanner de vulnerabilidades: `garak` (NVIDIA, open source)
- Storage: PostgreSQL para test results y attack logs
- Frontend: Next.js con dashboard de seguridad
- Observability: LangSmith

## Arquitectura del flujo

```
Sistema bajo testeo (uno de los proyectos 1-6)
   │
   ▼
[Attack Generator]
   │ ├─ HarmBench prompts conocidos
   │ ├─ JailbreakBench techniques
   │ ├─ Prompt injection variants (DAN, instructions override)
   │ ├─ LLM-generated adversarial (Claude attack mode)
   │ └─ Encoded attacks (base64, rot13, unicode)
   │
   ▼
[Attack Executor]
   │ corre cada attack contra el sistema target
   │
   ▼
[Response Analyzer]
   │ ├─ ¿hubo refusal? (debería en attacks)
   │ ├─ ¿hubo leak? (PII detector sobre output)
   │ ├─ ¿hubo compliance con la intent maliciosa?
   │ └─ ¿hubo hallucination factual?
   │
   ▼
[Categorizer] alineado con OWASP LLM Top 10
   │ LLM01: Prompt Injection
   │ LLM02: Insecure Output Handling
   │ LLM03: Training Data Poisoning
   │ LLM04: Model Denial of Service
   │ LLM05: Supply Chain Vulnerabilities
   │ LLM06: Sensitive Information Disclosure
   │ LLM07: Insecure Plugin Design
   │ LLM08: Excessive Agency
   │ LLM09: Overreliance
   │ LLM10: Model Theft
   │
   ▼
[Guardrails Layer]
   │ ├─ Input filtering
   │ ├─ Output sanitization
   │ ├─ PII redaction
   │ └─ Refusal injection para casos identificados
   │
   ▼
[Report Generator]
   → security report con vulnerabilidades, severidad, recomendaciones
```

## Métricas y evaluación

- Attack success rate por categoría OWASP (porcentaje de attacks que rompieron el sistema)
- False positive rate de guardrails (porcentaje de queries legítimas rechazadas)
- Latencia agregada por guardrails
- Coverage del OWASP LLM Top 10
- Reducción de attack success rate antes vs después de guardrails

**Tabla obligatoria**:

| Categoría OWASP | Attack Success (baseline) | Attack Success (con guardrails) | FP rate |
|---|---|---|---|
| LLM01 Prompt Injection | | | |
| LLM02 Insecure Output | | | |
| LLM06 Info Disclosure | | | |
| ... | | | |

## Definition of Done específico del Proyecto 7

- [ ] Framework aplicado a al menos dos proyectos previos del portafolio (típicamente Proyecto 1 y Proyecto 3)
- [ ] Cobertura de las diez categorías OWASP documentada con tests por cada una
- [ ] Reducción de attack success rate cuantificada antes vs después de guardrails
- [ ] Demo permite probar attacks contra una versión simplificada del sistema
- [ ] Galería de cincuenta attacks ejecutados con resultados pre-computados
- [ ] Reports de seguridad para los proyectos 1 y 3 incluidos como PDF en el repo
- [ ] Librería publicable como paquete pip con tests propios

---

# PROYECTO 8 — GraphRAG sobre SEC EDGAR

## Caso de uso

Sistema GraphRAG que responde preguntas complejas multi-hop sobre el ecosistema de empresas públicas a partir de los reportes 10-K y 10-Q que esas empresas presentan obligatoriamente a la SEC. Construye un knowledge graph con entidades (empresas, directores, subsidiarias, productos, mercados, competidores) y relaciones (board memberships, ownership stakes, supplier relationships, competitive overlap). Caso de uso central de finanzas, consultoría estratégica, compliance y M&A. Empresas como Visible Alpha, Tegus, AlphaSense facturan cientos de millones por resolver esto a su modo.

## Dataset

**SEC EDGAR** (datos públicos, oficiales, gratis):

- URL principal: `https://www.sec.gov/edgar/searchedgar/companysearch`
- API: `https://www.sec.gov/edgar/sec-api-documentation`
- Filings 10-K (anuales), 10-Q (trimestrales), 8-K (eventos significativos), DEF 14A (proxy statements con info de directors)
- Cobertura: todas las empresas públicas en EEUU desde 1993
- Para empezar manejable: top 500 empresas del S&P 500, últimos cinco años, lo cual da aproximadamente diez mil documentos

**Alternativa o complemento**: dataset pre-procesado `EDGAR-CORPUS` en HuggingFace si está disponible.

## Stack técnico

- Knowledge graph DB: Neo4j 5+ con plugin APOC
- Lenguaje de consulta: Cypher
- Vector index nativo de Neo4j 5.13+ para hybrid search (estructural + vectorial)
- LLM para extracción de entidades y relaciones: Claude Sonnet 4.5
- Validación de extracción: Pydantic schemas
- Embeddings: Voyage AI `voyage-3` o `bge-large-en-v1.5` local
- Orquestación: LangChain con módulo `neo4j-graphrag` (oficial de Neo4j) o LlamaIndex KnowledgeGraphIndex
- Implementación de referencia: Microsoft `graphrag` library como base conceptual
- Frontend: Next.js con `react-force-graph-2d` para visualización del grafo
- Storage adicional: PostgreSQL para audit y staleness tracking
- Observability: LangSmith

## Arquitectura del flujo

```
FASE DE INGESTA (una vez sobre el corpus):
   │
   PDF/HTML del 10-K de Apple Inc 2024
   │
   ▼
[Document Chunker] respeta secciones del 10-K (Item 1 Business, Item 1A Risk Factors, etc.)
   │
   ▼
[Entity Extractor] Claude + Pydantic
   │ → entities: [
   │     {id: "apple", type: "Company", cik: "320193"},
   │     {id: "tim_cook", type: "Person", role: "CEO"},
   │     {id: "tsmc", type: "Company", relationship: "supplier"}
   │   ]
   │ → relationships: [
   │     {from: "tim_cook", to: "apple", type: "CEO_OF", since: "2011"},
   │     {from: "apple", to: "tsmc", type: "SUPPLIED_BY"},
   │     {from: "apple", to: "samsung", type: "COMPETES_WITH"}
   │   ]
   │
   ▼
[Graph Merger] Neo4j MERGE
   │ → si entidad existe, no duplica; si no, crea
   │ → genera embedding del nombre+descripción y guarda en nodo
   │
   ▼
[Staleness Tracker]
   → cada nodo tiene updated_at y source_filing_date

FASE DE CONSULTA:
   │
   Pregunta: "¿Qué empresas del S&P 500 dependen de TSMC y cuál es su exposición combinada?"
   │
   ▼
[Query Classifier] Claude
   │ → tipo: multi_hop + aggregation
   │
   ▼
[Entry Point Finder] vector search en Neo4j
   │ → nodos seed: [tsmc]
   │
   ▼
[Graph Traversal] Cypher
   │ MATCH (tsmc:Company {ticker:'TSM'})<-[:SUPPLIED_BY]-(c:Company)
   │ WHERE c.in_sp500 = true
   │ RETURN c, c.revenue, count(*) as dependency_strength
   │
   ▼
[Result Aggregator]
   │ → ordenamiento, totales, ratios
   │
   ▼
[Synthesizer] Claude
   → respuesta natural con citas a nodos específicos
   │
   ▼
[Visualization]
   → subgrafo de los nodos relevantes para mostrar en frontend
```

## Métricas y evaluación

Construir manualmente eval set de cien preguntas multi-hop sobre S&P 500 con ground truth construida verificando manualmente en los 10-Ks. Categorías de preguntas:

- Lookup directo (treinta): "¿Quién es el CEO de Microsoft?"
- Multi-hop dos saltos (treinta): "¿Qué empresas competidoras de Apple tienen al mismo proveedor de chips?"
- Multi-hop tres o más saltos (veinte): "¿Qué directores sirven en boards de competidores directos en el sector farmacéutico?"
- Aggregation (veinte): "¿Cuántas empresas del S&P 500 mencionan exposición a China como riesgo en su 10-K 2024?"

**Métricas obligatorias**:

- Hit rate sobre las preguntas multi-hop
- Entity extraction F1: precision/recall de entidades extraídas vs gold standard
- Relationship extraction F1
- Faithfulness con RAGAS sobre las respuestas finales
- Comparativa contra vector RAG puro sobre el mismo corpus

**Tabla comparativa**:

| Sistema | Lookup Hit | 2-hop Hit | 3-hop Hit | Aggregation Hit | Faithfulness |
|---|---|---|---|---|---|
| Vector RAG sobre el mismo corpus | | | | | |
| GraphRAG (este sistema) | | | | | |
| Hybrid: Graph + Vector | | | | | |

## Definition of Done específico del Proyecto 8

- [ ] Knowledge graph poblado con al menos las top cien empresas del S&P 500 y sus 10-Ks de los últimos tres años
- [ ] Mínimo cinco mil nodos y veinte mil aristas en el grafo final
- [ ] Eval set de cien preguntas multi-hop con ground truth manual completado
- [ ] Comparativa contra Vector RAG sobre el mismo corpus con números reproducibles
- [ ] Demo con visualización interactiva del grafo (react-force-graph)
- [ ] Queries pre-baked en la demo cubriendo las cuatro categorías
- [ ] Staleness detector activo que marca nodos con datos mayores a 365 días
- [ ] Schema del grafo documentado en `docs/graph_schema.md` con todos los tipos de nodos y relaciones

---

# PROYECTO 9 — Voice AI Conversational Agent

## Caso de uso

Agente conversacional por voz para customer service telefónico. El cliente llama o envía audio, el sistema transcribe en tiempo real con Whisper, entiende el intent con Claude, busca información en una base de conocimiento si hace falta, genera respuesta y la sintetiza de vuelta como voz natural. Caso de uso de un mercado en explosión: Bland AI, Vapi, Retell, Hume y Pindrop están valuadas en cientos de millones. Aplicaciones reales: reservas de restaurantes, agendamiento de citas médicas, customer support de primera línea, conversational commerce.

## Datasets

**Mozilla Common Voice**: `https://commonvoice.mozilla.org/en/datasets`

- Datos open de voz con transcripciones, múltiples idiomas
- Útil para evaluar WER del STT en condiciones reales

**LibriSpeech**: `https://www.openslr.org/12/`

- 1.000 horas de audiobooks en inglés con transcripciones
- Benchmark estándar de WER

**Spoken-SQuAD**: `https://github.com/chiahsuan156/Spoken-SQuAD`

- Versión hablada de SQuAD para evaluar Q&A sobre audio

**MultiWOZ 2.4** (para conversational evaluation): `https://github.com/budzianowski/multiwoz`

- 10.000 diálogos task-oriented multi-domain
- Útil para evaluar task completion conversacional

## Stack técnico

- Speech-to-Text: `openai-whisper` con modelo `whisper-large-v3` (local, GPU) o Whisper API ($0.006 por minuto)
- LLM principal: Claude Sonnet 4.5
- Text-to-Speech: ElevenLabs API (calidad premium, $0.30/1K caracteres) o `coqui-tts` con XTTS-v2 local
- Orquestación de turnos: LangGraph con turn detection
- Streaming de audio en producción: LiveKit Cloud o Twilio Voice
- VAD (Voice Activity Detection): `silero-vad` para detectar fin de turno
- Storage: PostgreSQL para transcripts, S3 para audio files
- Frontend: Next.js con WebRTC para audio en browser
- Observability: LangSmith + métricas custom de latencia por componente

## Arquitectura del flujo

```
Audio entrante (WebRTC, telefonía, archivo)
   │
   ▼
[VAD] Silero VAD detecta fin de turno
   │
   ▼
[STT] Whisper-large-v3 transcribe
   │ → texto + confidence + idioma detectado
   │
   ▼
[Intent + Context] LangGraph state
   │ ├─ historial conversacional
   │ ├─ slots ya completados (date, party_size, etc.)
   │ └─ tipo de tarea actual
   │
   ▼
[Reasoner] Claude
   │ → next action: respond | ask_clarification | book | transfer_to_human
   │
   ├──► si necesita info: RAG sobre KB
   ├──► si necesita action: tool call (booking API, etc.)
   │
   ▼
[Response Generator] Claude
   → texto natural conversacional (no formal)
   │
   ▼
[TTS] ElevenLabs o XTTS-v2
   → audio output (formato WAV o MP3 streamed)
   │
   ▼
[Audio Stream Back] al cliente
   │
   ▼
[Conversation Logger] PostgreSQL
   → transcript completo, audio refs, decisiones, latencias por turno
```

## Métricas y evaluación

- WER (Word Error Rate) del STT sobre LibriSpeech test-clean y test-other
- WER en idiomas específicos del use case (español si target LATAM)
- End-to-end latency por turno conversacional: STT + LLM + TTS, target menor a 800ms para sentirse natural
- Resolution rate: porcentaje de conversaciones que completan la tarea sin transferir a humano, medido sobre cien conversaciones simuladas con LLM-as-judge
- MOS (Mean Opinion Score) sobre calidad de voz sintética, medido con human eval o usando `nisqa` automated MOS
- Cost per minute de conversación

**Tabla comparativa obligatoria**:

| Componente | Métrica | Valor |
|---|---|---|
| STT | WER sobre LibriSpeech test-clean | |
| STT | WER en español Common Voice | |
| LLM | Resolution rate sobre 100 conversaciones | |
| TTS | MOS automated | |
| Sistema | Latencia p95 end-to-end por turno | |
| Sistema | Costo por minuto de conversación | |

## Definition of Done específico del Proyecto 9

- [ ] WER reportado sobre al menos dos benchmarks (LibriSpeech + un dataset en español)
- [ ] Latencia end-to-end por turno medida y optimizada por debajo de un segundo
- [ ] Cien conversaciones simuladas evaluadas con LLM-as-judge para resolution rate
- [ ] Demo con interfaz WebRTC permite hablar en el navegador y recibir respuesta en voz
- [ ] Diez conversaciones reales grabadas como MP3 incluidas en el repo como evidence
- [ ] Comparativa entre Whisper open vs API documentada con costos
- [ ] Comparativa entre XTTS-v2 vs ElevenLabs documentada con MOS
- [ ] Conversación demo dura mínimo seis turnos completando una tarea real

---

# Cobertura final del portafolio

Mapeando los nueve proyectos contra los grandes bloques de capacidades que pide la industria de AI Engineering en 2026, la cobertura final queda como sigue. RAG completo con búsqueda híbrida y reranking lo cubre profundamente el Proyecto 1 y parcialmente los Proyectos 4 y 8. Fine-tuning con LoRA y publicación de modelos en HuggingFace Hub lo cubre el Proyecto 2. Agentes con LangGraph, tool use, reflection y memoria persistente los cubren los Proyectos 3, 4, 5 y 6. Document AI con parsing de PDFs complejos y tablas lo cubre el Proyecto 4. Multimodal con visión integrada en pipelines y agentes lo cubren los Proyectos 4 y 5. Computer Use y automatización de interfaces reales lo cubre el Proyecto 5. Code AI para developer tools lo cubre el Proyecto 6. AI Safety, red teaming, guardrails y compliance lo cubre el Proyecto 7. Información estructurada relacional y consultas multi-hop sobre knowledge graphs los cubre el Proyecto 8. Voice AI con STT, LLM y TTS lo cubre el Proyecto 9. Las habilidades transversales de evaluación rigurosa con métricas estándar, observability con traces públicos, deploy en producción, mostrabilidad pasiva y documentación profesional aparecen en los nueve proyectos por igual.

Lo único que queda fuera incluso con cobertura del noventa y nueve por ciento es relativamente nicho. Reproducción de papers de research desde cero es para roles de Research Engineer, no AI Engineer aplicado. Recommendation systems clásicos con factorización de matrices y two-tower models pertenecen más al perfil de Machine Learning Engineer tradicional. Time series forecasting es nicho específico de empresas con datos temporales centrales. Esos no necesitan estar en el portafolio para AI Engineer mid-senior.

---

# Orden de ejecución sugerido

El orden propuesto minimiza retrabajo permitiendo reutilizar infraestructura común y conocimiento entre proyectos consecutivos.

**Fase 1 (semanas 1 a 9)**: Proyectos 1, 2 y 3 en este orden. El Proyecto 1 establece la base de RAG, eval framework y deploy. El Proyecto 2 agrega fine-tuning encima de la infraestructura ya montada. El Proyecto 3 introduce agentes con tool use, base para los siguientes.

**Fase 2 (semanas 10 a 15)**: Proyectos 4 y 5. El Proyecto 4 (Document AI) reusa pipeline de evaluación del 1 y añade multimodal con Claude Vision. El Proyecto 5 (Computer Use) extiende el agente del 3 con visión y acción real.

**Fase 3 (semanas 16 a 21)**: Proyectos 6 y 7. El Proyecto 6 (Code Review) es independiente pero reusa observability de los anteriores. El Proyecto 7 (AI Safety) se construye encima de los Proyectos 1 y 3 que ya tienen sistemas para atacar.

**Fase 4 (semanas 22 a 27)**: Proyectos 8 y 9. El Proyecto 8 (GraphRAG) es la profundización conceptual de RAG. El Proyecto 9 (Voice AI) cierra modalidad faltante.

Total realista: veintisiete semanas concentradas, equivalente a seis meses y medio si sostenés quince a veinte horas semanales en portafolio más diez horas en cursos.

---

# Plantilla de brief para Claude Code

Al iniciar cada sesión de Claude Code para trabajar en un proyecto, pegar el siguiente bloque adaptado:

```
Voy a trabajar en el Proyecto N del portafolio AI Engineer.

CONTEXTO: portafolio completo definido en /docs/portafolio_specs.md

PROYECTO: [nombre del proyecto]

ESTADO ACTUAL: [describir qué está hecho y qué falta]

OBJETIVO DE ESTA SESIÓN: [tarea concreta]

CRITERIOS DE ACEPTACIÓN:
1. La tarea no se considera completa hasta que pasa los criterios del bloque [X] del Definition of Done universal
2. Cualquier cambio en código nuevo requiere tests unitarios
3. Cualquier endpoint nuevo requiere validación Pydantic y manejo de errores
4. Cualquier llamada a API externa requiere timeout y retry con tenacity
5. Cualquier configuración nueva va a .env.example, nunca hardcodeada
6. Antes de declarar la tarea lista, verificar que mypy --strict y ruff check pasan sin errores

NO MARCAR COMO COMPLETO si:
- No agregaste tests para el código nuevo
- No actualizaste el README si cambió comportamiento
- No corriste el flujo end-to-end al menos una vez
- Hay TODOs sin contextualizar
- Hay prints de debug olvidados

Empezamos por: [primera subtarea concreta]
```

---

# Notas finales sobre uso del documento

Este documento es la fuente de verdad del portafolio. Vivirá en cada repo dentro de `docs/portafolio_specs.md` para que Claude Code lo tenga siempre a mano como contexto. Cualquier desviación de las specs se documenta en el README del proyecto correspondiente, no se hace silenciosamente.

El Definition of Done universal del principio se relee antes de cerrar cualquier milestone. Si Claude Code declara una tarea completa, abrir el checklist y verificar item por item, no aceptar la afirmación de completitud sin la verificación.

Los datasets mencionados son públicos y libres para uso de portafolio, pero verificar siempre la licencia exacta antes de redistribuir resultados procesados. Lo que se publica en HuggingFace Hub o blog posts debe respetar la licencia del dataset original.

Las URLs de APIs y servicios mencionados (Anthropic, Voyage, Cohere, Tavily, ElevenLabs) tienen sus propios términos de servicio y precios que pueden cambiar. Verificar en el momento de usar cada servicio.

Cada proyecto, al terminar su milestone v1.0.0, dispara una rutina de comunicación: blog post, post de LinkedIn, actualización del CV, agregar al portfolio website. El proyecto no termina con el `git tag v1.0.0` sino con la comunicación al exterior.
