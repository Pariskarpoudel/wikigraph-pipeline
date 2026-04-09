# evaluate/llm_judge.py
#
# Evaluates a KG output against its source article using LLM as judge.
# Measures QUALITY — are the extracted triples factually correct?
#
# Usage:
#   python evaluate/llm_judge.py data/output/Plain_maskray.json data/raw/article_5.txt
#   python evaluate/llm_judge.py --all
#
# Output:
#   evaluate/results/<article>_judge.json  — detailed per-triple scores
#   evaluate/results/judge_summary.txt     — summary table across all articles

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

RESULTS_DIR = "evaluate/results"
BATCH_SIZE  = 5   # small batches → fewer parse failures


# ─────────────────────────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """You are an expert knowledge graph evaluator.
You will be given a source article and a small list of knowledge graph triples extracted from it.
Evaluate each triple carefully and honestly.

For each triple output:
- "verdict": "correct" | "partial" | "incorrect"
- "score": 1.0 (correct), 0.5 (partial), 0.0 (incorrect)
- "reason": one sentence explanation

Definitions:
- correct:   fully supported by the article text
- partial:   roughly right but imprecise, missing detail, or slightly wrong
- incorrect: not supported by the article, or contradicts it

Output JSON only. No explanation outside JSON.
Output every triple in the batch — do not skip any."""


def build_judge_prompt(article_text: str, triples: List[Dict], batch_num: int, total_batches: int) -> str:
    triples_block = "\n".join(
        f'{i+1}. ({t["subject"]}, {t["relation"]}, {t["object"]})'
        for i, t in enumerate(triples)
    )

    return f"""Article text:
\"\"\"
{article_text[:6000]}
\"\"\"

Evaluate these {len(triples)} triples (batch {batch_num}/{total_batches}):
{triples_block}

