import argparse
import json

from pipeline.chunker import chunk_article, chunk_essay_from_text


def _preview_chunks(chunks, limit: int):
	print(f"Total chunks: {len(chunks)}")
	for c in chunks[:limit]:
		print(
			f"\n[{c['chunk_index']}] {c['article_title']} | "
			f"{c['section_path']} (~{c['token_approx']} tokens)"
		)
		print(c["chunk_text"][:250])


def main():
	parser = argparse.ArgumentParser(description="Quick chunker test runner")
	parser.add_argument(
		"--article-txt",
		default="data/raw/article_1.txt",
		help="Path to one article .txt file",
	)
	parser.add_argument(
		"--essay-txt",
		default=None,
		help="Path to one essay .txt file (uses essay chunking)",
	)
	parser.add_argument(
		"--preview",
		type=int,
		default=5,
		help="How many chunks to preview",
	)
	parser.add_argument(
		"--all-chunks",
		action="store_true",
		help="Print all chunks (no preview)",
	)
	args = parser.parse_args()

	if args.essay_txt:
		with open(args.essay_txt, "r", encoding="utf-8") as f:
			text = f.read()
		title = args.essay_txt.split("/")[-1].split("\\")[-1].rsplit(".", 1)[0]
		chunks = chunk_essay_from_text(text, fallback_title=title)
		print(f"Mode: essay | File: {args.essay_txt}")
	else:
		chunks = chunk_article(args.article_txt)
		print(f"Mode: article | File: {args.article_txt}")

	if args.all_chunks:
		print(json.dumps(chunks, indent=2, ensure_ascii=False))
	else:
		_preview_chunks(chunks, args.preview)


if __name__ == "__main__":
	main()