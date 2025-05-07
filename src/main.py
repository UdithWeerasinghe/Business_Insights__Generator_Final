import os, datetime
import pandas as pd
from prophet import Prophet
import matplotlib
matplotlib.use('Agg')

from src import analysis, llm

def process_query(query: str):
    # --- Folders ---
    json_root    = "data/json_input"
    graphs_folder = "data/graphs"
    insights_folder = "data/insights"
    os.makedirs(graphs_folder, exist_ok=True)
    os.makedirs(insights_folder, exist_ok=True)

    # --- LLM setup ---
    config = llm.load_config("config/config.json")
    _, _, _ = llm.authenticate_and_load_model(config)
    gen = lambda sys, usr: llm.generate_response(sys, usr)

    # --- 1) Build product index from all JSONs ---
    index, docs, embedder = analysis.build_product_index(json_root)

    # --- 3) Find best matching product ---
    sys_p = "You are a product-search assistant."
    refined = gen(sys_p, query)
    best = analysis.search_vector_store(refined, index, docs, embedder, top_k=1)[0]
    product = best["product"]

    # --- 4) Extract its time series from all JSONs ---
    series = analysis.extract_product_timeseries(json_root, product)

    # --- 5) Plot & forecast if we have ≥2 points ---
    if len(series) >= 2:
        import matplotlib.pyplot as plt
        df = pd.DataFrame(series).rename(columns={"Date":"ds","value":"y"})
        model = Prophet().fit(df)
        future = model.make_future_dataframe(periods=14, freq='M')
        fc = model.predict(future)
        fc = fc[fc.ds > df.ds.max()]
        fc["yhat"] = fc["yhat"].clip(lower=0.0)

        # Prepare data for frontend
        observed = {
            "x": df["ds"].dt.strftime("%Y-%m-%d").tolist(),
            "y": df["y"].tolist()
        }
        forecast = {
            "x": fc["ds"].dt.strftime("%Y-%m-%d").tolist(),
            "y": fc["yhat"].tolist()
        }

        insights = analysis.generate_insights_from_predictions(
            fc[['ds','yhat']],
            product,
            gen
        )
    else:
        observed = {"x": [], "y": []}
        forecast = {"x": [], "y": []}
        insights = f"No time-series ≥2 points found for {product}."

    # --- 7) Save one insights file ---
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(insights_folder, f"insights_{ts}.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"Query: {query}\nProduct: {product}\n\n")
        f.write(insights)

    return observed, forecast, insights

def main():
    # --- Folders ---
    json_root    = "data/json_input"   # top-level folder containing your 4 subfolders
    graphs_folder = "data/graphs"
    insights_folder = "data/insights"
    os.makedirs(graphs_folder, exist_ok=True)
    os.makedirs(insights_folder, exist_ok=True)

    # --- LLM setup ---
    config = llm.load_config("config/config.json")
    _, _, _ = llm.authenticate_and_load_model(config)
    gen = lambda sys, usr: llm.generate_response(sys, usr)

    # --- 1) Build product index from all JSONs ---
    index, docs, embedder = analysis.build_product_index(json_root)

    # --- 2) Get user's query ---
    query = input("Enter your query (e.g. product name): ").strip()

    # --- 3) Find best matching product ---
    sys_p = "You are a product-search assistant."
    refined = gen(sys_p, query)
    # reuse your FAISS search fn:
    best = analysis.search_vector_store(refined, index, docs, embedder, top_k=1)[0]
    product = best["product"]
    print("Most relevant product:", product, "in file", best["file"])

    # --- 4) Extract its time series from all JSONs ---
    series = analysis.extract_product_timeseries(json_root, product)

    # --- 5) Plot & forecast if we have ≥2 points ---
    if len(series) >= 2:
        df = pd.DataFrame(series).rename(columns={"Date":"ds","value":"y"})
        model = Prophet().fit(df)
        future = model.make_future_dataframe(periods=14, freq='M')
        fc = model.predict(future)
        fc = fc[fc.ds > df.ds.max()]
        fc["yhat"] = fc["yhat"].clip(lower=0.0)

        import matplotlib.pyplot as plt
        plt.figure(figsize=(8,4))
        plt.plot(df.ds, df.y, label="Observed")
        plt.plot(fc.ds, fc.yhat, "--", label="Forecast")
        plt.legend()
        graph_path = os.path.join(graphs_folder, f"{product}_trend.png")
        plt.savefig(graph_path); plt.close()

        insights = analysis.generate_insights_from_predictions(
            fc[['ds','yhat']],
            product,
            gen
        )
    else:
        print("Not enough time series data for", product)
        insights = f"No time-series ≥2 points found for {product}."

    # --- 7) Save one insights file ---
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(insights_folder, f"insights_{ts}.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"Query: {query}\nProduct: {product}\n\n")
        f.write(insights)
    print("Insights saved to", out)

if __name__=="__main__":
    main()
