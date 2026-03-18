# pipeline/graph_assembler.py
import json
import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)


def assemble_graph(
    article_title:        str,
    resolved_triples:     List[Dict],
    entity_map:           Dict[str, str],
    relation_map:         Dict[str, str],
    relation_definitions: Dict[str, str],
    entity_concepts:      Dict[str, List[str]],
    relation_concepts:    Dict[str, List[str]],
) -> Dict:

    # All unique nodes — subjects and objects ( entities and literals )
    all_nodes = set()
    for t in resolved_triples:
        all_nodes.add(t["subject"])
        all_nodes.add(t["object"])

    # Build node dict — entities get concepts, literals get empty
    nodes = {
        node: {
            "concepts": entity_concepts.get(node, [])
            # empty list for literals — no concepts assigned
        }
        for node in all_nodes
    }

    # Build relation dict
    relations = {
        t["relation"]: {
            "definition": relation_definitions.get(t["relation"], ""),
            "concepts":   relation_concepts.get(t["relation"], [])
        }
        for t in resolved_triples
    }

    kg = {
        "article_title":  article_title,
        "nodes":          nodes,
        "relations":      relations,
        "triples":        resolved_triples,
        "entity_map":     entity_map,
        "relation_map":   relation_map,
    }

    logger.info(
        f"Graph assembled: {len(nodes)} nodes, "
        f"{len(relations)} relations, "
        f"{len(resolved_triples)} triples"
    )
    return kg


def save_graph(kg: Dict, output_dir: str = "data/output") -> str:
    """
    Save knowledge graph to JSON file.
    Returns path to saved file.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Sanitize title for filename
    filename = kg["article_title"].replace(" ", "_").replace("/", "_") + ".json"
    path     = os.path.join(output_dir, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)

    logger.info(f"Graph saved to: {path}")
    return path


def load_graph(path: str) -> Dict:
    """Load a saved knowledge graph from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
# Keeping this in graph_assembler.py as a utility for later (if needed):
def concepts_to_triples(kg: Dict) -> List[Dict]:
    """Convert concept metadata to triples when needed for downstream tasks."""
    concept_triples = []
    for entity, data in kg["nodes"].items():
        for concept in data.get("concepts", []):
            concept_triples.append({
                "subject":  entity,
                "relation": "type",
                "object":   concept
            })
    for relation, data in kg["relations"].items():
        for concept in data.get("concepts", []):
            concept_triples.append({
                "subject":  relation,
                "relation": "category",
                "object":   concept
            })
    return concept_triples