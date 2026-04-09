# evaluate/evaluate.py
#
# QA-based evaluation of KG quality against source article.
# No ground truth needed — questions generated from article text,
# answered from KG triples, compared against text-based answers.
#
# Usage:
#   python evaluate/evaluate.py data/output/Plain_maskray.json data/raw/article_5.txt
#   python evaluate/evaluate.py --all
#
# Output:
#   evaluate/results/<article>_qa.json   — per-question results
#   evaluate/results/summary.txt         — score table across all articles

import os
import json
import sys
import time
import logging
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.llm import llm_call
from utils.parser import parse_llm_json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

RESULTS_DIR   = "evaluate/results"
NUM_QUESTIONS = 20   # how many questions to generate per article


# ─────────────────────────────────────────────────────────────
# Step 1 — Generate questions from article text
# ─────────────────────────────────────────────────────────────

QUESTION_GEN_SYSTEM = """You are an expert at generating factual questions from text.
Given an article, generate diverse factual questions that test whether key facts are captured.
Cover different aspects: taxonomy, biology, behavior, geography, history, conservation, people, dates, numbers.
Output JSON only. No explanation outside JSON."""


def generate_questions(article_text: str, article_title: str, n: int = NUM_QUESTIONS) -> List[str]:
    """Generate N factual questions from article text."""

    user_prompt = f"""Article title: {article_title}

Article text:
\"\"\"
{article_text[:5000]}
\"\"\"

Generate exactly {n} diverse factual questions about this article.
Questions should be specific and answerable from the article.
Questions should be relevant and important — avoid trivial or overly broad questions.

Output format:
{{
  "questions": [
    "What family does the plain maskray belong to?",
    "Who first described the plain maskray scientifically?",
    ...
  ]
}}"""

    raw = llm_call(
        system_prompt=QUESTION_GEN_SYSTEM,
        user_prompt=user_prompt,
        model=config.LLM_DEFAULT_MODEL
    )

    result = parse_llm_json(raw, expected_type="dict")

    if result is None or "questions" not in result:
        logger.warning("Question generation failed")
        return []

    questions = [q for q in result["questions"] if isinstance(q, str) and q.strip()]
    logger.info(f"Generated {len(questions)} questions")
    return questions[:n]


# ─────────────────────────────────────────────────────────────
# Step 2 — Answer questions from KG triples only
# ─────────────────────────────────────────────────────────────

KG_ANSWER_SYSTEM = """You are a knowledge graph query engine.
You will be given a set of knowledge graph triples and a question.
Answer the question using ONLY the triples provided.
If the answer cannot be found in the triples, say exactly: "NOT IN KG"
Be concise — one sentence maximum.
Output JSON only."""


def answer_from_kg(question: str, triples: List[Dict], article_title: str) -> str:
    """Answer a question using only KG triples."""

    # Format triples as readable text
    triples_text = "\n".join(
        f"({t['subject']}, {t['relation']}, {t['object']})"
        for t in triples
    )

    user_prompt = f"""Article: {article_title}

Knowledge graph triples:
{triples_text}

Question: {question}

Answer using ONLY the triples above. If not found say "NOT IN KG".

Output format:
{{"answer": "your answer here"}}"""

    raw = llm_call(
        system_prompt=KG_ANSWER_SYSTEM,
        user_prompt=user_prompt,
        model=config.LLM_DEFAULT_MODEL
    )

    result = parse_llm_json(raw, expected_type="dict")

    if result is None or "answer" not in result:
        return "PARSE FAILED"

    return str(result["answer"]).strip()


# ─────────────────────────────────────────────────────────────
# Step 3 — Answer questions from article text (ground truth)
# ─────────────────────────────────────────────────────────────

TEXT_ANSWER_SYSTEM = """You are a precise question answering system.
Answer the question using ONLY the article text provided.
Be concise — one sentence maximum.
Output JSON only."""


