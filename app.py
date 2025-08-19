import os
from typing import List, Dict

import streamlit as st
from openai import OpenAI


# ---- Configuration and Helpers ----

def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages: List[Dict[str, str]] = []
    if "pending_user" not in st.session_state:
        st.session_state.pending_user: str | None = None


def build_system_prompt(style: str, safety: str, audience: str, length: str) -> str:
    return (
        "You are JesterBot, a friendly, quick-witted joke-telling assistant.\n\n"
        "Goals:\n"
        f"- Craft original jokes tailored to the user's request.\n"
        f"- Style: {style}\n"
        f"- Safety/Tone: {safety}\n"
        f"- Audience: {audience}\n"
        f"- Length: {length}\n\n"
        "Guidelines:\n"
        "- Deliver the joke directly (avoid meta prefaces like 'Here is a joke:').\n"
        "- Keep it concise unless asked for more.\n"
        "- Avoid offensive content, slurs, hate speech, or punching down.\n"
        "- If requested content conflicts with the safety level, decline briefly and offer a cleaner alternative.\n"
        "- Prefer clear line breaks where helpful; default to a single joke unless asked for multiple.\n"
        "- If asked to explain, provide a brief explanation after the joke.\n"
        "- If no topic is given, pick a playful everyday theme.\n"
    )


def build_messages(system_prompt: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    return [{"role": "system", "content": system_prompt}] + history


@st.cache_resource(show_spinner=False)
def get_client() -> OpenAI:
    return OpenAI()


def generate_reply(
    client: OpenAI,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.8,
    max_tokens: int = 200,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        presence_penalty=0.3,
        frequency_penalty=0.2,
    )
    return response.choices[0].message.content.strip()


def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})


def clear_chat():
    st.session_state.messages = []


def send_user_message(text: str, client: OpenAI, model: str, system_prompt: str, temperature: float, max_tokens: int):
    if not text:
        return
    add_message("user", text)
    with st.chat_message("user"):
        st.markdown(text)

    with st.chat_message("assistant"):
        with st.spinner("Working on a punchline..."):
            messages = build_messages(system_prompt, st.session_state.messages)
            reply = generate_reply(client, model, messages, temperature=temperature, max_tokens=max_tokens)
            st.markdown(reply)
    add_message("assistant", reply)


# ---- Streamlit App ----

def main():
    st.set_page_config(page_title="JesterBot - Joke Chatbot", page_icon="🎭", layout="centered")
    init_state()
    client = get_client()

    st.title("🎭 JesterBot")
    st.caption("Your on-demand joke companion. Ask for any style, topic, or audience.")

    # Sidebar settings
    with st.sidebar:
        st.header("Settings")
        model = st.selectbox(
            "Model",
            options=["gpt-4", "gpt-3.5-turbo"],
            index=0,
            help="gpt-4 for best wit and nuance; gpt-3.5-turbo for faster, cheaper laughs.",
        )

        style = st.selectbox(
            "Style",
            options=[
                "One-liner",
                "Pun",
                "Dad joke",
                "Observational",
                "Wordplay",
                "Knock-knock",
                "Light roast (kind, no insults)",
                "Absurdist",
            ],
            index=0,
        )

        safety = st.selectbox(
            "Safety/Tone",
            options=[
                "Family-friendly",
                "Edgy but respectful (no slurs, no insults, no hate)",
            ],
            index=0,
        )

        audience = st.selectbox(
            "Audience",
            options=["General", "Kids", "Techies", "Science lovers", "Movie fans"],
            index=0,
        )

        length = st.selectbox(
            "Length",
            options=["Short (1-2 lines)", "Medium (3-6 lines)"],
            index=0,
        )

        temperature = st.slider("Creativity (temperature)", 0.0, 1.5, 0.8, 0.05)
        max_tokens = st.slider("Max tokens for response", 64, 400, 200, 8)

        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Clear chat", help="Start fresh"):
                clear_chat()
                st.experimental_rerun()
        with col_b:
            if st.button("Tell me something random", help="Generate a random joke prompt"):
                st.session_state.pending_user = "Surprise me with a fresh, original joke."

        st.markdown("---")
        st.caption("Tip: Add a topic, like 'Make a pun about coffee' or 'A kids joke about dinosaurs'.")

    system_prompt = build_system_prompt(style, safety, audience, length)

    # Show existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Quick suggestions
    st.markdown("Try a quick prompt:")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        if st.button("Programmer one-liner"):
            st.session_state.pending_user = "Tell a clean one-liner about programmers."
    with s2:
        if st.button("Coffee pun"):
            st.session_state.pending_user = "Make a witty pun about coffee."
    with s3:
        if st.button("Gentle roast"):
            st.session_state.pending_user = "Gently roast my procrastination (keep it kind)."
    with s4:
        if st.button("Kids + dinosaurs"):
            st.session_state.pending_user = "A kids-friendly dinosaur joke, please."

    # Chat input
    user_text = st.chat_input("Ask for a joke or give a topic...")
    if user_text:
        send_user_message(user_text, client, model, system_prompt, temperature, max_tokens)

    # Handle pending quick-suggestion
    if st.session_state.pending_user:
        send_user_message(st.session_state.pending_user, client, model, system_prompt, temperature, max_tokens)
        st.session_state.pending_user = None


if __name__ == "__main__":
    main()