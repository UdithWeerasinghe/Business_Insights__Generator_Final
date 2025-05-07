##############normal code ####################

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from prophet import Prophet
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
import faiss
from datetime import datetime

def find_json_files(directory):
    json_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files

def load_json_data(directory):
    json_files = find_json_files(directory)
    data = []
    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            data.append(json.load(f))
    return data

def build_vector_store(categories):
    vectorizer = TfidfVectorizer(stop_words='english')
    category_embeddings = vectorizer.fit_transform(categories)
    return vectorizer, category_embeddings

# --- New FAISS Vector Store Functions ---

def build_faiss_index(output_directory):
    """
    Loads JSON files from the output_directory and builds a FAISS index.
    Returns: (index, documents, embedder)
    Each document is a dict: {"text": ..., "metadata": {...}, "category": ...}
    """
    documents = []
    json_files = find_json_files(output_directory)
    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        meta = content.get("metadata", {})
        data = content.get("data", {})
        for category in data.keys():
            # Create a document string combining the category and source metadata.
            doc_text = f"Category: {category}. File: {meta.get('file_name','')}. Sheet: {meta.get('sheet_name','')}."
            documents.append({"text": doc_text, "metadata": meta, "category": category})
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    doc_texts = [doc["text"] for doc in documents]
    doc_embeddings = embedder.encode(doc_texts, convert_to_numpy=True)
    embedding_dim = doc_embeddings.shape[1]
    index = faiss.IndexFlatL2(embedding_dim)
    index.add(doc_embeddings)
    print(f"FAISS index built with {index.ntotal} documents.")
    return index, documents, embedder

def search_vector_store(query, index, documents, embedder, top_k=1):
    query_embedding = embedder.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, top_k)
    results = []
    for idx in indices[0]:
        results.append(documents[idx])
    return results

def analyze_query_with_llm_faiss(user_query, generate_response_func, index, documents, embedder):
    system_prompt = "You are an expert data analyst. Help refine this query to better match data categories."
    refined_query = generate_response_func(system_prompt, user_query)
    results = search_vector_store(refined_query, index, documents, embedder, top_k=1)
    if results:
        best_match = results[0]
        print(f"Most relevant category: {best_match['category']}")
        print(f"Found in file: {best_match['metadata'].get('file_name')} sheet: {best_match['metadata'].get('sheet_name')}")
        return best_match['category']
    else:
        return None

def extract_values_for_category(json_data, category):
    values = []
    for file_data in json_data:
        data = file_data.get("data", {})
        if category in data:
            values.extend(data[category])
    return values

def plot_trend_and_save(values, category, output_file):
    dates = []
    y_values = []
    for entry in values:
        dates.append(entry["Date"])
        y_values.append(entry["value"])
    dates = pd.to_datetime(dates)
    df = pd.DataFrame({'ds': dates, 'y': y_values})
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=14, freq='M')
    forecast = model.predict(future)
    forecast_filtered = forecast[forecast['ds'] > max(dates)]
    plt.figure(figsize=(10,6))
    sns.lineplot(x=dates, y=y_values, label=f'{category} (Observed)', color='blue')
    sns.lineplot(x=forecast_filtered['ds'], y=forecast_filtered['yhat'],
                 label=f'{category} (Predicted)', color='orange', linestyle='--')
    if not forecast_filtered.empty:
        plt.plot([max(dates), forecast_filtered['ds'].iloc[0]],
                 [y_values[-1], forecast_filtered['yhat'].iloc[0]],
                 color='orange', linestyle='--')
    plt.title(f'Trend and Prediction for {category}')
    plt.xlabel('Time')
    plt.ylabel(category)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def display_predicted_values(values):
    dates = []
    y_values = []
    for entry in values:
        dates.append(entry["Date"])
        y_values.append(entry["value"])
    dates = pd.to_datetime(dates)
    df = pd.DataFrame({'ds': dates, 'y': y_values})
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=14, freq='M')
    forecast = model.predict(future)
    last_date = max(dates)
    forecast_filtered = forecast[forecast['ds'] > last_date]
    predicted_values = forecast_filtered[['ds', 'yhat']]
    print("Predicted Values for upcoming periods:")
    print(predicted_values.to_string(index=False))

