import os
import uuid
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from google import genai

# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="My AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
API_KEY = os.getenv("OPENAI_API_KEY")

INSTRUCTIONS = """
You are My AI, a helpful and friendly AI assistant.
Answer clearly and naturally.
Help with programming, writing, learning, brainstorming,
and everyday questions.
Use Markdown and code blocks when useful.
Be honest when you are unsure of an answer.
"""

# --------------------------------------------------
# Custom styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #212121;
        color: #ececec;
    }

    [data-testid="stSidebar"] {
        background-color: #171717;
        border-right: 1px solid #303030;
    }

    [data-testid="stHeader"] {
        background-color: transparent;
    }

    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 7rem;
    }

    .brand {
        font-size: 1.65rem;
        font-weight: 750;
        letter-spacing: -1px;
        margin-bottom: 1.2rem;
    }

    .brand span {
        color: #10a37f;
    }

    .subtitle {
        color: #a0a0a0;
        font-size: 0.92rem;
        text-align: center;
        margin-top: -8px;
        margin-bottom: 28px;
    }

    .stButton > button {
        border-radius: 10px;
        border: 1px solid #393939;
        text-align: left;
        min-height: 2.5rem;
    }

    .stButton > button:hover {
        border-color: #10a37f;
        color: #ffffff;
    }

    [data-testid="stChatInput"] {
        border-color: #454545;
    }

    [data-testid="stChatMessage"] {
        border-radius: 12px;
    }

    .sidebar-note {
        color: #8d8d8d;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Session state: multiple conversations
# --------------------------------------------------

def new_chat():
    chat_id = str(uuid.uuid4())

    st.session_state.chats[chat_id] = {
        "title": "New chat",
        "messages": [],
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    st.session_state.active_chat = chat_id


if "chats" not in st.session_state:
    st.session_state.chats = {}

if "active_chat" not in st.session_state:
    new_chat()

if st.session_state.active_chat not in st.session_state.chats:
    new_chat()

# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div class="brand">✳ <span>My</span> AI</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "＋  New chat",
        use_container_width=True,
        type="primary",
    ):
        new_chat()
        st.rerun()

    st.divider()
    st.caption("YOUR CONVERSATIONS")

    # Most recently created chats appear first.
    chat_items = list(st.session_state.chats.items())
    chat_items.reverse()

    for chat_id, chat in chat_items:
        is_active = chat_id == st.session_state.active_chat
        label = ("● " if is_active else "  ") + chat["title"]

        col_chat, col_delete = st.columns([5, 1])

        with col_chat:
            if st.button(
                label,
                key=f"open_{chat_id}",
                use_container_width=True,
            ):
                st.session_state.active_chat = chat_id
                st.rerun()

        with col_delete:
            if st.button(
                "×",
                key=f"delete_{chat_id}",
                help="Delete this conversation",
            ):
                del st.session_state.chats[chat_id]

                if not st.session_state.chats:
                    new_chat()
                elif st.session_state.active_chat == chat_id:
                    st.session_state.active_chat = next(
                        iter(st.session_state.chats)
                    )

                st.rerun()

    st.divider()
    st.markdown(
        '<div class="sidebar-note">'
        'AI-generated answers may contain mistakes.<br>'
        'Chats are stored in this browser session only.'
        '</div>',
        unsafe_allow_html=True,
    )

# --------------------------------------------------
# Main chat window
# --------------------------------------------------

active_id = st.session_state.active_chat
chat = st.session_state.chats[active_id]
messages = chat["messages"]

if not messages:
    st.markdown(
        "<h1 style='text-align:center; margin-top:15vh;'>"
        "What can I help with?</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">'
        'Ask a question, learn something, or build something amazing.'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown("### " + chat["title"])

    for message in messages:
        with st.chat_message(
            message["role"],
            avatar="🧑" if message["role"] == "user" else "✳️",
        ):
            st.markdown(message["content"])

# --------------------------------------------------
# Input and AI response
# --------------------------------------------------

prompt = st.chat_input("Message My AI...")

if prompt:
    # Save the user's message.
    messages.append({
        "role": "user",
        "content": prompt,
    })

    # Name the conversation after its first message.
    if chat["title"] == "New chat":
        chat["title"] = prompt.strip().replace("\n", " ")[:36]
        if len(prompt.strip()) > 36:
            chat["title"] += "..."

    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="✳️"):
        if not API_KEY:
            answer = (
                "Please configure OPENAI_API_KEY in your .env file, "
                "then restart the app."
            )
            st.error(answer)
        else:
            try:
                client = OpenAI(api_key=API_KEY)

                with st.spinner("Thinking..."):
                    response = client.responses.create(
                        model=MODEL,
                        instructions=INSTRUCTIONS,
                        input=[
                            {
                                "role": message["role"],
                                "content": message["content"],
                            }
                            for message in messages
                        ],
                    )

                answer = response.output_text or (
                    "I couldn't produce a text response. Please try again."
                )
                st.markdown(answer)

            except Exception:
                answer = (
                    "I couldn't reach the AI service. Please check your "
                    "internet connection, API key, API billing, and model "
                    "access, then try again."
                )
                st.error(answer)

    messages.append({
        "role": "assistant",
        "content": answer,
    })

    st.rerun()