def answer_from_text(question: str, article_text: str, article_title: str) -> str:
    """Answer a question from article text — this is the ground truth answer."""

    user_prompt = f"""Article: {article_title}

Article text:
\"\"\"
{article_text[:5000]}
\"\"\"

Question: {question}

Answer using ONLY the article text above.

Output format:
{{"answer": "your answer here"}}"""

    raw = llm_call(
        system_prompt=TEXT_ANSWER_SYSTEM,
        user_prompt=user_prompt,
        model=config.LLM_DEFAULT_MODEL
    )

    result = parse_llm_json(raw, expected_type="dict")

    if result is None or "answer" not in result:
        return "PARSE FAILED"

    return str(result["answer"]).strip()


# ─────────────────────────────────────────────────────────────
# Step 4 — Compare KG answer vs text answer
# ─────────────────────────────────────────────────────────────

COMPARE_SYSTEM = """You are evaluating whether two answers convey the same information.
Compare the KG answer against the reference text answer.
Be strict but fair — minor wording differences are fine, but missing key facts are not.
Output JSON only."""


def compare_answers_batch(questions: List[str], kg_answers: List[str], text_answers: List[str]) -> List[Dict]:
    """
    Compare KG answers vs text answers in one batched LLM call.
    Returns list of {verdict, score, reason} per question.
    """

    comparisons_block = "\n\n".join(
        f'{i+1}. Question: {q}\n   Text answer: {ta}\n   KG answer:   {ka}'
        for i, (q, ta, ka) in enumerate(zip(questions, text_answers, kg_answers))
    )

    user_prompt = f"""Compare each KG answer against the reference text answer.

Scoring:
- 1.0 = KG answer is correct and complete
- 0.5 = KG answer is partially correct or missing some detail
- 0.0 = KG answer is wrong, irrelevant, or "NOT IN KG"

{comparisons_block}

Output format:
{{
  "1": {{"verdict": "correct", "score": 1.0, "reason": "..."}},
  "2": {{"verdict": "partial", "score": 0.5, "reason": "..."}},
  "3": {{"verdict": "incorrect", "score": 0.0, "reason": "..."}},
  ...
}}"""

    raw = llm_call(
        system_prompt=COMPARE_SYSTEM,
        user_prompt=user_prompt,
        model=config.LLM_DEFAULT_MODEL
    )

    result = parse_llm_json(raw, expected_type="dict")

    comparisons = []
    for i in range(len(questions)):
        key   = str(i + 1)
        entry = result.get(key, {}) if result else {}

        # handle score — LLM sometimes returns int, float, or None
        raw_score = entry.get("score", None)
        try:
            score = float(raw_score) if raw_score is not None else None
        except (TypeError, ValueError):
            score = None

        verdict = entry.get("verdict", "unscored")

        # infer verdict from score if missing
        if score is not None and verdict == "unscored":
            if score >= 1.0:
                verdict = "correct"
            elif score >= 0.5:
                verdict = "partial"
            else:
                verdict = "incorrect"

        comparisons.append({
            "verdict": verdict,
            "score":   score,
            "reason":  entry.get("reason", "parse failed")
        })

    return comparisons


# ─────────────────────────────────────────────────────────────
# Main evaluation function
# ─────────────────────────────────────────────────────────────

