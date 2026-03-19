# main.py
import os
import json
import logging
import config
from pipeline.chunker import chunk_article
from pipeline.extractor import extract_all_triples
from pipeline.deduplicator import deduplicate_triples
from pipeline.entity_resolver import resolve_entities
from pipeline.relation_definer import define_relations
from pipeline.relation_canonicalizer import canonicalize_relations
from pipeline.schema_inducer import induce_schema
from pipeline.graph_assembler import assemble_graph, save_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


def run_pipeline(article_path: str, output_dir: str = config.DATA_OUTPUT_DIR) -> dict:
    """
    Run full KG construction pipeline on a single article.

    Args:
        article_path: path to WikiText-103 article .txt file
        output_dir:   where to save the output KG JSON

    Returns:
        kg — complete knowledge graph dict
    """
    logger.info(f"{'='*60}")
    logger.info(f"Starting pipeline for: {article_path}")
    logger.info(f"{'='*60}")

    # ── Step 1: Chunking ──────────────────────────────────────
    logger.info("Step 1: Chunking article...")
    chunks = chunk_article(article_path)
    logger.info(f"  → {len(chunks)} chunks")

    if not chunks:
        raise ValueError(f"No chunks produced from {article_path}")

    article_title = chunks[0]["article_title"]
    logger.info(f"  → Article: '{article_title}'")

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
    # triples -> entityresolved triples
    # entity_map : entity_to_canonical mapping 
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

    # ── Save ──────────────────────────────────────────────────
    path = save_graph(kg, output_dir)

    # ── Summary ───────────────────────────────────────────────
    logger.info(f"{'='*60}")
    logger.info(f"Pipeline complete for '{article_title}'")
    logger.info(f"  Nodes:     {len(kg['nodes'])}")
    logger.info(f"  Relations: {len(kg['relations'])}")
    logger.info(f"  Triples:   {len(kg['triples'])}")
    logger.info(f"  Saved to:  {path}")
    logger.info(f"{'='*60}")

    return kg


def run_all(data_dir: str = config.DATA_RAW_DIR, output_dir: str = config.DATA_OUTPUT_DIR):
    """
    Run pipeline on all articles in data_dir.
    """
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
            results.append({
                "article": path,
                "status":  "failed",
                "error":   str(e)
            })

    # Print summary table
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


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        # Single article mode
        # python main.py data/raw/article_1.txt
        run_pipeline(sys.argv[1])

    else:
        # Run all articles in data/raw/
        # python main.py
        run_all()