# test_entity_resolver.py
import logging
logging.basicConfig(level=logging.INFO)

from pipeline.entity_resolver import resolve_entities

# Simulating realistic article-level triples across multiple chunks
# More context per entity → better embeddings → better resolution
triples = [
    # Marie Curie variants — many triples across chunks
    {"subject": "Marie Skłodowska Curie", "relation": "born in",          "object": "Warsaw"},
    {"subject": "Marie Skłodowska Curie", "relation": "born on",          "object": "7 November 1867"},
    {"subject": "Marie Skłodowska Curie", "relation": "nationality",      "object": "Polish-French"},
    {"subject": "Marie Curie",            "relation": "discovered",        "object": "Polonium"},
    {"subject": "Marie Curie",            "relation": "discovered",        "object": "Radium"},
    {"subject": "Marie Curie",            "relation": "won",               "object": "Nobel Prize in Physics"},
    {"subject": "Marie Curie",            "relation": "won",               "object": "Nobel Prize in Chemistry"},
    {"subject": "Marie Curie",            "relation": "worked at",         "object": "University of Paris"},
    {"subject": "M. Curie",               "relation": "married",           "object": "Pierre Curie"},
    {"subject": "M. Curie",               "relation": "conducted",         "object": "radioactivity research"},
    {"subject": "M. Curie",               "relation": "developed",         "object": "mobile radiography units"},
    {"subject": "Curie",                  "relation": "studied at",        "object": "Sorbonne"},
    {"subject": "Curie",                  "relation": "became",            "object": "first female professor at Sorbonne"},
    {"subject": "Curie",                  "relation": "pioneered",         "object": "radioactivity research"},

    # Pierre Curie variants
    {"subject": "Pierre Curie",           "relation": "married",           "object": "Marie Curie"},
    {"subject": "Pierre Curie",           "relation": "won",               "object": "Nobel Prize in Physics"},
    {"subject": "Pierre Curie",           "relation": "worked at",         "object": "University of Paris"},
    {"subject": "Pierre",                 "relation": "died in",           "object": "1906"},
    {"subject": "Pierre",                 "relation": "died in",           "object": "street accident"},
    {"subject": "Pierre",                 "relation": "collaborated with", "object": "Marie Curie"},

    # Sorbonne / University of Paris variants
    {"subject": "University of Paris",    "relation": "located in",        "object": "Paris"},
    {"subject": "University of Paris",    "relation": "founded in",        "object": "1150"},
    {"subject": "Sorbonne",               "relation": "employed",          "object": "Marie Curie"},
    {"subject": "Sorbonne",               "relation": "located in",        "object": "Paris"},

    # standalone entities
    {"subject": "Polonium",               "relation": "discovered by",     "object": "Marie Curie"},
    {"subject": "Polonium",               "relation": "named after",       "object": "Poland"},
    {"subject": "Radium",                 "relation": "isolated by",       "object": "Marie Curie"},
    {"subject": "Nobel Prize in Physics", "relation": "awarded in",        "object": "1903"},
    {"subject": "radioactivity research", "relation": "pioneered by",      "object": "Marie Curie"},
]

resolved_triples, entity_map = resolve_entities(triples, "Marie Curie")

print("\n" + "="*50)
print("ENTITY MAP")
print("="*50)
for variant, canonical in entity_map.items():
    marker = "→" if variant != canonical else "="
    print(f"  {variant:35s} {marker}  {canonical}")

print("\n" + "="*50)
print("RESOLVED TRIPLES")
print("="*50)
for t in resolved_triples:
    print(f"  {t['subject']:35s} | {t['relation']:30s} | {t['object']}")

print("\n" + "="*50)
print("STATS")
print("="*50)
merged = sum(1 for k, v in entity_map.items() if k != v)
print(f"  Total entities:   {len(entity_map)}")
print(f"  Merged variants:  {merged}")
print(f"  Canonical names:  {len(set(entity_map.values()))}")