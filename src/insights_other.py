################## normal  code ################## 

# import os

# def load_other_texts(folder_path: str) -> dict:
#     """
#     Load all text files from the specified folder and return a dictionary
#     with keys as filenames and values as the file content.
#     """
#     texts = {}
#     for file in os.listdir(folder_path):
#         if file.endswith(".txt"):
#             path = os.path.join(folder_path, file)
#             with open(path, "r", encoding="utf-8") as f:
#                 texts[file] = f.read()
#     return texts

# def generate_other_insights(user_query: str, texts: dict, generate_response_func) -> str:
#     """
#     Concatenate the texts (or otherwise process them) and generate insights based on a user query.
#     The generate_response_func should be your LLM function that accepts a system prompt and a user prompt.
#     """
#     combined_text = "\n\n".join(texts.values())
#     prompt = (
#         f"Given the following text data:\n\n{combined_text}\n\n"
#         f"User query: {user_query}\n\n"
#         "Please provide actionable business insights based on the above data."
#     )
#     insights = generate_response_func("Generate business insights", prompt, temperature=0.7, max_tokens=1000)
#     return insights


##### multi modal code ######

#import os

# def load_other_texts(folder_path: str) -> dict:
#     texts = {}
#     for file in os.listdir(folder_path):
#         if file.endswith(".txt"):
#             path = os.path.join(folder_path, file)
#             with open(path, "r", encoding="utf-8") as f:
#                 texts[file] = f.read()
#     return texts

# def generate_other_insights(user_query: str, texts: dict, generate_response_func) -> str:
#     combined_text = "\n\n".join(texts.values())
#     prompt = (
#         f"Given the following multi-modal text data:\n\n{combined_text}\n\n"
#         f"User query: {user_query}\n\n"
#         "Please provide actionable business insights based on the above data."
#     )
#     insights = generate_response_func("Generate business insights", prompt, temperature=0.7, max_tokens=1000)
#     return insights

####agents

# def generate_other_insights(user_query: str, texts: dict, generate_response_func) -> str:
#     combined_text = "\n\n".join(texts.values())
#     combined_prompt = (
#         "Generate business insights\n\n"
#         f"Data:\n{combined_text}\n\n"
#         f"User query: {user_query}\n\n"
#         "Please provide actionable business insights based on the above data."
#     )
#     # llm_client was already given temperature & max_tokens at init,
#     # so here we call with exactly one positional arg:
#     insights = generate_response_func(combined_prompt)
#     return insights

# src/insights_other.py agntsmul

# import os

# def load_other_texts(folder_path: str) -> dict:
#     texts = {}
#     for file in os.listdir(folder_path):
#         if file.endswith(".txt"):
#             path = os.path.join(folder_path, file)
#             with open(path, "r", encoding="utf-8") as f:
#                 texts[file] = f.read()
#     return texts

# def generate_other_insights(
#     user_query: str,
#     texts: dict,
#     generate_response_func,
#     timeseries_df=None,
#     forecast_df=None,
#     category: str = None
# ) -> str:
#     """
#     If you pass in `timeseries_df` & `forecast_df` & `category`,
#     it will first summarise the forecast.  Then it will append
#     all the `texts` context, and finally send one big prompt
#     to your LLM via generate_response_func.
#     """
#     prompt_parts = []

#     # 1) If there is a time-series, summarize it
#     if timeseries_df is not None and forecast_df is not None and category:
#         last_obs = timeseries_df.iloc[-1]
#         summary = [
#             f"## Forecast summary for '{category}':",
#             f"- Last observed {category}: {last_obs['y']} on {last_obs['ds'].date()}",
#             "## Predictions:",
#         ]
#         for _, row in forecast_df.iterrows():
#             summary.append(f"- {row['ds'].date()}: {row['yhat']:.2f}")
#         prompt_parts.append("\n".join(summary))

#     # 2) Then add all other text-contexts
#     if texts:
#         prompt_parts.append("## Additional Context from other files:")
#         for fname, content in texts.items():
#             prompt_parts.append(f"--- {fname} ---\n{content}")

#     # 3) Finally add the user's original question
#     prompt_parts.append(f"## User Query:\n{user_query}")

#     full_prompt = "\n\n".join(prompt_parts)

#     # 4) Call your LLM once
#     return generate_response_func(
#         "You are a senior business consultant.  Based on the data below, "
#         "provide a single, unified set of actionable insights and recommendations.",
#         full_prompt
#     )


#######agentsltst

import os
from typing import Callable, Optional
import pandas as pd

def generate_other_insights(
    user_query: str,
    texts: dict,
    generate_response_fn: Callable[[str,str], str],
    timeseries_df: Optional[pd.DataFrame] = None,
    forecast_df:  Optional[pd.DataFrame] = None,
    category:     Optional[str]     = None,
) -> str:
    """
    Combine any time-series forecast + extracted text, then ask the LLM.
    Enhanced to provide product/category-specific context and richer prompts.
    """
    # 1) Build system + user prompt
    product_str = f" for '{category}'" if category else ""
    system = (
        f"You are a senior business consultant. Use all the data provided to generate a concise, actionable report for business decision-making regarding{product_str}."
    )

    user_parts = []

    # 2) If we have a forecast, include a summary
    if timeseries_df is not None and forecast_df is not None and category:
        last_obs = timeseries_df.iloc[-1]
        first_fc = forecast_df.iloc[0]
        user_parts.append(
            f"## Forecast summary for {category}:\n"
            f"- Last observed value: {last_obs.y:.2f} on {last_obs.ds.date()}\n"
            f"- Next period forecast: {first_fc.yhat:.2f} on {first_fc.ds.date()}"
        )
        # Attach full forecast table (clipped to non-negative)
        forecast_df = forecast_df.copy()
        forecast_df['yhat'] = forecast_df['yhat'].clip(lower=0.0)
        user_parts.append(
            "### Full Forecast Table:\n" +
            forecast_df[['ds','yhat']].to_string(index=False)
        )

    # 3) Add product/category context from text docs (filter for product if possible)
    if texts:
        user_parts.append(f"## Additional extracted text data for {category if category else 'context'}:")
        for fn, content in texts.items():
            # Only include text mentioning the category/product if possible
            if category is None or (category.lower() in content.lower() or category.lower() in fn.lower()):
                user_parts.append(f"--- from `{fn}` ---\n{content[:1000]}")  # first 1k chars

    # 4) The actual user question
    user_parts.append(f"## User query about {category if category else 'the business'}:\n{user_query}")

    full_user = "\n\n".join(user_parts)

    # 5) Call the LLM with stop sequences
    stop_sequences = ["## User query:", "## Forecast summary", "## Additional extracted text data"]
    prompt = f"{system}\n\n{full_user}"
    try:
        return generate_response_fn.invoke(prompt, stop=stop_sequences)
    except AttributeError:
        return generate_response_fn(prompt, stop=stop_sequences)


