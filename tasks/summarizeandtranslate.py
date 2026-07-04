from dotenv import load_dotenv
import os
from openai import AzureOpenAI

# Load .env
load_dotenv()

api_key = os.getenv("AZURE_OPENAI_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

if not api_key or not endpoint:
    raise ValueError("Missing AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT in environment variables.")

# Create Azure OpenAI client
client = AzureOpenAI(
    api_key=api_key,
    api_version="2024-05-01-preview",
    azure_endpoint=endpoint
)
# Original text
text = """
Artificial Intelligence (AI) is revolutionizing industries by automating tasks,
enhancing decision-making, and enabling new innovations. From healthcare to finance,
AI applications are improving efficiency and accuracy at an unprecedented scale.
"""

# 1. Summarization
summary_prompt = f"Summarize the following text in 50 words:\n{text}"

summary_response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": summary_prompt}
    ],
    temperature=0.2,  # Low randomness for factual summarization

)

summary = summary_response.choices[0].message.content
print("Summary:", summary)
#
# 2. Translation
translation_prompt = f"Translate the following summary into Telugu:\n{summary}"

translation_response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": translation_prompt}
    ],
    temperature=0.3,

)

translation = translation_response.choices[0].message.content
print("Translation:", translation)