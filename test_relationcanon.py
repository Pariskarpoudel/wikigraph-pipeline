import logging
logging.basicConfig(level=logging.INFO)

from pipeline.relation_definer import define_relations
from pipeline.relation_canonicalizer import canonicalize_relations

# Realistic triples with relation variants — simulating article-level extraction
triples = [
    # born in variants
    {"subject": "Marie Curie",          "relation": "born in",          "object": "Warsaw"},
    {"subject": "Pierre Curie",         "relation": "was born in",      "object": "Paris"},
    {"subject": "Henri Becquerel",      "relation": "birthplace",       "object": "Paris"},

    # discovered variants
    {"subject": "Marie Curie",          "relation": "discovered",       "object": "Polonium"},
    {"subject": "Marie Curie",          "relation": "discovered",       "object": "Radium"},
    {"subject": "Henri Becquerel",      "relation": "identified",       "object": "uranium rays"},
    {"subject": "Polonium",             "relation": "discovered by",    "object": "Marie Curie"},

    # worked at variants
    {"subject": "Marie Curie",          "relation": "worked at",        "object": "University of Paris"},
    {"subject": "Pierre Curie",         "relation": "employed at",      "object": "University of Paris"},
    {"subject": "Henri Becquerel",      "relation": "affiliated with",  "object": "Museum of Natural History"},

    # won variants
    {"subject": "Marie Curie",          "relation": "won",              "object": "Nobel Prize in Physics"},
    {"subject": "Marie Curie",          "relation": "awarded",          "object": "Nobel Prize in Chemistry"},
    {"subject": "Pierre Curie",         "relation": "received",         "object": "Nobel Prize in Physics"},

    # died variants
    {"subject": "Pierre Curie",         "relation": "died in",          "object": "1906"},
    {"subject": "Marie Curie",          "relation": "died in",          "object": "1934"},
    {"subject": "Pierre Curie",         "relation": "died of",          "object": "street accident"},

    # location variants
    {"subject": "University of Paris",  "relation": "located in",       "object": "Paris"},
    {"subject": "Museum of Natural History", "relation": "situated in", "object": "Paris"},

    # misc
    {"subject": "Marie Curie",          "relation": "married",          "object": "Pierre Curie"},
    {"subject": "Polonium",             "relation": "named after",      "object": "Poland"},
    {"subject": "Nobel Prize in Physics","relation": "awarded in",      "object": "1903"},

    # to test if if long relation gets normalized or not
    {"subject": "Marie Curie", "relation": "was appointed as a professor at", "object": "University of Paris"},
]

# Step 1 — define relations
definitions = define_relations(triples, "Marie Curie")

print("\n" + "="*60)
print("RELATION DEFINITIONS")
print("="*60)
for rel, defn in definitions.items():
    print(f"  '{rel}':\n    {defn}")

# Step 2 — canonicalize
resolved_triples, relation_map = canonicalize_relations(
    triples, definitions, "Marie Curie"
)

print("\n" + "="*60)
print("RELATION MAP")
print("="*60)
for variant, canonical in relation_map.items():
    marker = "→" if variant != canonical else "="
    print(f"  '{variant:25s}' {marker}  '{canonical}'")

print("\n" + "="*60)
print("RESOLVED TRIPLES")
print("="*60)
for t in resolved_triples:
    print(f"  {t['subject']:30s} | {t['relation']:20s} | {t['object']}")

print("\n" + "="*60)
print("STATS")
print("="*60)
merged = sum(1 for k, v in relation_map.items() if k != v)
print(f"  Total relations:  {len(relation_map)}")
print(f"  Merged variants:  {merged}")
print(f"  Canonical names:  {len(set(relation_map.values()))}")
