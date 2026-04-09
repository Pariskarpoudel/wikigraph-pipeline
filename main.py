# main.py
import os
import json
import logging
import concurrent.futures
import config
from pipeline.chunker import chunk_article, chunk_article_from_text, chunk_essay_from_text
from pipeline.extractor import extract_all_triples
from pipeline.deduplicator import deduplicate_triples
from pipeline.entity_resolver import resolve_entities
from pipeline.relation_definer import define_relations
from pipeline.relation_canonicalizer import canonicalize_relations
from pipeline.schema_inducer import induce_schema
from pipeline.graph_assembler import assemble_graph, save_graph, save_graph_jsonl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Core pipeline — single article/essay
# ─────────────────────────────────────────────────────────────

def run_pipeline_from_text(
    text:          str,
    title:         str,
    dataset:       str = "wiki",          # ← "wiki" or "essay"
    output_dir:    str = config.DATA_OUTPUT_DIR,
    kg_jsonl_path: str = config.OUTPUT_KG_JSONL,
    save_jsonl:    bool = True,
) -> dict:
    """
    Run full KG construction pipeline on a raw text string.
    Works for both WikiGraphs and essay (mine1) datasets.

    Args:
        text:       raw article/essay string
        title:      article/essay title
        dataset:    "wiki" → chunk_article_from_text
                    "essay" → chunk_essay_from_text
        output_dir: where to save the output KG JSON
    """
    logger.info(f"{'='*60}")
    logger.info(f"Starting pipeline [{dataset}]: '{title}'")
    logger.info(f"{'='*60}")

    # ── Step 1: Chunking ──────────────────────────────────────
    logger.info("Step 1: Chunking...")
    if dataset == "essay":
        chunks = chunk_essay_from_text(text, fallback_title=title)
    else:
        chunks = chunk_article_from_text(text, fallback_title=title)
    logger.info(f"  → {len(chunks)} chunks")

    if not chunks:
        raise ValueError(f"No chunks produced for '{title}'")

    article_title = chunks[0]["article_title"]
    logger.info(f"  → Title: '{article_title}'")

    # ── Step 2: Triple Extraction ─────────────────────────────
    logger.info("Step 2: Extracting triples...")
    raw_triples = extract_all_triples(chunks)
    logger.info(f"  → {len(raw_triples)} raw triples")

    # ── Step 3: Deduplication ─────────────────────────────────
    logger.info("Step 3: Deduplicating triples...")
    triples = deduplicate_triples(raw_triples)
    logger.info(f"  → {len(triples)} triples after dedup")

    # ── Step 4: Entity Resolution ─────────────────────────────
    logger.info("Step 4: Resolving entities...")
    triples, entity_map = resolve_entities(triples, article_title)
    logger.info(f"  → {len(entity_map)} entities resolved")

    # ── Step 5: Relation Definition ───────────────────────────
    logger.info("Step 5: Defining relations...")
    relation_definitions = define_relations(triples, article_title)
    logger.info(f"  → {len(relation_definitions)} relations defined")

    # ── Step 6: Relation Canonicalization ─────────────────────
    logger.info("Step 6: Canonicalizing relations...")
    triples, relation_map = canonicalize_relations(
        triples, relation_definitions, article_title
    )
    logger.info(f"  → {len(relation_map)} relations canonicalized")

    # ── Step 7: Schema Induction ──────────────────────────────
    logger.info("Step 7: Inducing schema...")
    entity_concepts, relation_concepts = induce_schema(
        triples, relation_definitions, article_title
    )
    logger.info(f"  → {len(entity_concepts)} entity concepts")
    logger.info(f"  → {len(relation_concepts)} relation concepts")

    # ── Step 8: Graph Assembly ────────────────────────────────
    logger.info("Step 8: Assembling graph...")
    kg = assemble_graph(
        article_title        = article_title,
        resolved_triples     = triples,
        entity_map           = entity_map,
        relation_map         = relation_map,
        relation_definitions = relation_definitions,
        entity_concepts      = entity_concepts,
        relation_concepts    = relation_concepts,
    )

    if save_jsonl:
        save_graph_jsonl(kg, kg_jsonl_path)
        saved_path = kg_jsonl_path
    else:
        saved_path = save_graph(kg, output_dir)

    logger.info(f"{'='*60}")
    logger.info(f"Pipeline complete for '{article_title}'")
    logger.info(f"  Nodes:     {len(kg['nodes'])}")
    logger.info(f"  Relations: {len(kg['relations'])}")
    logger.info(f"  Triples:   {len(kg['triples'])}")
    logger.info(f"  Saved to:  {saved_path}")
    logger.info(f"{'='*60}")

    return kg


