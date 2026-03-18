# test_relation_definer.py
import logging
logging.basicConfig(level=logging.INFO)

from pipeline.relation_definer import define_relations

# Realistic article-level triples — variety of relation types
triples = [
    {"subject": "Marie Curie",          "relation": "born in",          "object": "Warsaw"},
    {"subject": "Marie Curie",          "relation": "born on",          "object": "7 November 1867"},
    {"subject": "Marie Curie",          "relation": "discovered",       "object": "Polonium"},
    {"subject": "Marie Curie",          "relation": "discovered",       "object": "Radium"},
    {"subject": "Marie Curie",          "relation": "won",              "object": "Nobel Prize in Physics"},
    {"subject": "Marie Curie",          "relation": "won",              "object": "Nobel Prize in Chemistry"},
    {"subject": "Marie Curie",          "relation": "studied at",       "object": "University of Paris"},
    {"subject": "Marie Curie",          "relation": "worked at",        "object": "University of Paris"},
    {"subject": "Marie Curie",          "relation": "married",          "object": "Pierre Curie"},
    {"subject": "Marie Curie",          "relation": "pioneered",        "object": "radioactivity research"},
    {"subject": "Marie Curie",          "relation": "developed",        "object": "mobile radiography units"},
    {"subject": "Marie Curie",          "relation": "became",           "object": "first female professor"},
    {"subject": "Pierre Curie",         "relation": "collaborated with","object": "Marie Curie"},
    {"subject": "Pierre Curie",         "relation": "died in",          "object": "1906"},
    {"subject": "Pierre Curie",         "relation": "died of",          "object": "street accident"},
    {"subject": "Polonium",             "relation": "named after",      "object": "Poland"},
    {"subject": "Polonium",             "relation": "discovered by",    "object": "Marie Curie"},
    {"subject": "University of Paris",  "relation": "located in",       "object": "Paris"},
    {"subject": "University of Paris",  "relation": "founded in",       "object": "1150"},
    {"subject": "Nobel Prize",          "relation": "awarded in",       "object": "1903"},
]

definitions = define_relations(triples, "Marie Curie")

print("\n" + "="*60)
print("RELATION DEFINITIONS")
print("="*60)
for relation, definition in definitions.items():
    print(f"\n  '{relation}':")
    print(f"    {definition}")

print("\n" + "="*60)
print("STATS")
print("="*60)
print(f"  Unique relations:  {len(triples)} triples → {len(definitions)} definitions")