# def generate_insights_from_predictions(predicted_values, parameter, generate_response_func):
#     summary_text = (
#         f"The parameter '{parameter}' has been analyzed with the following predicted values "
#         "for each month from the last observed date onward:\n\n"
#     )
    
#     summary_text += predicted_values.to_string(index=False, header=False)
#     summary_text += (
#         "\n\nProvide insights, recommendations, and suggestions to improve decision-making for this parameter."
#     )
#     system_prompt = (
#         "You are a highly skilled business consultant specializing in data-driven decision-making. "
#         "Analyze the provided predictions and generate actionable insights and recommendations."
#     )
#     insights = generate_response_func(system_prompt, summary_text, temperature=0.7, max_tokens=1000)
#     print(f"Insights and Recommendations for '{parameter}':\n")
#     print(insights)
#     return insights

###########3before agent working one

# def generate_insights_from_predictions(predicted_values, parameter, generate_response_func):
#     # If predicted_values is a list (raw Excel data), compute forecast first:
#     if isinstance(predicted_values, list):
#         dates = [entry["Date"] for entry in predicted_values]
#         y_values = [entry["value"] for entry in predicted_values]
#         dates = pd.to_datetime(dates)
#         df = pd.DataFrame({'ds': dates, 'y': y_values})
#         model = Prophet()
#         model.fit(df)
#         future = model.make_future_dataframe(periods=14, freq='M')
#         forecast = model.predict(future)
#         last_date = max(dates)
#         forecast_filtered = forecast[forecast['ds'] > last_date]
#         predicted_values_df = forecast_filtered[['ds', 'yhat']]
#     else:
#         predicted_values_df = predicted_values  # Assume it is a DataFrame

#     summary_text = (
#         f"The parameter '{parameter}' has been analyzed with the following predicted values "
#         "for each month from the last observed date onward:\n\n"
#     )
#     summary_text += predicted_values_df.to_string(index=False, header=False)
#     summary_text += (
#         "\n\nProvide insights, recommendations, and suggestions to improve decision-making for this parameter."
#     )
#     system_prompt = (
#         "You are a highly skilled business consultant specializing in data-driven decision-making. "
#         "Analyze the provided predictions and generate actionable insights and recommendations."
#     )
#     insights = generate_response_func(system_prompt, summary_text, temperature=0.7, max_tokens=1000)
#     print(f"Insights and Recommendations for '{parameter}':\n")
#     print(insights)
#     return insights




############ multi-modal code #######################


# def build_unified_index(excel_json_dir: str, other_text_dir: str):
#     """
#     Build a single FAISS index over:
#       - Excel time-series categories (one doc per category)
#       - Other text files (one doc per file)
#     Returns (index, documents, embedder)
#     where documents is a list of dicts with metadata.
#     """
#     documents = []
#     # 1) Excel JSON entries
#     for root, _, files in os.walk(excel_json_dir):
#         for fname in files:
#             if not fname.endswith('.json'): continue
#             path = os.path.join(root, fname)
#             content = json.load(open(path, 'r', encoding='utf-8'))
#             meta = content.get("metadata", {})
#             data = content.get("data", {})
#             for category, series in data.items():
#                 # Represent time-series doc by its category name + a summary
#                 summary = f"Category: {category}. Source: {meta.get('file_name')} / {meta.get('sheet_name')}."
#                 documents.append({
#                     "id": len(documents),
#                     "type": "timeseries",
#                     "text": summary,
#                     "category": category,
#                     "file": meta.get("file_name"),
#                     "sheet": meta.get("sheet_name"),
#                     "series": series
#                 })

