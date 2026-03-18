from pipeline.deduplicator import deduplicate_triples

triples = [
    {"subject": "Marie Curie", "relation": "born in", "object": "Warsaw"},
    {"subject": "Marie Curie", "relation": "born in", "object": "Warsaw"},  # exact dup
    {"subject": "marie curie", "relation": "born in", "object": "warsaw"},  # case dup
    {"subject": "Marie Curie", "relation": "discovered", "object": "Polonium"},
]

result = deduplicate_triples(triples)
for t in result:
    print(t)
print(f"\nTotal: {len(result)}")  # expect 2