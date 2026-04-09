# pipeline/extractor.py
import asyncio
import logging
from typing import List, Dict
import config
from utils.llm import llm_call, llm_call_async
from utils.parser import parse_llm_json
from prompts.oie import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)

def _validate_triples(data: list) -> List[Dict]:
    valid = []
    for item in data:
        if (
            isinstance(item, dict)
            and all(k in item for k in ["subject", "relation", "object"])
            and all(isinstance(item[k], str) and item[k].strip() for k in ["subject", "relation", "object"])
        ):
            valid.append({
                "subject":  item["subject"].strip(),
                "relation": item["relation"].strip(),
                "object":   item["object"].strip(),
            })
    return valid

async def _extract_chunk_async(chunk: Dict) -> List[Dict]:
    user_prompt = build_user_prompt(
        article_title=chunk["article_title"],
        section_heading=chunk["section_path"],
        chunk_text=chunk["chunk_text"]
    )
    raw = await llm_call_async(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=config.EXTRACTOR_MODEL,
    )
    data = parse_llm_json(raw, expected_type="list")
    if data is None:
        logger.warning(f"Chunk {chunk['chunk_index']} — parse failed, returning []")
        return []
    triples = _validate_triples(data)
    logger.info(f"Chunk {chunk['chunk_index']} ({chunk['section_path']}) → {len(triples)} triples")
    return triples

async def extract_all_triples_async(chunks: List[Dict]) -> List[Dict]:
    """All chunks of one article extracted in parallel."""
    results = await asyncio.gather(*[
        _extract_chunk_async(chunk) for chunk in chunks
    ])
    all_triples = [triple for chunk_triples in results for triple in chunk_triples]
    logger.info(f"Total triples extracted: {len(all_triples)}")
    return all_triples

def extract_all_triples(chunks: List[Dict]) -> List[Dict]:
    """Sync wrapper — keeps rest of pipeline unchanged."""
    return asyncio.run(extract_all_triples_async(chunks))


# # pipeline/extractor.py
# import logging
# from typing import List, Dict
# import config
# from utils.llm import llm_call
# from utils.parser import parse_llm_json
# from prompts.oie import SYSTEM_PROMPT, build_user_prompt

# logger = logging.getLogger(__name__)


# def _validate_triples(data: list) -> List[Dict]:
#     """Keep only valid triples — all three keys present and non-empty."""
#     valid = []
#     for item in data:
#         if (
#             isinstance(item, dict)
#             and all(k in item for k in ["subject", "relation", "object"])
#             and all(isinstance(item[k], str) and item[k].strip() for k in ["subject", "relation", "object"])
#         ):
#             valid.append({
#                 "subject":  item["subject"].strip(),
#                 "relation": item["relation"].strip(),
#                 "object":   item["object"].strip(),
#             })
#     return valid


# def extract_triples_from_chunk(chunk: Dict) -> List[Dict]:
#     """
#     Extract triples from a single chunk.
#     Returns list of validated triple dicts.
#     """
#     user_prompt = build_user_prompt(
#         article_title=chunk["article_title"],
#         section_heading=chunk["section_path"],
#         chunk_text=chunk["chunk_text"]
#     )

#     raw = llm_call(
#         system_prompt=SYSTEM_PROMPT,
#         user_prompt=user_prompt,
#         model=config.EXTRACTOR_MODEL,
#     )

#     data = parse_llm_json(raw, expected_type="list")

#     if data is None:
#         logger.warning(f"Chunk {chunk['chunk_index']} — parse failed, returning []")
#         return []

#     triples = _validate_triples(data)
#     logger.info(f"Chunk {chunk['chunk_index']} ({chunk['section_path']}) → {len(triples)} triples")
#     return triples


# def extract_all_triples(chunks: List[Dict]) -> List[Dict]:
#     """
#     Run triple extraction over all chunks.
#     Returns merged flat list of all triples.
#     """
#     all_triples = []

#     for chunk in chunks:
#         triples = extract_triples_from_chunk(chunk)
#         all_triples.extend(triples)

#     logger.info(f"Total triples extracted: {len(all_triples)}")
#     return all_triples