#     # 2) Other text files
#     for root, _, files in os.walk(other_text_dir):
#         for fname in files:
#             if not fname.lower().endswith('.txt'): continue
#             path = os.path.join(root, fname)
#             text = open(path, 'r', encoding='utf-8').read()
#             documents.append({
#                 "id": len(documents),
#                 "type": "text",
#                 "text": text,
#                 "file": fname
#             })

#     # 3) Embed
#     embedder = SentenceTransformer('all-MiniLM-L6-v2')
#     texts = [doc["text"] for doc in documents]
#     embeddings = embedder.encode(texts, convert_to_numpy=True)

#     # 4) Build FAISS index
#     dim = embeddings.shape[1]
#     index = faiss.IndexFlatL2(dim)
#     index.add(embeddings)

#     print(f"Unified FAISS index built with {index.ntotal} documents.")
#     return index, documents, embedder

# def retrieve_relevant_docs(query: str, index, documents, embedder, top_k: int = 5):
#     """
#     Returns the top_k document dicts most similar to the query.
#     """
#     q_emb = embedder.encode([query], convert_to_numpy=True)
#     distances, indices = index.search(q_emb, top_k)
#     return [documents[i] for i in indices[0]]

def build_unified_index(excel_json_dir: str, other_text_dir: str):
    """
    Build a single FAISS index over:
      1) Excel time‑series (one doc per category, with metadata & raw series)
      2) Other extracted text files (one doc per .txt)
    Returns: (index, documents, embedder)
    """
    from sentence_transformers import SentenceTransformer
    import faiss

    documents = []

    # 1) Excel JSON entries → timeseries docs
    for fp in find_json_files(excel_json_dir):
        with open(fp, 'r', encoding='utf-8') as f:
            content = json.load(f)
        meta = content.get("metadata", {})
        for cat, series in content.get("data", {}).items():
            summary = f"Category: {cat}. Source: {meta.get('file_name')} / {meta.get('sheet_name')}."
            documents.append({
                "type": "timeseries",
                "text": summary,
                "category": cat,
                "file": meta.get("file_name"),
                "sheet": meta.get("sheet_name"),
                "series": series
            })

    # 2) Other text files → text docs
    for fname in os.listdir(other_text_dir):
        if not fname.lower().endswith(".txt"):
            continue
        path = os.path.join(other_text_dir, fname)
        text = open(path, 'r', encoding='utf-8').read()
        documents.append({
            "type": "text",
            "text": text,
            "file": fname
        })

    # 3) Embed all documents
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    texts = [d["text"] for d in documents]
    embeddings = embedder.encode(texts, convert_to_numpy=True)

    # 4) Build the FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    print(f"Unified FAISS index built with {index.ntotal} documents.")
    return index, documents, embedder

def retrieve_relevant_docs(query: str, index, documents, embedder, top_k: int = 5):
    """
    Given a user query, return the top_k documents (timeseries & text) most similar.
    """
    q_emb = embedder.encode([query], convert_to_numpy=True)
    distances, indices = index.search(q_emb, top_k)
    return [documents[i] for i in indices[0]]

# def generate_insights_from_predictions(predicted_values, parameter, generate_response_func):
#     # If predicted_values is a list (raw Excel data), compute forecast first:
#     if isinstance(predicted_values, list):
#         dates = [entry["Date"] for entry in predicted_values]
#         y_values = [entry["value"] for entry in predicted_values]
#         dates = pd.to_datetime(dates)
#         df = pd.DataFrame({'ds': dates, 'y': y_values})
#         model = Prophet()
#         model.fit(df)
#         future = model.make_future_dataframe(periods=14, freq='M')
#         forecast = model.predict(future)
#         last_date = max(dates)
#         forecast_filtered = forecast[forecast['ds'] > last_date]
#         predicted_values_df = forecast_filtered[['ds', 'yhat']]
#     else:
#         predicted_values_df = predicted_values  # Assume it is a DataFrame

