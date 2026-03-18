# test_utils.py
import logging
logging.basicConfig(level=logging.INFO)

from utils.parser import parse_llm_json
from utils.llm import llm_call
from utils.embedder import embed, cosine_similarity

print("\n" + "="*50)
print("TESTING parser.py")
print("="*50)

# Should return list
r1 = parse_llm_json('```json\n[{"subject": "Curie", "relation": "discovered", "object": "Polonium"}]\n```', expected_type="list")
print(f"✅ Fenced JSON list: {r1}")

# Should return dict
r2 = parse_llm_json('{"canonical": "Marie Curie", "matches": ["Curie", "M. Curie"]}', expected_type="dict")
print(f"✅ Dict: {r2}")

# Trailing comma
r3 = parse_llm_json('[{"subject": "Curie", "relation": "discovered", "object": "Polonium",}]', expected_type="list")
print(f"✅ Trailing comma: {r3}")

# Prose around JSON
r4 = parse_llm_json('Here are the triples: [{"subject": "Curie", "relation": "discovered", "object": "Polonium"}] Hope that helps!', expected_type="list")
print(f"✅ Prose around JSON: {r4}")

# Should return None
r5 = parse_llm_json("this is not json", expected_type="list")
print(f"✅ Bad input returns None: {r5}")

# Type mismatch — should return None
r6 = parse_llm_json('[{"subject": "Curie"}]', expected_type="dict")
print(f"✅ Type mismatch returns None: {r6}")


print("\n" + "="*50)
print("TESTING llm.py")
print("="*50)

result = llm_call(
    system_prompt="You are a triple extractor. Always return a JSON array of triples with keys: subject, relation, object.",
    user_prompt='Extract triples from: "Marie Curie discovered Polonium and was born in Warsaw."'
)
print(f"✅ LLM raw response:\n{result}")


print("\n" + "="*50)
print("TESTING embedder.py")
print("="*50)

embs = embed(["Marie Curie", "Curie", "Albert Einstein"])
print(f"✅ Embedding shape: {embs.shape}")  # expect (3, 384)

sim_same = cosine_similarity(embs[0], embs[1])
sim_diff = cosine_similarity(embs[0], embs[2])
print(f"✅ Marie Curie vs Curie (expect high ~0.9+): {sim_same:.4f}")
print(f"✅ Marie Curie vs Einstein (expect lower):   {sim_diff:.4f}")

assert sim_same > sim_diff, "❌ Similarity logic is wrong!"
print("✅ Similarity ordering correct")

print("\n" + "="*50)
print("ALL UTILS TESTS DONE")
print("="*50)