def evaluate_kg(kg_path: str, article_path: str) -> Dict:
    """
    Run full QA evaluation on a single KG + article pair.
    Returns results dict with per-question scores and summary.
    """

    # Load KG
    with open(kg_path, "r", encoding="utf-8") as f:
        kg = json.load(f)

    # Load article
    with open(article_path, "r", encoding="utf-8") as f:
        article_text = f.read()

    article_title = kg["article_title"]
    triples       = kg["triples"]

    logger.info(f"{'='*60}")
    logger.info(f"Evaluating: '{article_title}'")
    logger.info(f"  KG triples: {len(triples)}")
    logger.info(f"{'='*60}")

    # ── Step 1: Generate questions ────────────────────────────
    logger.info("Step 1: Generating questions from article...")
    questions = generate_questions(article_text, article_title)

    if not questions:
        logger.error("No questions generated — aborting")
        return {}

    # ── Step 2: Answer from KG ────────────────────────────────
    logger.info("Step 2: Answering questions from KG triples...")
    kg_answers = []
    for i, q in enumerate(questions, 1):
        logger.info(f"  KG answer {i}/{len(questions)}: {q[:60]}...")
        ans = answer_from_kg(q, triples, article_title)
        kg_answers.append(ans)
        time.sleep(1)

    # ── Step 3: Answer from text ──────────────────────────────
    logger.info("Step 3: Answering questions from article text...")
    text_answers = []
    for i, q in enumerate(questions, 1):
        logger.info(f"  Text answer {i}/{len(questions)}: {q[:60]}...")
        ans = answer_from_text(q, article_text, article_title)
        text_answers.append(ans)
        time.sleep(1)

    # ── Step 4: Compare in batches of 5 ──────────────────────
    logger.info("Step 4: Comparing KG answers vs text answers...")
    BATCH = 5
    all_comparisons = []

    for i in range(0, len(questions), BATCH):
        batch_q  = questions[i:i+BATCH]
        batch_kg = kg_answers[i:i+BATCH]
        batch_tx = text_answers[i:i+BATCH]
        comps    = compare_answers_batch(batch_q, batch_kg, batch_tx)
        all_comparisons.extend(comps)
        time.sleep(1)

    # ── Build per-question results ────────────────────────────
    qa_results = []
    for q, ka, ta, comp in zip(questions, kg_answers, text_answers, all_comparisons):
        qa_results.append({
            "question":    q,
            "text_answer": ta,
            "kg_answer":   ka,
            "verdict":     comp["verdict"],
            "score":       comp["score"],
            "reason":      comp["reason"],
        })

    # ── Summary stats ─────────────────────────────────────────
    scored    = [r for r in qa_results if r["score"] is not None]
    n_scored  = len(scored)
    n_total   = len(qa_results)

    correct   = sum(1 for r in scored if r["verdict"] == "correct")
    partial   = sum(1 for r in scored if r["verdict"] == "partial")
    incorrect = sum(1 for r in scored if r["verdict"] == "incorrect")
    not_in_kg = sum(1 for r in qa_results if "NOT IN KG" in r["kg_answer"])
    avg_score = sum(r["score"] for r in scored) / n_scored if n_scored > 0 else 0

    summary = {
        "article_title":  article_title,
        "kg_triples":     len(triples),
        "total_questions": n_total,
        "scored":         n_scored,
        "correct":        correct,
        "partial":        partial,
        "incorrect":      incorrect,
        "not_in_kg":      not_in_kg,
        "avg_score":      round(avg_score, 3),
        "coverage":       round((correct + partial) / n_total, 3) if n_total > 0 else 0,
    }

    # Print results clearly
    logger.info(f"\n{'='*60}")
    logger.info(f"RESULTS: '{article_title}'")
    logger.info(f"  Total questions:  {n_total}")
    logger.info(f"  Correct:          {correct}")
    logger.info(f"  Partial:          {partial}")
    logger.info(f"  Incorrect:        {incorrect}")
    logger.info(f"  Not in KG:        {not_in_kg}")
    logger.info(f"  Avg score:        {avg_score:.3f}")
    logger.info(f"  Coverage:         {summary['coverage']:.3f}")
    logger.info(f"{'='*60}\n")

    # Print each question result
    for i, r in enumerate(qa_results, 1):
        verdict_icon = "✅" if r["verdict"] == "correct" else "⚠️" if r["verdict"] == "partial" else "❌"
        logger.info(f"  {verdict_icon} Q{i}: {r['question']}")
        logger.info(f"       Text: {r['text_answer']}")
        logger.info(f"       KG:   {r['kg_answer']}")
        logger.info(f"       → {r['verdict']} | {r['reason']}\n")

    return {
        "summary":    summary,
        "qa_results": qa_results,
    }