#     summary_text = (
#         f"The parameter '{parameter}' has been analyzed with the following predicted values "
#         "for each month from the last observed date onward:\n\n"
#     )
#     summary_text += predicted_values_df.to_string(index=False, header=False)
#     summary_text += (
#         "\n\nProvide insights, recommendations, and suggestions to improve decision-making for this parameter."
#     )
#     system_prompt = (
#         "You are a highly skilled business consultant specializing in data-driven decision-making. "
#         "Analyze the provided predictions and generate actionable insights and recommendations."
#     )
#     full_prompt = system_prompt + "\n\n" + summary_text
#     # Call with one positional arg:
#     insights = generate_response_func(full_prompt)
#     #insights = generate_response_func(full_prompt, temperature=0.7, max_tokens=1000)

#     print(f"Insights and Recommendations for '{parameter}':\n")
#     print(insights)
#     return insights

#####newdata

def build_product_index(json_root: str):
    """
    Walk json_root (recursively) and pull out every "(product, date)" pair
    as a tiny document for FAISS.  Returns (index, documents, embedder),
    where each documents[i] has keys: text, product, file.
    """
    documents = []
    for dirpath, _, files in os.walk(json_root):
        for fn in files:
            if not fn.lower().endswith(".json"):
                continue
            path = os.path.join(dirpath, fn)
            c = json.load(open(path, "r", encoding="utf-8"))
            # 1) stock reports
            if "ReportDate" in c and "Items" in c:
                date = c["ReportDate"]
                for item in c["Items"]:
                    prod = item.get("Product")
                    if prod:
                        txt = f"Product: {prod}. Date: {date}."
                        documents.append({"text": txt, "product": prod, "file": fn})
            # 2) invoices & purchase orders
            elif "OrderDate" in c and "Products" in c:
                date = c["OrderDate"]
                for p in c["Products"]:
                    prod = p.get("ProductName") or p.get("Product")
                    if prod:
                        txt = f"Product: {prod}. Date: {date}."
                        documents.append({"text": txt, "product": prod, "file": fn})
            # 3) shipping orders
            elif "OrderDetails" in c and "Products" in c["OrderDetails"]:
                od = c["OrderDetails"]
                date = od.get("OrderDate")
                for p in od["Products"]:
                    prod = p.get("Product")
                    if prod:
                        txt = f"Product: {prod}. Date: {date}."
                        documents.append({"text": txt, "product": prod, "file": fn})
    # embed + build index
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    texts = [d["text"] for d in documents]
    embs  = embedder.encode(texts, convert_to_numpy=True)
    dim = embs.shape[1]
    idx = faiss.IndexFlatL2(dim)
    idx.add(embs)
    print(f"Product FAISS index built with {idx.ntotal} docs.")
    return idx, documents, embedder

def extract_product_timeseries(json_root: str, product_name: str):
    """
    Walk the same tree, pull out every time-stamped record for that product,
    normalize to {'Date': pd.Timestamp, 'value': float}, sort, return list.
    """
    series = []
    for dirpath, _, files in os.walk(json_root):
        for fn in files:
            if not fn.lower().endswith(".json"):
                continue
            path = os.path.join(dirpath, fn)
            c = json.load(open(path, "r", encoding="utf-8"))
            # 1) stock
            if "ReportDate" in c and "Items" in c:
                for item in c["Items"]:
                    if item.get("Product")==product_name:
                        series.append({
                            "Date":            c["ReportDate"],
                            "value":          item.get("UnitsSold", 0)
                        })
            # 2) invoices & purchase
            elif "OrderDate" in c and "Products" in c:
                for p in c["Products"]:
                    prod = p.get("ProductName") or p.get("Product")
                    if prod==product_name:
                        # here we take money earned; swap to p["Quantity"] if you prefer
                        val = p.get("Quantity",0) * p.get("UnitPrice",0)
                        series.append({"Date": c["OrderDate"], "value": val})
            # 3) shipping
            elif "OrderDetails" in c and "Products" in c["OrderDetails"]:
                od = c["OrderDetails"]
                for p in od["Products"]:
                    if p.get("Product")==product_name:
                        val = p.get("Total") or (p.get("Quantity",0)*p.get("UnitPrice",0))
                        series.append({"Date": od.get("OrderDate"), "value": val})
    # normalize & sort
    for e in series:
        e["Date"] = pd.to_datetime(e["Date"])
    return sorted(series, key=lambda x: x["Date"])

