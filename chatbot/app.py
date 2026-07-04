import streamlit as st
from dotenv import load_dotenv
import os
from openai import AzureOpenAI

load_dotenv()

def init_openai_client():
    return AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-06-01"
    )

# Initialize Session State
def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []  # current chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []  # all previous chats

# Display Chat History
def display_chat_history():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# Get User Input
def get_user_input():
    return st.chat_input("Type your message...")

# Process User Message
def process_user_message(user_input):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

# Get Bot Response
def get_bot_response(client, deployment):
    response = client.chat.completions.create(
        model=deployment,
        messages=st.session_state.messages
    )
    return response.choices[0].message.content

# Display Bot Response
def display_bot_response(bot_reply):
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.write(bot_reply)

# Main App
def main():
    st.set_page_config(page_title="Simple Chatbot")
    st.title("Simple Chatbot with Streamlit")

    init_session_state()
    client = init_openai_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    # Sidebar: Show previous chats
    st.sidebar.title("Chat History")
    if st.session_state.chat_history:
        for i, chat in enumerate(st.session_state.chat_history):
            st.sidebar.write(f"Chat {i+1}:")
            for msg in chat[:3]:  # show first 3 messages as preview
                st.sidebar.write(f"- {msg['role']}: {msg['content'][:40]}...")
    else:
        st.sidebar.write("No previous chats yet.")

    # Display current chat
    display_chat_history()

    # Get user input
    user_input = get_user_input()

    if user_input:
        process_user_message(user_input)
        bot_reply = get_bot_response(client, deployment)
        display_bot_response(bot_reply)

    # Button to start new chat
    if st.sidebar.button("Start New Chat"):
        if st.session_state.messages:
            st.session_state.chat_history.append(st.session_state.messages.copy())
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()