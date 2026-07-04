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

def ask_gpt(messages):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",     # or gpt-3.5-turbo
        messages=messages
    )
    return response.choices[0].message.content

def chat():
    print("ChatBot: Ask me anything! (type 'exit' to quit)\n")

    messages = []  # full conversation stored here

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Chat ended.")
            break

        messages.append({"role": "user", "content": user_input})

        answer = ask_gpt(messages)

        print("\nBot:", answer, "\n")

        messages.append({"role": "assistant", "content": answer})
        # This stores the model’s reply as part of the conversation history.

if __name__ == "__main__":
    chat()
