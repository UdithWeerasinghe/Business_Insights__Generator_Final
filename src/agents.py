# src/agents.py

# import os, json
# from langchain_ollama.llms import OllamaLLM        # ← changed import
# from langchain.agents import initialize_agent, Tool, AgentType
# from src import etl, analysis, file_processor, insights_other
# from src.llm import load_config                      # ← load_config now lives in llm.py

# from langchain.prompts import PromptTemplate
# from langchain.agents import AgentExecutor
# from langchain.agents.mrkl.prompt import FORMAT_INSTRUCTIONS


# cfg = load_config("config/config.json")

# # # (1) Run ETL once at import time
# # etl.run_etl_pipeline(
# #     cfg["input_folder"],
# #     cfg["intermediate_folder"],
# #     cfg["output_folder"],
# # )

# # (2) Build unified index (Excel JSON + other_text)
# index, documents, embedder = analysis.build_unified_index(
#     cfg["output_folder"],
#     cfg["other_text_folder"]
# )

# # (3) Instantiate OllamaLLM
# llm_client = OllamaLLM(model=cfg["model_name"])

# def _forecast_and_plot(best_doc):
#     import pandas as pd
#     import matplotlib.pyplot as plt
#     from prophet import Prophet

#     df = pd.DataFrame(best_doc["series"])
#     df["Date"] = pd.to_datetime(df["Date"])
#     df = df.sort_values("Date").rename(columns={"Date": "ds", "value": "y"})

#     m = Prophet().fit(df)
#     fut = m.make_future_dataframe(periods=14, freq="M")
#     fc = m.predict(fut)
#     fc_filt = fc[fc.ds > df.ds.max()]

#     plt.figure(figsize=(10,6))
#     plt.plot(df.ds, df.y, label="Observed", linewidth=2)
#     plt.plot(fc_filt.ds, fc_filt.yhat, "--", label="Forecast", linewidth=2)
#     plt.legend()
#     out = os.path.join(cfg["graphs_folder"], f"{best_doc['category']}_trend.png")
#     plt.savefig(out)
#     plt.close()
#     return out

# # (4) Define our tools (no ETL tool here—ETL already ran)
# tools = [
#     Tool(
#     name="Search_Relevance",
#     func=lambda query: analysis.retrieve_relevant_docs(query, index, documents, embedder, top_k=5),
#     description=(
#         "Given a user query, return a LIST of the top-k matching document dicts. "
#         "Each dict has keys: type, category (or file), series (if timeseries), file, sheet, text (if text)."
#     ),
# ),

#     Tool(
#     name="Forecast_Visualize",
#     func=_forecast_and_plot,   # <-- it WILL receive the Python dict you returned above
#     description="Given a timeseries doc dict, plot & forecast and return the saved graph path."
# ),

#     Tool(
#         name="Generate_Insights",
#         func=lambda inputs: insights_other.generate_other_insights(
#             inputs["query"], inputs["texts"], llm_client
#         ),
#         description="Given extracted text docs and a query, generate actionable textual insights."
#     ),
# ]




# template = """
# You are a Business Insights Agent.  Use the available tools to fetch data,
# run forecasts, and generate written recommendations.

# When you have enough to _answer_ the user, stop calling tools and emit:

#   Answer: <your final write‐up here>

# Always follow this format strictly:

#   Thought: <your reasoning>
#   Action: <tool name>
#   Action Input: <what you pass to the tool>
#   Observation: <tool output>
#   ... repeat Thought/Action/Observation as needed ...
#   Answer: <final answer>

# Begin!  The user question is:
# {input}
# {format_instructions}
# """
# prompt = PromptTemplate(
#     template=template,
#     input_variables=["input"],
#     partial_variables={"format_instructions": FORMAT_INSTRUCTIONS},
# )


# # (5) Build the agent
# agent = initialize_agent(
#     tools,
#     llm_client,
#     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#     verbose=True,
#     max_iterations=6,            # allow up to 6 thought-action loops
#     max_execution_time=300,      # or give it 5 minutes total
#     early_stopping_method="generate",
#     handle_parsing_errors=True, 
# )


