# utils/llm.py
import os
import time
import logging
from dotenv import load_dotenv
from groq import Groq
import config

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
logger  = logging.getLogger(__name__)


def llm_call(
    system_prompt: str,
    user_prompt: str,
    model: str = None,
) -> str:
    """
    Single LLM call. Retries up to 3 times on failure.

    model: defaults to config.LLM_DEFAULT_MODEL
    """
    selected_model = model or config.LLM_DEFAULT_MODEL

    for attempt in range(config.LLM_MAX_RETRIES):
        try:
            response = _client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.LLM_TEMPERATURE
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.warning(
                f"LLM call failed (attempt {attempt + 1}/{config.LLM_MAX_RETRIES}): {e}"
            )
            if attempt < config.LLM_MAX_RETRIES - 1:
                time.sleep(config.LLM_RETRY_DELAY_SECONDS)
            else:
                raise




















# import os
# import time
# import logging
# from dotenv import load_dotenv
# from google import genai
# from google.genai import types

# load_dotenv()
# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# logger = logging.getLogger(__name__)


# def llm_call(
#     system_prompt: str,
#     user_prompt: str,
#     model: str = "gemini-2.5-flash-lite",
#     response_schema: dict = None
# ) -> str:
#     """
#     Single LLM call. Retries up to 3 times on failure.

#     model: "gemini-2.5-flash-lite"  → default, high volume steps (2, 3, 5, 7)
#            "gemini-2.5-flash"  → reasoning-heavy steps (4, 6)
#     """
#     config = types.GenerateContentConfig(
#         system_instruction=system_prompt,
#         temperature=0.0,
#         response_mime_type="application/json",
#         response_schema=response_schema if response_schema else None
#     )

#     for attempt in range(3):
#         try:
#             response = client.models.generate_content(
#                 model=model,
#                 contents=user_prompt,
#                 config=config
#             )
#             return response.text

#         except Exception as e:
#             logger.warning(f"LLM call failed (attempt {attempt+1}/3): {e}")
#             if attempt < 2:
#                 time.sleep(5)
#             else:
#                 raise