def run_pipeline(article_path: str, output_dir: str = config.DATA_OUTPUT_DIR) -> dict:
    """
    Original entry point — reads from .txt file.
    Kept for single-article mode: python main.py data/raw/article.txt
    Always uses wiki chunking.
    """
    logger.info(f"{'='*60}")
    logger.info(f"Starting pipeline for: {article_path}")
    logger.info(f"{'='*60}")

    logger.info("Step 1: Chunking article...")
    chunks = chunk_article(article_path)
    logger.info(f"  → {len(chunks)} chunks")

    if not chunks:
        raise ValueError(f"No chunks produced from {article_path}")

    article_title = chunks[0]["article_title"]
    logger.info(f"  → Article: '{article_title}'")

    logger.info("Step 2: Extracting triples...")
    raw_triples = extract_all_triples(chunks)
    logger.info(f"  → {len(raw_triples)} raw triples")

    logger.info("Step 3: Deduplicating triples...")
    triples = deduplicate_triples(raw_triples)
    logger.info(f"  → {len(triples)} triples after dedup")

    logger.info("Step 4: Resolving entities...")
    triples, entity_map = resolve_entities(triples, article_title)
    logger.info(f"  → {len(entity_map)} entities resolved")

    logger.info("Step 5: Defining relations...")
    relation_definitions = define_relations(triples, article_title)
    logger.info(f"  → {len(relation_definitions)} relations defined")

    logger.info("Step 6: Canonicalizing relations...")
    triples, relation_map = canonicalize_relations(
        triples, relation_definitions, article_title
    )
    logger.info(f"  → {len(relation_map)} relations canonicalized")

    logger.info("Step 7: Inducing schema...")
    entity_concepts, relation_concepts = induce_schema(
        triples, relation_definitions, article_title
    )
    logger.info(f"  → {len(entity_concepts)} entity concepts")
    logger.info(f"  → {len(relation_concepts)} relation concepts")

    logger.info("Step 8: Assembling graph...")
    kg = assemble_graph(
        article_title        = article_title,
        resolved_triples     = triples,
        entity_map           = entity_map,
        relation_map         = relation_map,
        relation_definitions = relation_definitions,
        entity_concepts      = entity_concepts,
        relation_concepts    = relation_concepts,
    )

    path = save_graph(kg, output_dir)

    logger.info(f"{'='*60}")
    logger.info(f"Pipeline complete for '{article_title}'")
    logger.info(f"  Nodes:     {len(kg['nodes'])}")
    logger.info(f"  Relations: {len(kg['relations'])}")
    logger.info(f"  Triples:   {len(kg['triples'])}")
    logger.info(f"  Saved to:  {path}")
    logger.info(f"{'='*60}")

    return kg


def run_single_essay(essay_path: str, output_dir: str = config.DATA_OUTPUT_DIR) -> dict:
    """
    Entry point for a single essay .txt file.
    Uses essay chunking via run_pipeline_from_text(..., dataset="essay").
    """
    if not os.path.exists(essay_path):
        raise FileNotFoundError(f"Essay file not found: {essay_path}")

    with open(essay_path, "r", encoding="utf-8") as f:
        text = f.read()

    if not text.strip():
        raise ValueError(f"Essay file is empty: {essay_path}")

    title = os.path.splitext(os.path.basename(essay_path))[0]

    return run_pipeline_from_text(
        text=text,
        title=title,
        dataset="essay",
        output_dir=output_dir,
        save_jsonl=False,
    )