# # now build a zero‐shot agent with our very explicit prompt
# # agent = AgentExecutor.from_agent_and_tools(
# #     llm=llm_client,
# #     tools=tools,
# #     prompt=prompt,
# #     verbose=True,
# #     handle_parsing_errors=True,
# #     max_iterations=6,
# #     max_execution_time=300,
# #     early_stopping_method="generate",
# #     agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
# # )



# src/agents.py lastagent

# import os, json
# from langchain_ollama.llms import OllamaLLM
# from langchain.agents import initialize_agent, Tool, AgentType
# from src import etl, analysis, file_processor, insights_other
# from src.llm import load_config

# # 1) Load config
# cfg = load_config("config/config.json")

# # 2) Helper to forecast & plot a timeseries doc
# def _forecast_and_plot(best_doc):
#     import pandas as pd
#     import matplotlib.pyplot as plt
#     from prophet import Prophet

#     df = pd.DataFrame(best_doc["series"])
#     df["Date"] = pd.to_datetime(df["Date"])
#     df = df.sort_values("Date").rename(columns={"Date": "ds", "value": "y"})

#     m = Prophet().fit(df)
#     fut = m.make_future_dataframe(periods=14, freq="M")
#     fc = m.predict(fut)
#     fc_filt = fc[fc.ds > df.ds.max()]

#     plt.figure(figsize=(10,6))
#     plt.plot(df.ds, df.y, label="Observed", linewidth=2)
#     plt.plot(fc_filt.ds, fc_filt.yhat, "--", label="Forecast", linewidth=2)
#     plt.legend()
#     out = os.path.join(cfg["graphs_folder"], f"{best_doc['category']}_trend.png")
#     plt.savefig(out)
#     plt.close()
#     return out

# # 3) Build unified FAISS index (Excel JSON + extracted text)
# index, documents, embedder = analysis.build_unified_index(
#     cfg["output_folder"],
#     cfg["other_text_folder"]
# )

# # 4) Instantiate Ollama LLM
# # llm_client = OllamaLLM(model=cfg["model_name"])

# llm_client = OllamaLLM(
#     model=cfg["model_name"],
#     temperature=0.7,
#     max_tokens=1000,
# )


# # 5) Orchestration: search → (optional) forecast+plot → text insights → save both
# def full_pipeline(query: str) -> str:
#     # a) retrieve top-5 docs
#     docs = analysis.retrieve_relevant_docs(query, index, documents, embedder, top_k=5)

#     # b) forecast+plot if at least one valid series
#     ts_docs = [d for d in docs if d["type"] == "timeseries" and len(d["series"]) >= 2]
#     graph_path = None
#     if ts_docs:
#         graph_path = _forecast_and_plot(ts_docs[0])

#     # c) gather all text docs into a dict
#     other_texts = {}
#     for d in docs:
#         if d["type"] == "text":
#             fn = d["file"]
#             try:
#                 txt = open(os.path.join(cfg["other_text_folder"], fn), "r", encoding="utf-8").read()
#                 other_texts[fn] = txt
#             except FileNotFoundError:
#                 pass

#     # d) run the text-only insights generator
#     insights = insights_other.generate_other_insights(query, other_texts, llm_client)

#     # e) save to a timestamped file
#     from datetime import datetime
#     ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
#     out_dir = cfg["insights_folder"] if graph_path else cfg["other_results_folder"]
    
#     out_file = os.path.join(out_dir, f"insights_{ts_str}.txt")
#     with open(out_file, "w", encoding="utf-8") as f:
#         if graph_path:
#             f.write(f"Graph: {graph_path}\n\n")
#         f.write(f"Query: {query}\n\n")
#         f.write(insights)

#     return (
#         f"✅ Done.\n"
#         f"Graph saved to: {graph_path or 'N/A'}\n"
#         f"Insights saved to: {out_file}"
#     )

