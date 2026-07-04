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
# --- Send the request ---
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    temperature=0.2,
    messages=[
        {"role": "user", "content": "Explain about hyderabad city."}
    ]
)

print(response.choices[0].message.content)