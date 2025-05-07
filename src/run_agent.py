# # src/run_agent.py

# from src.agents import agent

# def main():
#     print("🎯 Business Insights Generator (agentic mode)\n")
#     query = input("Enter your business-insight query: ").strip()

#     # ✅ Use "input" as key instead of "query"
#     result = agent.invoke({"input": query})

#     print("\n=== Agent Response ===")
#     print(result)

# if __name__ == "__main__":
#     main()

# src/run_agent.py

# import os, json, datetime
# from src.agents import agent, index, documents, embedder
# from src import analysis, insights_other, file_processor
# import pandas as pd
# from prophet import Prophet
# import matplotlib.pyplot as plt

# # load your config (paths, etc)
# from src.llm import load_config
# cfg = load_config("config/config.json")

# def main():
#     query = input("Enter your business-insight query: ").strip()
#     # 1) Run the agent *only* to fetch the refined docs list
#     result = agent.invoke({"input": query})
#     print("\n=== Agent raw output ===")
#     print(result)

#     # 2) Now get the actual docs back via the same call you exposed:
#     docs = analysis.retrieve_relevant_docs(query, index, documents, embedder, top_k=5)
#     # split into timeseries vs text
#     ts_docs = [d for d in docs if d["type"]=="timeseries" and len(d["series"])>=2]
#     text_docs = [d for d in docs if d["type"]=="text"]

#     # 3) If we have a timeseries, plot & forecast
#     if ts_docs:
#         best = ts_docs[0]
#         graph_path = _forecast_and_plot = analysis.plot_trend_and_save  # or call your helper
#         # you can either call your helper directly:
#         fps = f"{best['category']}_trend.png"
#         graph_file = os.path.join(cfg["graphs_folder"], fps)
#         analysis.plot_trend_and_save(best["series"], best["category"], graph_file)
#         print("Graph saved:", graph_file)

#     # 4) Always produce an insights .txt by concatenating time-series summary + text
#     #    (this mirrors your earlier "else" branch)
#     combined_text = ""
#     for td in text_docs:
#         path = os.path.join(cfg["other_text_folder"], td["file"])
#         snippet = open(path, encoding="utf-8").read()
#         combined_text += f"\n--- {td['file']} ---\n{snippet}\n"

#     # if we did a timeseries, prepend the summary+forecast lines:
#     if ts_docs:
#         import pandas as pd
#         df = pd.DataFrame(best["series"])
#         df["Date"] = pd.to_datetime(df["Date"])
#         df = df.sort_values("Date")
#         summary = (
#             f"Category '{best['category']}', last observed: {df['value'].iat[-1]} on {df['Date'].iat[-1].date()}\n"
#             "Forecast:\n"
#             + "\n".join(
#                 f"{row['ds'].date()}: {row['yhat']:.2f}"
#                 for _, row in Prophet().fit(
#                     df.rename(columns={"Date":"ds","value":"y"})).make_future_dataframe(
#                     periods=14, freq="M"
#                 ).pipe(lambda fut: Prophet().fit(
#                     df.rename(columns={"Date":"ds","value":"y"})).predict(fut)
#                 )[lambda fc: fc.ds > df["Date"].max()]
#                 .iterrows()
#             )
#             + "\n\n"
#         )
#     else:
#         summary = ""

#     insight = insights_other.generate_other_insights(query, {"_ts_summary": summary, **{td['file']: open(os.path.join(cfg["other_text_folder"],td['file']),encoding="utf-8").read() for td in text_docs}}, lambda s,u: agent.invoke({"input":u}))
#     # save to file
#     ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#     out = os.path.join(cfg["insights_folder"], f"insights_{ts}.txt")
#     with open(out, "w", encoding="utf-8") as f:
#         f.write("User Query:\n" + query + "\n\n")
#         f.write("Sources:\n" + "\n".join(
#             (f"{d['file']}/{d.get('sheet','')}" for d in docs)
#         ) + "\n\n")
#         f.write("Insights:\n" + insight)
#     print("Insights saved:", out)

# if __name__=="__main__":
#     main()



# # running agent src/run_agent.py
# from src.agents import agent

# def main():
#     query = input("Enter your business‐insight query: ").strip()
#     # force the agent to call our pipeline tool
#     prompt = f"Action: Run_Full_Pipeline\nAction Input: \"{query}\""
#     result = agent.invoke({"input": prompt})
#     print(result)

# if __name__ == "__main__":
#     main()



# src/run_agent.py

# src/run_agent.py

import sys
from src.agents import pipeline_agent
from src.main import process_query

def main():
    mode = "normal"
    if len(sys.argv) > 1 and sys.argv[1] == "agent":
        mode = "agent"
    query = input("Enter your business-insight query: ").strip()
    if mode == "agent":
        result = pipeline_agent.invoke({"input": query})
        print("\n=== Agent Response ===")
        print(result)
    else:
        observed, forecast, insights = process_query(query)
        print("\n=== Normal Mode Output ===")
        print("Observed:", observed)
        print("Forecast:", forecast)
        print("Insights:", insights)

if __name__ == "__main__":
    main()


