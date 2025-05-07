# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
# from huggingface_hub import login
# import json
# from src.config_loader import get_hf_api_key  # Import our helper

# def load_config(config_path='config/config.json'):
#     with open(config_path, 'r', encoding='utf-8') as f:
#         config = json.load(f)
#     # Override/add the HF_API_KEY from the environment
#     hf_api_key = get_hf_api_key()
#     if hf_api_key:
#         config["hf_api_key"] = hf_api_key
#     return config

# def authenticate_and_load_model(config):
#     hf_api_key = config.get("hf_api_key")
#     if hf_api_key:
#         login(hf_api_key)
#     model_name = config.get("model_name", "meta-llama/Meta-Llama-3-8B-Instruct")
#     device = config.get("device", "cuda")
#     model = AutoModelForCausalLM.from_pretrained(
#         model_name,
#         torch_dtype=torch.float16,
#         device_map="auto",
#         quantization_config=BitsAndBytesConfig(
#             load_in_4bit=True,
#             bnb_4bit_compute_dtype=torch.float16,
#             bnb_4bit_quant_type="nf4",
#         ),
#     )
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     return model, tokenizer, device

# def generate_response(system_prompt, user_prompt, temperature=0.7, max_tokens=500, model=None, tokenizer=None, device="cuda"):
#     messages = [
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": user_prompt}
#     ]
#     text = tokenizer.apply_chat_template(
#         messages,
#         tokenize=False,
#         add_generation_prompt=True
#     )
#     model_inputs = tokenizer([text], return_tensors="pt").to(device)
#     model.config.pad_token_id = model.config.eos_token_id
#     model_inputs['attention_mask'] = model_inputs['input_ids'].ne(model.config.pad_token_id).long()
#     generated_ids = model.generate(
#         model_inputs.input_ids,
#         attention_mask=model_inputs['attention_mask'],
#         max_new_tokens=max_tokens,
#         temperature=temperature,
#         do_sample=True,
#         top_k=10,
#         top_p=0.9,
#     )
#     response = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
#     return response

######################################################################################################################################################

# import subprocess
# import json

# def load_config(config_path='config/config.json'):
#     with open(config_path, 'r', encoding='utf-8') as f:
#         config = json.load(f)
#     return config

# def authenticate_and_load_model(config):
#     """
#     With Ollama, no model loading or authentication is needed in Python.
#     Ensure that Ollama is installed and that the model 'llama3.2:3b' is available.
#     Return dummy values.
#     """
#     return None, None, None

# def generate_response(system_prompt, user_prompt, temperature=0.7, max_tokens=500, **kwargs):
#     """
#     Generate a response using Ollama's CLI with the model 'llama3.2:3b'.
#     The system and user prompts are concatenated into a single prompt.
#     """
#     # Combine system prompt and user prompt into one string
#     prompt = f"{system_prompt}\n{user_prompt}"
#     try:
#         # Call Ollama CLI; adjust command-line parameters as needed per Ollama's documentation.
#         result = subprocess.run(
#             ["ollama", "run", "llama3.2:3b", prompt],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,
#             check=True
#         )
#         response = result.stdout.strip()
#         return response
#     except subprocess.CalledProcessError as e:
#         print("Error calling Ollama:", e.stderr)
#         return "Error generating response."

##############ollama code ###########################################################################################################


# import subprocess
# import json

# def load_config(config_path='config/config.json'):
#     with open(config_path, 'r', encoding='utf-8') as f:
#         config = json.load(f)
#     return config

# def authenticate_and_load_model(config):
#     """
#     With Ollama, no model loading or authentication is needed.
#     Ensure Ollama is installed and that the model 'llama3.2:3b' is available.
#     Return dummy values.
#     """
#     return None, None, None

# def generate_response(system_prompt, user_prompt, temperature=0.7, max_tokens=500, **kwargs):
#     """
#     Generate a response using Ollama's CLI with the model 'llama3.2:3b'.
#     Combines system and user prompts into a single prompt.
#     """
#     prompt = f"{system_prompt}\n{user_prompt}"
#     try:
#         result = subprocess.run(
#             ["ollama", "run", "llama3.2:3b", prompt],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,
#             encoding="utf-8",
#             check=True
#         )
#         response = result.stdout.strip()
#         return response
#     except subprocess.CalledProcessError as e:
#         print("Error calling Ollama:", e.stderr)
#         return "Error generating response."


############multi modal code###############

# import subprocess
# import json

# def load_config(config_path='config/config.json'):
#     with open(config_path, 'r', encoding='utf-8') as f:
#         config = json.load(f)
#     return config

# def authenticate_and_load_model(config):
#     """
#     With Ollama, no model loading or authentication is needed.
#     Ensure Ollama is installed and that the model 'llama3.2:3b' is available.
#     Return dummy values.
#     """
#     return None, None, None

# def generate_response(system_prompt, user_prompt, temperature=0.7, max_tokens=500, **kwargs):
#     """
#     Generate a response using Ollama's CLI with the model 'llama3.2:3b'.
#     Combines system and user prompts into a single prompt.
#     """
#     prompt = f"{system_prompt}\n{user_prompt}"
#     try:
#         result = subprocess.run(
#             ["ollama", "run", "llama3.2:3b", prompt],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             text=True,
#             encoding="utf-8",
#             check=True
#         )
#         response = result.stdout.strip()
#         return response
#     except subprocess.CalledProcessError as e:
#         print("Error calling Ollama:", e.stderr)
#         return "Error generating response."


# src/llm.py #####aiagent code#######

# src/llm.py
import json
from langchain_ollama.llms import OllamaLLM

_llm = None

def load_config(config_path='config/config.json'):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def authenticate_and_load_model(config):
    global _llm
    model_name = config.get("model_name", "llama3.2:3b")
    _llm = OllamaLLM(model=model_name)
    return None, None, None

def generate_response(system_prompt, user_prompt, temperature=0.7, max_tokens=500, **kwargs):
    if _llm is None:
        raise RuntimeError("Call authenticate_and_load_model first")
    prompt = f"SYSTEM: {system_prompt}\nUSER: {user_prompt}\nASSISTANT:"
    return _llm.invoke(prompt)

