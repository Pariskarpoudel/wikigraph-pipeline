from pipeline.extractor import extract_triples_from_chunk

chunk = {
    "article_title": "Marie Curie",
    "section_path": "Early Life and Career",
    "chunk_index": 0,
    "chunk_text": """Marie Skłodowska Curie was a physicist and chemist who conducted pioneering research on radioactivity. She was born Maria Salomea Skłodowska on 7 November 1867 in Warsaw, in what was then the Kingdom of Poland, part of the Russian Empire. She was the youngest of five children of Władysław Skłodowski, a mathematics and physics teacher, and Bronisława Boguska, who died of tuberculosis when Marie was ten years old. In 1891, at age 24, Curie moved to Paris to study at the Sorbonne, where she obtained degrees in physics (1893) and mathematics (1894). In 1894 she met Pierre Curie, a physicist eight years her senior; they married in 1895 in Sceaux. Together they investigated uranium rays discovered by Henri Becquerel in 1896. In 1898 the Curies announced the discovery of two new elements: polonium (named after Marie's native Poland) and radium. They isolated radium in its pure metallic state in 1910. Marie Curie became the first woman to win a Nobel Prize (Physics, 1903, shared with Pierre Curie and Henri Becquerel) and the first person to win two Nobel Prizes (second in Chemistry, 1911, for her work on radium and polonium). After Pierre's tragic death in a 1906 street accident, she took over his professorship at the Sorbonne, becoming the university's first female professor. During World War I she developed mobile radiography units ("Little Curies") to treat wounded soldiers."""
}

triples = extract_triples_from_chunk(chunk)
for t in triples:
    print(t)
print(f"\nTotal: {len(triples)}")

# from pipeline.chunker import chunk_article
# from pipeline.extractor import extract_all_triples

# chunks = chunk_article("data/raw/article_1.txt")
# print(len(chunks))
# triples = extract_all_triples(chunks)

# for t in triples[:10]:
#     print(t)
# print(f"\nTotal: {len(triples)}")