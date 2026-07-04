import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
import threading
import time


def run_model(get_mermaid_prompt: str):
    # Model selection
    model_id = "mistralai/Mistral-7B-Instruct-v0.3"
    print(model_id)
    # Uncomment to use other models:
    # model_id = "Qwen/Qwen2.5-Coder-32B-Instruct"
    # model_id = "Qwen/Qwen2.5-Coder-7B-Instruct"
    # model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

    print(f"Loading model: {model_id}")

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # Set pad_token if not set (fixes the second warning)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    model.eval()

    start = time.perf_counter()

    # Tokenize input
    inputs = tokenizer(get_mermaid_prompt, return_tensors="pt").to(model.device)

    print("Starting Generation...")

    # Setup streamer
    streamer = TextIteratorStreamer(
        tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,
    )

    # Generation parameters (fixed warnings)
    generation_kwargs = dict(
        **inputs,
        max_new_tokens=3250,
        do_sample=True,  # FIX: Enable sampling to use temperature
        temperature=0.7,
        top_p=0.95,
        pad_token_id=tokenizer.pad_token_id,  # FIX: Explicitly set pad token
        eos_token_id=tokenizer.eos_token_id,
        streamer=streamer,
    )

    # Start generation in separate thread
    generation_thread = threading.Thread(
        target=model.generate,
        kwargs=generation_kwargs,
        daemon=True,
    )
    generation_thread.start()

    print("\n=== STREAMING OUTPUT ===\n")

    # Stream and collect output
    generated_output = ""
    for token in streamer:
        print(token, end="", flush=True)
        generated_output += token

    # Wait for generation to complete
    generation_thread.join()

    end = time.perf_counter()
    print(f"\n\n=== Generation completed in {end - start:.2f} seconds ===\n")

    return generated_output