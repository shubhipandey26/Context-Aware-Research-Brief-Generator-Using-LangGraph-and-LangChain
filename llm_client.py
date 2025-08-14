
import json, re
from typing import Any, Dict
from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline
from pydantic import ValidationError

# Lazy singletons
_small = None
_base = None

def get_small_llm():
    global _small
    if _small is None:
        pp = pipeline("text2text-generation", model="google/flan-t5-small")
        _small = HuggingFacePipeline(pipeline=pp)
    return _small

def get_base_llm():
    global _base
    if _base is None:
        pp = pipeline("text2text-generation", model="google/flan-t5-base")
        _base = HuggingFacePipeline(pipeline=pp)
    return _base

def t2t_invoke(llm, prompt: str, max_tokens: int = 512) -> str:
    # langchain llm.invoke expects a string; HF pipeline respects max_length via kwargs
    return llm.invoke(prompt)

def extract_json_block(text: str):
    # Find longest JSON-like block
    blocks = re.findall(r'(\{.*?\}|\[.*?\])', text, flags=re.S)
    if not blocks:
        return None
    cand = max(blocks, key=len)
    try:
        return json.loads(cand)
    except Exception:
        # small repairs
        cand2 = re.sub(r",\s*}", "}", cand)
        cand2 = re.sub(r",\s*\]", "]", cand2)
        cand2 = cand2.replace("\n", " ")
        try:
            return json.loads(cand2)
        except Exception:
            return None

def ensure_pydantic(model_cls, data: Dict[str, Any]):
    try:
        return model_cls(**data)
    except ValidationError as e:
        raise e
