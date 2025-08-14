
import uuid, time, json
from datetime import datetime
from typing import List, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

# Change relative imports to absolute imports
from app.schemas import ResearchStep, ResearchPlan, SourceSummary, FinalBrief
from app.persistence import UserHistoryStore
from app.llm_client import get_small_llm, get_base_llm, t2t_invoke, extract_json_block
from app.tools import web_search, fetch_page_text
from app.utils import checkpoint_state, retry_call

# ---- Typed state ----
class State(TypedDict, total=False):
    run_id: str
    topic: str
    depth: int
    follow_up: bool
    user_id: str
    start_ts: float

    history_summary: str
    planning_steps: List[dict]
    search_results: List[dict]
    fetched_pages: List[dict]
    source_summaries: List[dict]
    final_brief: dict

store = UserHistoryStore()

# ---- Nodes ----
def node_context_summary(state: State):
    if not state.get("follow_up"):
        return {"history_summary": ""}
    prev = store.get_user_history(state["user_id"])
    if not prev:
        return {"history_summary": ""}

    small = get_small_llm()
    prompt = (
        "Summarize prior briefs into 4-6 bullet points of persistent context."
        "Return plain text bullets."
        f"{json.dumps(prev)[:3500]}"
    )
    out = t2t_invoke(small, prompt)
    checkpoint_state(state["run_id"], "context_summary", {"summary": out})
    return {"history_summary": out}

def node_planning(state: State):
    small = get_small_llm()
    prompt = (
        "You are a research planner. Given TOPIC, optional HISTORY, and DEPTH, "
        "produce ONLY a JSON object with key 'steps' as an array of objects with keys: "
        "step_id, description, rationale, estimated_time_minutes."
        "Keep step_id like 's1','s2'."
        f"TOPIC: {state['topic']}"
        "HISTORY:{state.get('history_summary','')}"
        "DEPTH:{state['depth']}"
        "JSON:"
    )
    raw = t2t_invoke(small, prompt)
    data = extract_json_block(raw) or {}
    steps = data.get("steps", [])
    if not isinstance(steps, list) or not steps:
        steps = [{"step_id":"s1","description":"Initial scoping","rationale":"","estimated_time_minutes":5}]
    validated = []
    for i, s in enumerate(steps):
        s = dict(s)
        s.setdefault("step_id", f"s{i+1}")
        s.setdefault("description", "TBD")
        s.setdefault("rationale", "")
        s.setdefault("estimated_time_minutes", 5)
        try:
            validated.append(ResearchStep(**s).model_dump())
        except Exception:
            validated.append(ResearchStep(step_id=f"s{i+1}", description="TBD", estimated_time_minutes=5).model_dump())
    checkpoint_state(state["run_id"], "planning", {"steps": validated})
    return {"planning_steps": validated}

def node_search(state: State):
    k = max(3, min(12, state.get("depth",1) * 4))
    hits = web_search(state["topic"], k=k)
    for i, h in enumerate(hits):
        h["id"] = f"src-{i+1}"
    checkpoint_state(state["run_id"], "search", {"hits": hits})
    return {"search_results": hits}

def node_fetch(state: State):
    fetched = []
    for h in state.get("search_results", []):
        url = h.get("url") or ""
        if not url:
            continue
        text = fetch_page_text(url)
        fetched.append({"id": h["id"], "url": url, "title": h.get("title",""), "text": text})
    checkpoint_state(state["run_id"], "fetch", {"count": len(fetched)})
    return {"fetched_pages": fetched}

def node_per_source(state: State):
    small = get_small_llm()
    out = []
    limit = max(3, min(12, state.get("depth",1) * 4))
    for fp in state.get("fetched_pages", [])[:limit]:
        prompt = (
            "Summarize the source as JSON with keys: "
            "source_id, title, url, summary, key_findings (array), published_date (string or null), confidence_score (0..1 or null). "
            "Return ONLY JSON."
            f"TITLE: {fp.get('title','')}"
            "URL: {fp.get('url')}"
            "TEXT:{fp.get('text','')[:4500]}"
        )
        def do():
            raw = t2t_invoke(small, prompt)
            data = extract_json_block(raw) or {}
            if not data:
                data = {
                    "source_id": fp["id"], "title": fp.get("title","Untitled"),
                    "url": fp.get("url"), "summary": raw[:800], "key_findings":[]
                }
            try:
                rec = SourceSummary(**data).model_dump()
                # Ensure URL is a string for serialization later
                if rec.get("url"):
                    rec["url"] = str(rec["url"])
            except Exception:
                rec = SourceSummary(
                    source_id=fp["id"], title=fp.get("title","Untitled")[:300],
                    url=fp.get("url"), summary=(data.get("summary") or "Summary unavailable")[:1200],
                    key_findings=(data.get("key_findings") or [])[:10]
                ).model_dump()
                # Ensure URL is a string for serialization later
                if rec.get("url"):
                    rec["url"] = str(rec["url"])
            return rec
        rec = retry_call(do, retries=2)
        out.append(rec)
        checkpoint_state(state["run_id"], f"per_source_{fp['id']}", rec)
    return {"source_summaries": out}

