# Global project configuration

# ── Backend selection ─────────────────────────────────────────
# "groq"   → uses Groq API (needs GROQ_API_KEY in .env)
# "ollama" → uses local Ollama server (no API key needed)
LLM_BACKEND = "ollama"

# ── Ollama settings (used when LLM_BACKEND = "ollama") ───────
OLLAMA_BASE_URL = "http://localhost:11434/v1"
OLLAMA_MODEL    = "phi4-mini:latest"   # change to whatever model you pulled

# ── Groq settings (used when LLM_BACKEND = "groq") ──────────
GROQ_MODEL = "llama-3.3-70b-versatile"

ARTICLE_PARALLEL = 1  # increase to 3 if VRAM allows

# ── LLM defaults ─────────────────────────────────────────────
LLM_DEFAULT_MODEL       = OLLAMA_MODEL if LLM_BACKEND == "ollama" else GROQ_MODEL
LLM_TEMPERATURE         = 0.0
LLM_MAX_RETRIES         = 3
LLM_RETRY_DELAY_SECONDS = 5
LLM_MAX_TOKENS = 2048  # safe ceiling for all steps

# ── Paths ─────────────────────────────────────────────────────
DATA_RAW_DIR    = "data/raw"
DATA_OUTPUT_DIR = "data/output"

# ── JSONL bulk run settings ───────────────────────────────────
JSONL_INPUT_FILE  = "articles_train.jsonl"        # input articles
OUTPUT_KG_JSONL   = "data/output/kg_output.jsonl" # one KG per line, appended after each article
MAX_ARTICLES      = None                        # None = run all
CHECKPOINT_FILE   = "data/output/progress.json"
ERROR_LOG_FILE    = "data/output/errors.json"

# Dataset-specific bulk defaults (recommended)
WIKI_JSONL_INPUT_FILE    = JSONL_INPUT_FILE
ESSAY_JSONL_INPUT_FILE   = "mine_train.jsonl"
WIKI_OUTPUT_KG_JSONL     = "data/output/kg_output_wiki.jsonl"
ESSAY_OUTPUT_KG_JSONL    = "data/output/kg_output_essay.jsonl"
WIKI_CHECKPOINT_FILE     = "data/output/progress_wiki.json"
ESSAY_CHECKPOINT_FILE    = "data/output/progress_essay.json"
WIKI_ERROR_LOG_FILE      = "data/output/errors_wiki.json"
ESSAY_ERROR_LOG_FILE     = "data/output/errors_essay.json"

# ── Embedding ─────────────────────────────────────────────────
EMBEDDING_MODEL            = "nomic-ai/nomic-embed-text-v1.5"
EMBEDDING_TRUST_REMOTE_CODE = True
EMBEDDING_NORMALIZE         = True

# ── Chunking ──────────────────────────────────────────────────
CHUNK_TARGET_TOKENS = 400
CHUNK_MAX_TOKENS    = 550
CHUNK_MIN_TOKENS    = 50

WIKI_CHUNK_TARGET_TOKENS  = 400
WIKI_CHUNK_MAX_TOKENS     = 550
WIKI_CHUNK_MIN_TOKENS     = 50

ESSAY_CHUNK_TARGET_TOKENS = 200
ESSAY_CHUNK_MAX_TOKENS    = 300
ESSAY_CHUNK_MIN_TOKENS    = 50

# ── Per-step model selection ──────────────────────────────────
EXTRACTOR_MODEL                      = LLM_DEFAULT_MODEL
ENTITY_RESOLUTION_MODEL              = LLM_DEFAULT_MODEL
RELATION_DEFINITION_MODEL            = LLM_DEFAULT_MODEL
RELATION_CANONICALIZATION_MODEL      = LLM_DEFAULT_MODEL
RELATION_SINGLETON_NORMALIZATION_MODEL = LLM_DEFAULT_MODEL
ENTITY_CONCEPT_MODEL                 = LLM_DEFAULT_MODEL
RELATION_CONCEPT_MODEL               = LLM_DEFAULT_MODEL

# ── Pipeline parameters ───────────────────────────────────────
ENTITY_SIMILARITY_THRESHOLD = 0.7
ENTITY_TOP_K_CANDIDATES     = 5
ENTITY_MAX_CONTEXT_TRIPLES  = 3

RELATION_SIMILARITY_THRESHOLD = 0.7
RELATION_TOP_K_CANDIDATES     = 5
RELATION_SINGLETON_BATCH_SIZE = 10

RELATION_DEFINITION_BATCH_SIZE = 10
SCHEMA_BATCH_SIZE               = 8