# ─────────────────────────────────────────────────────────────
# Save results
# ─────────────────────────────────────────────────────────────

def save_results(output: Dict, article_title: str):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    filename = article_title.replace(" ", "_").replace("/", "_") + "_qa.json"
    path     = os.path.join(RESULTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to: {path}")
    return path


def save_summary_table(all_summaries: List[Dict]):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "summary.txt")

    lines = []
    lines.append("=" * 90)
    lines.append("QA EVALUATION SUMMARY")
    lines.append("=" * 90)
    lines.append(
        f"{'Article':<30} {'Triples':>8} {'Q Total':>8} "
        f"{'Correct':>8} {'Partial':>8} {'Wrong':>7} {'NotInKG':>8} {'Score':>7} {'Coverage':>9}"
    )
    lines.append("-" * 90)

    for s in all_summaries:
        lines.append(
            f"{s['article_title']:<30} "
            f"{s['kg_triples']:>8} "
            f"{s['total_questions']:>8} "
            f"{s['correct']:>8} "
            f"{s['partial']:>8} "
            f"{s['incorrect']:>7} "
            f"{s['not_in_kg']:>8} "
            f"{s['avg_score']:>7.3f} "
            f"{s['coverage']:>9.3f}"
        )

    lines.append("-" * 90)

    if all_summaries:
        avg_score    = sum(s["avg_score"]  for s in all_summaries) / len(all_summaries)
        avg_coverage = sum(s["coverage"]   for s in all_summaries) / len(all_summaries)
        total_q      = sum(s["total_questions"] for s in all_summaries)
        lines.append(
            f"{'OVERALL':<30} {'':>8} {total_q:>8} "
            f"{'':>8} {'':>8} {'':>7} {'':>8} "
            f"{avg_score:>7.3f} {avg_coverage:>9.3f}"
        )

    lines.append("=" * 90)

    with open(path, "w") as f:
        f.write("\n".join(lines))

    print("\n" + "\n".join(lines))
    logger.info(f"Summary saved to: {path}")


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print("  python evaluate/evaluate.py data/output/Plain_maskray.json data/raw/article_5.txt")
        print("  python evaluate/evaluate.py --all  (uses PAIRS mapping below)")
        sys.exit(1)

    # ── Manual mapping for --all mode ─────────────────────────
    # Add your article_title → txt file mappings here
    PAIRS = [
        ("data/output/Plain_maskray.json", "data/raw/article_5.txt"),
        # ("data/output/Article_2_title.json", "data/raw/article_2.txt"),
        # ("data/output/Article_3_title.json", "data/raw/article_3.txt"),
        # ("data/output/Article_4_title.json", "data/raw/article_4.txt"),
        # ("data/output/Article_5_title.json", "data/raw/article_1.txt"),
    ]

    if args[0] == "--all":
        all_summaries = []
        for kg_path, article_path in PAIRS:
            if not os.path.exists(kg_path):
                logger.warning(f"KG file not found: {kg_path} — skipping")
                continue
            if not os.path.exists(article_path):
                logger.warning(f"Article file not found: {article_path} — skipping")
                continue
            try:
                output = evaluate_kg(kg_path, article_path)
                if output:
                    save_results(output, output["summary"]["article_title"])
                    all_summaries.append(output["summary"])
            except Exception as e:
                logger.error(f"Failed on {kg_path}: {e}")

        if all_summaries:
            save_summary_table(all_summaries)

    else:
        # Single pair
        if len(args) < 2:
            print("Provide both kg_path and article_path")
            sys.exit(1)

        kg_path      = args[0]
        article_path = args[1]

        output = evaluate_kg(kg_path, article_path)
        if output:
            save_results(output, output["summary"]["article_title"])
            save_summary_table([output["summary"]])