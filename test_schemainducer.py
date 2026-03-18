import logging
logging.basicConfig(level=logging.INFO)

from pipeline.relation_definer import define_relations
from pipeline.schema_inducer import induce_schema

triples = [
    {"subject": "Marie Curie",         "relation": "born in",       "object": "Warsaw"},
    {"subject": "Marie Curie",         "relation": "discovered",     "object": "Polonium"},
    {"subject": "Marie Curie",         "relation": "won",            "object": "Nobel Prize in Physics"},
    {"subject": "Marie Curie",         "relation": "worked at",      "object": "University of Paris"},
    {"subject": "Marie Curie",         "relation": "married",        "object": "Pierre Curie"},
    {"subject": "Pierre Curie",        "relation": "died in",        "object": "1906"},
    {"subject": "Pierre Curie",        "relation": "won",            "object": "Nobel Prize in Physics"},
    {"subject": "Polonium",            "relation": "named after",    "object": "Poland"},
    {"subject": "Polonium",            "relation": "discovered by",  "object": "Marie Curie"},
    {"subject": "University of Paris", "relation": "located in",     "object": "Paris"},
    {"subject": "University of Paris", "relation": "founded in",     "object": "1150"},
]

definitions = define_relations(triples, "Marie Curie")
entity_concepts, relation_concepts = induce_schema(triples, definitions, "Marie Curie")

print("\n" + "="*60)
print("ENTITY CONCEPTS")
print("="*60)
for entity, concepts in entity_concepts.items():
    print(f"  '{entity}':")
    print(f"    {concepts}")

print("\n" + "="*60)
print("RELATION CONCEPTS")
print("="*60)
for relation, concepts in relation_concepts.items():
    print(f"  '{relation}':")
    print(f"    {concepts}")