# ─────────────────────────────────────────────────────────────
# Checkpoint helpers
# ─────────────────────────────────────────────────────────────

def _load_checkpoint(checkpoint_file: str) -> set:
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)
            completed = set(data.get("completed", []))
            logger.info(f"Checkpoint loaded: {len(completed)} articles already done")
            return completed
        except Exception as e:
            logger.warning(f"Could not load checkpoint: {e} — starting fresh")
    return set()


def _save_checkpoint(completed: set, checkpoint_file: str):
    os.makedirs(os.path.dirname(checkpoint_file), exist_ok=True)
    with open(checkpoint_file, "w") as f:
        json.dump({"completed": list(completed)}, f, indent=2)


def _load_errors(error_log_file: str) -> list:
    if os.path.exists(error_log_file):
        try:
            with open(error_log_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_errors(errors: list, error_log_file: str):
    os.makedirs(os.path.dirname(error_log_file), exist_ok=True)
    with open(error_log_file, "w") as f:
        json.dump(errors, f, indent=2)


# ─────────────────────────────────────────────────────────────
# JSONL bulk runner
# ─────────────────────────────────────────────────────────────

def run_jsonl(
    jsonl_path:   str = config.JSONL_INPUT_FILE,
    output_dir:   str = config.DATA_OUTPUT_DIR,
    max_articles: int = config.MAX_ARTICLES,
    dataset:      str = "wiki",           # ← "wiki" or "essay"
):
    os.makedirs(output_dir, exist_ok=True)

    if dataset == "essay":
        checkpoint_file = config.ESSAY_CHECKPOINT_FILE
        error_log_file = config.ESSAY_ERROR_LOG_FILE
        kg_jsonl_path = config.ESSAY_OUTPUT_KG_JSONL
    else:
        checkpoint_file = config.WIKI_CHECKPOINT_FILE
        error_log_file = config.WIKI_ERROR_LOG_FILE
        kg_jsonl_path = config.WIKI_OUTPUT_KG_JSONL

    if not os.path.exists(jsonl_path):
        logger.error(f"JSONL file not found: {jsonl_path}")
        return

    completed = _load_checkpoint(checkpoint_file)
    errors    = _load_errors(error_log_file)

    articles = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    articles.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSONL line: {e}")

    total = len(articles)
    logger.info(f"Total articles in file: {total} | dataset={dataset}")

    if max_articles is not None:
        articles = articles[:max_articles]

    if dataset == "essay":
        pending = [
            a for i, a in enumerate(articles, 1)
            if str(a.get("id", i)) not in completed
        ]
    else:
        pending = [
            a for i, a in enumerate(articles, 1)
            if str(a.get("id", a.get("title", f"article_{i}"))) not in completed
        ]
    logger.info(f"Already done: {len(completed)} | Pending: {len(pending)}")

    success_count = 0
    fail_count    = 0

    def process_article(args):
        i, article = args

        # ── field names differ between wiki and essay datasets ──
        if dataset == "essay":
            article_title = article.get("essay_title", article.get("essay_topic", ""))
            article_id    = str(article.get("id", i))
            article_title = article_title or article_id
            article_text  = article.get("essay_content", "")
        else:
            article_id    = str(article.get("id", article.get("title", f"article_{i}")))
            article_title = article.get("title", article_id)
            article_text  = article.get("text", "")

        if article_id in completed:
            logger.info(f"[{i}] Skipping '{article_title}' (already done)")
            return "skip", article_id, article_title

        if not article_text.strip():
            logger.warning(f"[{i}] Empty text for '{article_title}' — skipping")
            return "fail", article_id, article_title, "empty text"

        try:
            run_pipeline_from_text(
                text       = article_text,
                title      = article_title,
                dataset    = dataset,
                output_dir = output_dir,
                kg_jsonl_path = kg_jsonl_path,
            )
            return "success", article_id, article_title
        except Exception as e:
            logger.error(f"[{i}] FAILED '{article_title}': {e}")
            return "fail", article_id, article_title, str(e)

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.ARTICLE_PARALLEL) as executor:
        futures = {
            executor.submit(process_article, arg): arg
            for arg in enumerate(articles, 1)
        }
        for future in concurrent.futures.as_completed(futures):
            result        = future.result()
            status        = result[0]
            article_id    = result[1]
            article_title = result[2]

            if status == "success":
                completed.add(article_id)
                _save_checkpoint(completed, checkpoint_file)
                success_count += 1
            elif status == "fail":
                error_msg = result[3] if len(result) > 3 else "empty text"
                errors.append({"id": article_id, "title": article_title, "error": error_msg})
                _save_errors(errors, error_log_file)
                fail_count += 1

    logger.info(f"\n{'='*60}")
    logger.info("BULK RUN COMPLETE")
    logger.info(f"  Successful: {success_count}")
    logger.info(f"  Failed:     {fail_count}")
    logger.info(f"  Output:     {kg_jsonl_path}")
    logger.info(f"  Checkpoint: {checkpoint_file}")
    logger.info(f"  Errors:     {error_log_file}")
    logger.info(f"{'='*60}")


