import csv
from config.settings import Settings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from datetime import datetime
from typing import Any
import os

def log_llm_input(llm_input):
    file_path = "./src/logs/llm_input.txt"
    # ✅ Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, mode = "w") as f:
            f.write("Empty" if not llm_input else "\n" + "\n".join(
                f"{'DORI' if isinstance(m, AIMessage) else 'User' if isinstance(m, HumanMessage) else 'System' if isinstance(m, SystemMessage) else 'Tool'} - {m.content}"
                for m in llm_input
            ))
    
    
    
    
    
def log_token_usage(ai_message: AIMessage, messages_list: list[Any]):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if Settings.MODEL_SERVER == "OLLAMA":
        token_usage = {
            "input_tokens": ai_message.usage_metadata.get("input_tokens", 0),
            "output_tokens": ai_message.usage_metadata.get("output_tokens", 0),
        }
    if Settings.MODEL_SERVER == "OPENAI":
        token_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
        }
    if Settings.MODEL_SERVER == "CLAUDE":
        token_usage = {
            "input_tokens": ai_message.usage_metadata.get("input_tokens", 0),
            "output_tokens": ai_message.usage_metadata.get("output_tokens", 0),
        }
        

    file_path = "./src/logs/token_usage_log.csv"
    # ✅ Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Clear file if messages_list has length 1
    if len(messages_list) == 1:
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "input_tokens", "output_tokens", "total_tokens"])
    
    # Append new row
    with open(file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        total = token_usage["input_tokens"] + token_usage["output_tokens"]
        writer.writerow([timestamp, token_usage["input_tokens"], token_usage["output_tokens"], total])
        
#from transformers import AutoTokenizer
# def count_tokens(text: str):
#     """
#     Count the number of tokens in a given text using a tokenizer.
#     """
#     # Load the tokenizer
#     tokenizer = AutoTokenizer.from_pretrained("openchat/openchat-3.5-0106")
    
#     # Encode the text and count tokens
#     token_ids = tokenizer.encode(text, return_tensors="pt")
    
#     return len(token_ids[0])