Output format — one entry per triple, numbered 1 to {len(triples)}:
{{
  "1": {{"verdict": "correct", "score": 1.0, "reason": "supported by article"}},
  "2": {{"verdict": "incorrect", "score": 0.0, "reason": "not mentioned in article"}},
  ...
}}"""


# ─────────────────────────────────────────────────────────────
# Core evaluation
# ─────────────────────────────────────────────────────────────

def _parse_entry(entry: dict) -> tuple:
    """Parse a single triple result entry. Returns (verdict, score, reason)."""
    raw_score = entry.get("score", None)
    try:
        score = float(raw_score) if raw_score is not None else None
    except (TypeError, ValueError):
        score = None

    verdict = entry.get("verdict", "unscored")

    # infer verdict from score if verdict missing or unscored
    if score is not None and verdict == "unscored":
        if score >= 1.0:
            verdict = "correct"
        elif score >= 0.5:
            verdict = "partial"
        else:
            verdict = "incorrect"

    reason = entry.get("reason", "")
    return verdict, score, reason


def evaluate_kg(kg_path: str, article_path: str) -> Dict:
    """
    Evaluate a single KG JSON against its source article.
    Returns results dict with per-triple scores and summary stats.
    """
    with open(kg_path, "r", encoding="utf-8") as f:
        kg = json.load(f)

    with open(article_path, "r", encoding="utf-8") as f:
        article_text = f.read()

    article_title = kg["article_title"]
    triples       = kg["triples"]

    logger.info(f"{'='*60}")
    logger.info(f"Evaluating: '{article_title}'")
    logger.info(f"  Total triples: {len(triples)}")
    logger.info(f"{'='*60}")

    batches        = [triples[i:i+BATCH_SIZE] for i in range(0, len(triples), BATCH_SIZE)]
    total_batches  = len(batches)
    triple_results = []

    for batch_num, batch in enumerate(batches, 1):
        logger.info(f"  Judging batch {batch_num}/{total_batches} ({len(batch)} triples)...")

        user_prompt = build_judge_prompt(article_text, batch, batch_num, total_batches)

        raw = llm_call(
            system_prompt=JUDGE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=config.LLM_DEFAULT_MODEL
        )

        result = parse_llm_json(raw, expected_type="dict")

        if result is None:
            logger.warning(f"  Parse failed for batch {batch_num} — marking as unscored")
            for t in batch:
                triple_results.append({
                    "triple":  t,
                    "verdict": "unscored",
                    "score":   None,
                    "reason":  "LLM parse failed"
                })
        else:
            for i, t in enumerate(batch):
                key   = str(i + 1)
                entry = result.get(key, {})

                if not entry:
                    logger.warning(f"  Missing entry for triple {i+1} in batch {batch_num}")
                    triple_results.append({
                        "triple":  t,
                        "verdict": "unscored",
                        "score":   None,
                        "reason":  "missing from LLM output"
                    })
                    continue

                verdict, score, reason = _parse_entry(entry)
                triple_results.append({
                    "triple":  t,
                    "verdict": verdict,
                    "score":   score,
                    "reason":  reason
                })

        time.sleep(1)   # avoid rate limits

    # ── Summary stats ─────────────────────────────────────────
    scored    = [r for r in triple_results if r["score"] is not None]
    total     = len(triple_results)
    n_scored  = len(scored)

    correct   = sum(1 for r in scored if r["verdict"] == "correct")
    partial   = sum(1 for r in scored if r["verdict"] == "partial")
    incorrect = sum(1 for r in scored if r["verdict"] == "incorrect")
    unscored  = total - n_scored
    avg_score = sum(r["score"] for r in scored) / n_scored if n_scored > 0 else 0

    summary = {
        "article_title":    article_title,
        "total_triples":    total,
        "scored_triples":   n_scored,
        "correct":          correct,
        "partial":          partial,
        "incorrect":        incorrect,
        "unscored":         unscored,
        "avg_score":        round(avg_score, 3),
        "precision_approx": round(avg_score, 3),
    }

    logger.info(f"\n{'='*60}")
    logger.info(f"RESULTS: '{article_title}'")
    logger.info(f"  Total triples:  {total}")
    logger.info(f"  Scored:         {n_scored}")
    logger.info(f"  Correct:        {correct}")
    logger.info(f"  Partial:        {partial}")
    logger.info(f"  Incorrect:      {incorrect}")
    logger.info(f"  Unscored:       {unscored}")
    logger.info(f"  Avg score:      {avg_score:.3f}")
    logger.info(f"{'='*60}\n")

    # print each triple result
    for i, r in enumerate(triple_results, 1):
        t    = r["triple"]
        icon = "✅" if r["verdict"] == "correct" else "⚠️" if r["verdict"] == "partial" else "❌"
        logger.info(
            f"  {icon} {i:>3}. ({t['subject']}, {t['relation']}, {t['object']})\n"
            f"         → {r['verdict']} | {r['reason']}"
        )

    return {
        "summary":        summary,
        "triple_results": triple_results,
    }


# ─────────────────────────────────────────────────────────────
# Save results
# ─────────────────────────────────────────────────────────────

def save_results(output: Dict, article_title: str):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    filename = article_title.replace(" ", "_").replace("/", "_") + "_judge.json"
    path     = os.path.join(RESULTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to: {path}")
    return path


def save_summary_table(all_summaries: List[Dict]):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "judge_summary.txt")

    lines = []
    lines.append("=" * 85)
    lines.append("LLM JUDGE EVALUATION SUMMARY  —  QUALITY (Precision)")
    lines.append("=" * 85)
    lines.append(
        f"{'Article':<35} {'Triples':>7} {'Scored':>7} "
        f"{'Correct':>8} {'Partial':>8} {'Wrong':>7} {'Unscored':>9} {'Score':>7}"
    )
    lines.append("-" * 85)

    for s in all_summaries:
        lines.append(
            f"{s['article_title']:<35} "
            f"{s['total_triples']:>7} "
            f"{s['scored_triples']:>7} "
            f"{s['correct']:>8} "
            f"{s['partial']:>8} "
            f"{s['incorrect']:>7} "
            f"{s['unscored']:>9} "
            f"{s['avg_score']:>7.3f}"
        )

    lines.append("-" * 85)

    if all_summaries:
        avg           = sum(s["avg_score"]     for s in all_summaries) / len(all_summaries)
        total_triples = sum(s["total_triples"] for s in all_summaries)
        lines.append(
            f"{'OVERALL':<35} {total_triples:>7} {'':>7} "
            f"{'':>8} {'':>8} {'':>7} {'':>9} {avg:>7.3f}"
        )

    lines.append("=" * 85)

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
        print("  python evaluate/llm_judge.py data/output/Plain_maskray.json data/raw/article_5.txt")
        print("  python evaluate/llm_judge.py --all  (uses PAIRS mapping below)")
        sys.exit(1)

    # ── Manual mapping for --all mode ─────────────────────────
    PAIRS = [
        ("data/output/Plain_maskray.json",                           "data/raw/article_5.txt"),
        ("data/output/Gambia_women_'s_national_football_team.json",  "data/raw/article_4.txt"),
        # add more pairs as you generate more KGs
        # ("data/output/Article_title.json", "data/raw/article_N.txt"),
    ]

    if args[0] == "--all":
        all_summaries = []
        for kg_path, article_path in PAIRS:
            if not os.path.exists(kg_path):
                logger.warning(f"KG not found: {kg_path} — skipping")
                continue
            if not os.path.exists(article_path):
                logger.warning(f"Article not found: {article_path} — skipping")
                continue
            try:
                output = evaluate_kg(kg_path, article_path)
                save_results(output, output["summary"]["article_title"])
                all_summaries.append(output["summary"])
            except Exception as e:
                logger.error(f"Failed on {kg_path}: {e}")

        if all_summaries:
            save_summary_table(all_summaries)

    else:
        if len(args) < 2:
            print("Provide both kg_path and article_path")
            sys.exit(1)

        kg_path      = args[0]
        article_path = args[1]

        output = evaluate_kg(kg_path, article_path)
        save_results(output, output["summary"]["article_title"])
        save_summary_table([output["summary"]])