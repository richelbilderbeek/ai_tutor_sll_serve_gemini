import argparse
import os
import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# 1. Parse Command-Line Arguments
# ---------------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument(
    "--api-key",
    type=str,
    default=None,
    help="Gemini API Key"
)
args, _ = parser.parse_known_args()

# Determine API key precedence: CLI flag -> Environment variable -> None
initial_api_key = args.api_key or os.environ.get("GEMINI_API_KEY")

# ---------------------------------------------------------
# 2. Page Configuration & Title
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Tutor - SciLifeLab Serve",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 Socratic AI Tutor")
st.caption("Powered by Gemini • Hosted on SciLifeLab Serve")

# ---------------------------------------------------------
# 3. System Prompt (Pedagogical Socratic Scaffolding)
# ---------------------------------------------------------
TUTOR_SYSTEM_INSTRUCTION = """You are an expert, encouraging Socratic tutor. 
Your primary goal is to guide students to discover solutions and understand core concepts independently.

Pedagogical Rules:
1. Never provide the direct solution, full answers, or completed assignments.
2. Guide the student step-by-step using probing questions, conceptual hints, and analogies.
3. Ask ONLY ONE question per response to prevent cognitive overload.
4. If the student asks for the answer directly, politely decline and offer a simpler hint or break the problem into a smaller sub-step.
5. If the student makes an error, gently highlight the reasoning gap and ask them to reflect on that specific step.
6. Acknowledge and reinforce progress before moving to the next concept."""

# ---------------------------------------------------------
# 4. Sidebar Configuration
# ---------------------------------------------------------
with st.sidebar:
    st.header("Configuration")
    
    # If not supplied via CLI or environment, provide a password input box
    if not initial_api_key:
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Enter your Gemini API key or pass it via --api-key when launching the app."
        )
    else:
        api_key = initial_api_key
        st.success("API key loaded from startup configuration.", icon="✅")

    model_name = st.selectbox(
        "Model",
        ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-1.5-flash"],
        index=0
    )

    if st.button("Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Halt execution if no key has been supplied yet
if not api_key:
    st.info("Please provide a Gemini API key via CLI (`-- --api-key <key>`) or enter it in the sidebar to begin.", icon="🔑")
    st.stop()

# ---------------------------------------------------------
# 5. Initialize Gemini Client & Conversation Memory
# ---------------------------------------------------------
client = genai.Client(api_key=api_key.strip())

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render past message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------
# 6. Chat Interaction & Response Streaming
# ---------------------------------------------------------
if prompt := st.chat_input("What problem or concept would you like to explore?"):
    # Record and display the user's message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Format multi-turn conversation history for the Gemini API
    contents = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=m["content"])]
            )
        )

    # Generate and stream the tutor's response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        try:
            response_stream = client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=TUTOR_SYSTEM_INSTRUCTION,
                    temperature=0.7,
                ),
            )
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Error calling Gemini API: {e}")