def node_synthesis(state: State):
    base = get_base_llm()
    start = time.time()
    # Convert HttpUrl objects in source_summaries to strings before dumping
    source_summaries_for_dump = []
    for summary in state.get('source_summaries', []):
        summary_copy = summary.copy()
        if summary_copy.get('url'):
            summary_copy['url'] = str(summary_copy['url'])
        source_summaries_for_dump.append(summary_copy)

    prompt = (
        "Create a FinalBrief as JSON with keys: "
        "brief_id (uuid), topic, generated_at (ISO8601), depth (int), user_id, summary (<=250 words), "
        "planning_steps (array of ResearchStep), source_summaries (array of SourceSummary), "
        "synthesized_insights (array of short bullets), references (array of URLs), provenance (object), "
        "token_usage (object), latency_ms (int). "
        "Return ONLY JSON."
        f"Topic:{state['topic']}"
        "Depth:{state['depth']}"
        "User:{state['user_id']}"
        f"Planning:{json.dumps(state.get('planning_steps',[]))}"
        f"Sources:{json.dumps(source_summaries_for_dump)}" # Use the converted list
    )
    def do():
        raw = t2t_invoke(base, prompt)
        data = extract_json_block(raw)
        if not data:
            data = {
                "brief_id": str(uuid.uuid4()),
                "topic": state["topic"],
                "generated_at": datetime.utcnow().isoformat(),
                "depth": state["depth"],
                "user_id": state["user_id"],
                "summary": raw[:1200],
                "planning_steps": state.get("planning_steps", []),
                "source_summaries": state.get("source_summaries", []),
                "synthesized_insights": [],
                "references": [str(s.get("url")) for s in state.get("source_summaries",[]) if s.get("url")][:15], # Convert HttpUrl to string
                "provenance": {},
                "token_usage": {},
                "latency_ms": int((time.time()-start)*1000)
            }
        fb = FinalBrief(**data).model_dump()
        return fb
    fb = retry_call(do, retries=2)
    checkpoint_state(state["run_id"], "synthesis", fb)
    return {"final_brief": fb}

def node_post_process(state: State):
    final = state.get("final_brief", {})
    # Dedupe references and convert to strings
    seen, refs = set(), []
    for u in final.get("references", []):
        url_str = str(u) if u else "" # Convert HttpUrl to string
        if url_str and url_str not in seen:
            seen.add(url_str); refs.append(url_str)
    final["references"] = refs[:20]
    if state.get("start_ts"):
        final["latency_ms"] = int((time.time() - state["start_ts"]) * 1000)
    final = FinalBrief(**final).model_dump()
    # persist history
    store.append_brief(state["user_id"], final)
    checkpoint_state(state["run_id"], "post_process", {"saved": True, "refs": len(refs)})
    return {"final_brief": final}

# ---- Build graph ----
def build_graph():
    g = StateGraph(State)
    g.add_node("context_summary", node_context_summary)
    g.add_node("planning", node_planning)
    g.add_node("search", node_search)
    g.add_node("fetch", node_fetch)
    g.add_node("per_source", node_per_source)
    g.add_node("synthesis", node_synthesis)
    g.add_node("post_process", node_post_process)

    g.add_edge(START, "context_summary")
    g.add_edge("context_summary", "planning")
    g.add_edge("planning", "search")
    g.add_edge("search", "fetch")
    g.add_edge("fetch", "per_source")
    g.add_edge("synthesis", "post_process")
    g.add_edge("post_process", END)
    return g.compile()

def build_and_run(topic: str, depth: int, user_id: str, follow_up: bool=False, run_id: Optional[str]=None):
    run_id = run_id or str(uuid.uuid4())
    chain = build_graph()
    init = {
        "run_id": run_id,
        "topic": topic,
        "depth": int(depth),
        "follow_up": bool(follow_up),
        "user_id": user_id,
        "start_ts": time.time()
    }
    res = chain.invoke(init)
    return res.get("final_brief")
