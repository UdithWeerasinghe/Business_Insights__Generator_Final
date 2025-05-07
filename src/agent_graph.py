import os
import pandas as pd
from prophet import Prophet
from langgraph.graph import StateGraph, END
from src import analysis, insights_other
from src.llm import load_config
from langchain_ollama.llms import OllamaLLM
from typing import TypedDict, List, Dict, Any

# --- Setup (reuse your config and index logic) ---
cfg = load_config("config/config.json")
index, documents, embedder = analysis.build_unified_index(cfg["output_folder"], cfg["other_text_folder"])

# Configure the LLM with essential parameters only
llm_client = OllamaLLM(
    model=cfg["model_name"],
    temperature=0.7,
    num_ctx=4096
)

# --- Node 1: Search ---
def search_node(state):
    query = state["query"]
    # If the query is short or just a brand, ask the LLM to expand it
    if len(query.split()) < 3:
        clarification_prompt = (
            f"The user asked: '{query}'. "
            "If this is a brand name or ambiguous, expand it to a full product query (e.g., 'sales of the beverage <brand>' or 'sales of <brand> across all categories'). "
            "Otherwise, return the query as is."
        )
        try:
            expanded_query = llm_client.invoke(clarification_prompt)
            if expanded_query and isinstance(expanded_query, str):
                query = expanded_query.strip()
        except Exception:
            pass  # fallback to original query if LLM fails

    # Now use the expanded query for vector retrieval
    docs = analysis.retrieve_relevant_docs(query, index, documents, embedder, top_k=5)
    ts_docs = [d for d in docs if d["type"] == "timeseries" and len(d["series"]) >= 2]
    best_ts = ts_docs[0] if ts_docs else None
    text_docs = {d["file"]: d["text"] for d in docs if d["type"] == "text"}
    return {**state, "best_ts": best_ts, "text_docs": text_docs}

# --- Node 2: Forecast ---
def forecast_node(state):
    best_ts = state.get("best_ts")
    if not best_ts:
        return {**state, "observed": {"x": [], "y": []}, "forecast": {"x": [], "y": []}, "forecast_df": None}
    df = pd.DataFrame(best_ts["series"])
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").rename(columns={"Date": "ds", "value": "y"})
    m = Prophet().fit(df)
    fut = m.make_future_dataframe(periods=14, freq="M")
    fc = m.predict(fut)
    fc_filt = fc[fc.ds > df.ds.max()]
    observed = {"x": df["ds"].dt.strftime("%Y-%m-%d").tolist(), "y": df["y"].tolist()}
    forecast = {"x": fc_filt["ds"].dt.strftime("%Y-%m-%d").tolist(), "y": fc_filt["yhat"].tolist()}
    return {**state, "observed": observed, "forecast": forecast, "forecast_df": fc_filt, "timeseries_df": df, "category": best_ts["category"]}

# --- Node 3: Insights ---
def insights_node(state):
    query = state["query"]
    text_docs = state.get("text_docs", {})
    forecast_df = state.get("forecast_df")
    timeseries_df = state.get("timeseries_df")
    category = state.get("category")
    insights = insights_other.generate_other_insights(
        user_query=query,
        texts=text_docs,
        generate_response_fn=llm_client,
        timeseries_df=timeseries_df,
        forecast_df=forecast_df,
        category=category
    )
    return {**state, "insights": insights}

# --- Build the LangGraph pipeline ---
class AgentState(TypedDict, total=False):
    query: str
    best_ts: Any
    text_docs: Dict[str, str]
    observed: Dict[str, List]
    forecast: Dict[str, List]
    forecast_df: Any
    timeseries_df: Any
    category: str
    insights: str

graph = StateGraph(AgentState)
graph.add_node("search_data", search_node)
graph.add_node("generate_forecast", forecast_node)
graph.add_node("generate_insights", insights_node)
graph.add_edge("search_data", "generate_forecast")
graph.add_edge("generate_forecast", "generate_insights")
graph.add_edge("generate_insights", END)
graph.set_entry_point("search_data")
pipeline = graph.compile()

# --- Helper for Flask or CLI ---
def run_agentic_pipeline(query):
    state = {"query": query}
    result = pipeline.invoke(state)
    # Return the same structure as your normal mode
    return {
        "observed": result.get("observed", {"x": [], "y": []}),
        "forecast": result.get("forecast", {"x": [], "y": []}),
        "insights": result.get("insights", "")
    }
