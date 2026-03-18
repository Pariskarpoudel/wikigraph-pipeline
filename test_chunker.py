from pipeline.chunker import chunk_article

chunks = chunk_article("data/raw/article_1.txt")
# for c in chunks[:4]:
#     print(f"\n[{c['chunk_index']}] {c['article_title']} | {c['section_path']} (~{c['token_approx']} tokens)")
#     print(c['chunk_text'][:200])
print(chunks)