# ─────────────────────────────────────────────────────────────
# Legacy: run all .txt files in data/raw/
# ─────────────────────────────────────────────────────────────

def run_all(data_dir: str = config.DATA_RAW_DIR, output_dir: str = config.DATA_OUTPUT_DIR):
    articles = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.endswith(".txt")
    ]

    if not articles:
        logger.warning(f"No .txt files found in {data_dir}")
        return

    logger.info(f"Found {len(articles)} articles to process")

    results = []
    for i, path in enumerate(articles, 1):
        logger.info(f"\nProcessing article {i}/{len(articles)}: {path}")
        try:
            kg = run_pipeline(path, output_dir)
            results.append({
                "article":   kg["article_title"],
                "nodes":     len(kg["nodes"]),
                "relations": len(kg["relations"]),
                "triples":   len(kg["triples"]),
                "status":    "success"
            })
        except Exception as e:
            logger.error(f"Failed on {path}: {e}")
            results.append({"article": path, "status": "failed", "error": str(e)})

    logger.info(f"\n{'='*60}")
    logger.info("PIPELINE SUMMARY")
    logger.info(f"{'='*60}")
    for r in results:
        if r["status"] == "success":
            logger.info(
                f"  ✅ {r['article']:30s} | "
                f"nodes: {r['nodes']:4d} | "
                f"relations: {r['relations']:3d} | "
                f"triples: {r['triples']:4d}"
            )
        else:
            logger.info(f"  ❌ {r['article']:30s} | FAILED: {r['error']}")


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]

    if not args:
        # No args → run all .txt files in data/raw/
        run_all()

    elif args[0] == "--jsonl":
        # Wiki JSONL bulk mode
        # python main.py --jsonl
        # python main.py --jsonl path/to/articles.jsonl
        jsonl_path = args[1] if len(args) > 1 else config.WIKI_JSONL_INPUT_FILE
        run_jsonl(jsonl_path=jsonl_path, dataset="wiki")

    elif args[0] == "--essay":
        # Essay JSONL bulk mode
        # python main.py --essay
        # python main.py --essay path/to/essays.jsonl
        jsonl_path = args[1] if len(args) > 1 else config.ESSAY_JSONL_INPUT_FILE
        run_jsonl(jsonl_path=jsonl_path, dataset="essay")

    elif args[0] == "--essay-txt":
        # Single essay .txt mode
        # python main.py --essay-txt data/mine_raw/essay1.txt
        if len(args) < 2:
            raise ValueError("Usage: python main.py --essay-txt <path/to/essay.txt>")
        run_single_essay(args[1])

    else:
        # Single article .txt mode
        # python main.py data/raw/article_1.txt
        run_pipeline(args[0])