# def generate_insights_from_predictions(predicted_values, parameter, generate_response_func):
#     # If they already passed a DataFrame, normalize its column names:
#     if isinstance(predicted_values, pd.DataFrame):
#         df = predicted_values.copy()
#         if 'Date' in df.columns:
#             df = df.rename(columns={'Date':'ds'})
#         if 'Predicted Value' in df.columns:
#             df = df.rename(columns={'Predicted Value':'yhat'})
#         predicted_df = df[['ds','yhat']]
#     else:
#         # They passed a list of raw entries → run Prophet internally
#         dates = [e["Date"] for e in predicted_values]
#         y_values = [e["value"] for e in predicted_values]
#         dates = pd.to_datetime(dates)
#         df2 = pd.DataFrame({'ds': dates, 'y': y_values})
#         m = Prophet(); m.fit(df2)
#         future = m.make_future_dataframe(periods=14, freq='M')
#         fc = m.predict(future)
#         last = df2['ds'].max()
#         predicted_df = fc[fc['ds'] > last][['ds','yhat']]

#     # Build the prompt
#     summary = "\n".join(f"{row['ds'].date()}: {row['yhat']:.2f}"
#                         for _, row in predicted_df.iterrows())
#     system_prompt = (
#         "You are a seasoned business consultant. "
#         "Here are the forecasted values:"
#     )
#     user_prompt = summary + "\n\n"
#     user_prompt += "Provide actionable insights, recommendations, and suggestions."
    
#     # TWO-argument call
#     return generate_response_func(system_prompt, user_prompt)



def generate_insights_from_predictions(predicted_values, parameter, generate_response_func):
    """
    Accepts either
      - a DataFrame with ['ds','yhat']  or
      - a DataFrame with ['Date','Predicted Value']
      - or even a raw list of {"Date":..., "value":...}
    and normalizes it to (ds,yhat) before building the LLM prompt.
    """
    # 1) turn raw list → forecast df
    if isinstance(predicted_values, list):
        dates = [e["Date"] for e in predicted_values]
        y_vals = [e["value"] for e in predicted_values]
        dates = pd.to_datetime(dates)
        df0 = pd.DataFrame({'ds': dates, 'y': y_vals})
        m = Prophet(); m.fit(df0)
        fut = m.make_future_dataframe(periods=14, freq='M')
        fc = m.predict(fut)
        last = df0['ds'].max()
        df = fc[fc['ds'] > last][['ds','yhat']]
    else:
        # 2) copy & rename whatever you got
        df = predicted_values.copy()
        if 'Date' in df.columns:
            df = df.rename(columns={'Date':'ds'})
        if 'Predicted Value' in df.columns:
            df = df.rename(columns={'Predicted Value':'yhat'})
        # catch any "y" → "yhat"
        if 'y' in df.columns and 'yhat' not in df.columns:
            df = df.rename(columns={'y':'yhat'})
        # now enforce exactly these two
        df = df[['ds','yhat']]
    
    # --- Ensure no negative predictions ---
    df['yhat'] = df['yhat'].clip(lower=0.0)

    # 3) build a simple text summary
    summary_lines = [f"{row['ds'].date()}: {row['yhat']:.2f}" for _, row in df.iterrows()]
    summary = "\n".join(summary_lines)

    system_prompt = (
        "You are a seasoned business consultant.  "
        f"You just forecasted `{parameter}`.  "
        "Here are the predictions:"
    )
    user_prompt = summary + "\n\nProvide actionable insights, recommendations, and suggestions."

    # 4) your LLM wants (sys, usr)
    insights = generate_response_func(system_prompt, user_prompt)
    return insights
