# data/sample.py
from datasets import load_dataset
import re
import os

dataset = load_dataset("wikitext", "wikitext-103-raw-v1", split="train")

full_text = "\n".join(row['text'] for row in dataset)

# Split on top-level headings
parts = re.split(r'\n( = (?!=))', full_text)

# Reconstruct articles with the = prefix restored
articles = []
for i in range(1, len(parts) - 1, 2):
    heading = parts[i]        # " = "
    body = parts[i + 1]       # "Title = \n\n content..."
    full_article = heading + body
    if len(full_article.strip()) > 2000:
        articles.append(full_article.strip())

print(f"Found {len(articles)} articles")

os.makedirs("data/raw", exist_ok=True)
for i, article in enumerate(articles[:5]):
    path = f"data/raw/article_{i+1}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(article)
    print(f"Saved: {path} — {article[:60].strip()}")