# # 6) Define our tools (no ETL, since it's already been run once offline)
# tools = [
#     Tool(
#         name="Search_Relevance",
#         func=lambda query: "\n".join(
#             f"- {d['type']} "{d.get('category', d['file'])}" from {d.get('file','?')}/{d.get('sheet','')}"
#             for d in analysis.retrieve_relevant_docs(query, index, documents, embedder, top_k=5)
#         ),
#         description=(
#             "Given a user query, return a bulleted list of matching documents "
#             "(time-series categories or text files) and their source filenames."
#         )
#     ),
#     Tool(
#         name="Forecast_Visualize",
#         func=lambda best: _forecast_and_plot(best),
#         description="Given a timeseries document dict, produce & save a forecast plot and return its filepath."
#     ),
#     Tool(
#         name="Generate_Insights",
#         func=lambda inputs: insights_other.generate_other_insights(
#             inputs["query"], inputs["texts"], llm_client
#         ),
#         description="Given extracted text files and a query, generate actionable business insights."
#     ),
#     Tool(
#         name="Run_Full_Pipeline",
#         func=lambda q: full_pipeline(q),
#         description=(
#             "Run the entire BI pipeline on a single query: search, forecast+plot (if any), "
#             "and insights generation over all file types."
#         )
#     ),
# ]

# # 7) Build the agent
# agent = initialize_agent(
#     tools,
#     llm_client,
#     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#     verbose=True,
#     max_iterations=6,
#     max_execution_time=300,
#     early_stopping_method="generate",
#     handle_parsing_errors=True,
# )


# src/agents.py
import os, datetime
from langchain_ollama.llms import OllamaLLM
from langchain.agents import initialize_agent, Tool, AgentType

from src import etl, analysis, file_processor, insights_other
from src.llm import load_config

# ─── 1) Load config ────────────────────────────────────────────────────────
cfg = load_config("config/config.json")

# ─── 2) Pre-extract other‐type files ONCE ───────────────────────────────────
os.makedirs(cfg["other_text_folder"], exist_ok=True)
for fname in os.listdir(cfg["input_other_folder"]):
    path = os.path.join(cfg["input_other_folder"], fname)
    txt = file_processor.extract_text_from_file(path)
    if txt:
        out_txt = os.path.splitext(fname)[0] + ".txt"
        with open(os.path.join(cfg["other_text_folder"], out_txt), "w", encoding="utf-8") as f:
            f.write(txt)

# ─── 3) Build unified FAISS index ─────────────────────────────────────────
index, documents, embedder = analysis.build_unified_index(
    cfg["output_folder"],
    cfg["other_text_folder"]
)

# ─── 4) Instatiate OllamaLLM ───────────────────────────────────────────────
llm_client = OllamaLLM(model=cfg["model_name"])

def search_agent(query):
    # Returns top relevant docs
    return analysis.retrieve_relevant_docs(query, index, documents, embedder, top_k=5)

def forecast_agent(timeseries_doc):
    # Receives a timeseries doc, returns forecast data (and optionally a plot path)
    import pandas as pd
    from prophet import Prophet
    df = pd.DataFrame(timeseries_doc["series"])
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").rename(columns={"Date": "ds", "value": "y"})
    m = Prophet().fit(df)
    fut = m.make_future_dataframe(periods=14, freq="M")
    fc = m.predict(fut)
    fc_filt = fc[fc.ds > df.ds.max()]
    # Optionally save plot here
    return fc_filt[["ds", "yhat"]].to_dict(orient="records")

def insights_agent(query, texts, forecast_df=None, category=None):
    # Generates insights using LLM
    return insights_other.generate_other_insights(
        user_query=query,
        texts=texts,
        generate_response_fn=llm_client,
        forecast_df=forecast_df,
        category=category
    )

# Define tools for LangChain agent
tools = [
    Tool(
        name="SearchAgent",
        func=search_agent,
        description="Search for relevant documents given a user query."
    ),
    Tool(
        name="ForecastAgent",
        func=forecast_agent,
        description="Given a timeseries document, forecast future values."
    ),
    Tool(
        name="InsightsAgent",
        func=lambda inputs: insights_agent(inputs["query"], inputs["texts"], inputs.get("forecast_df"), inputs.get("category")),
        description="Generate business insights from text and forecast data."
    ),
]

# Optionally, you can define a pipeline agent that orchestrates the above
pipeline_agent = initialize_agent(
    tools,
    llm_client,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=6,
    early_stopping_method="generate",
    handle_parsing_errors=True,
)
