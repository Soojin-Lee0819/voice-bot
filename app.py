import streamlit as st
import openai
from elevenlabs import ElevenLabs
from dotenv import load_dotenv
import os
import asyncio
import base64
from kani import Kani
from kani.engines.openai import OpenAIEngine

# Load environment variables
load_dotenv()

# Set your API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
eleven_api_key = os.getenv("ELEVEN_API_KEY")

# Initialize ElevenLabs client
eleven = ElevenLabs(api_key=eleven_api_key)

# Custom voice ID for Angela
ANGELA_VOICE_ID = "ANGELA_VOICE_ID"

# Streamlit UI setup
st.set_page_config(page_title="Chat with Angela", page_icon="💬")
st.markdown("""
    <style>
        .message {
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            max-width: 80%;
        }
        .user-message {
            background-color: #dcf8c6;
            margin-left: auto;
            margin-right: 10px;
            max-width: 80%;
        }
        .bot-message {
            background-color: #ffffff;
            margin-right: auto;
            margin-left: 10px;
            max-width: 80%;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .input-area {
            position: sticky;
            top: 0;
            background-color: #fff;
            padding: 10px 0;
            margin-top: 10px;
        }
        .stApp {
            max-width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

st.title("💬 Chat with Angela (Voice Bot)")
st.markdown("Ask Angela anything below — her replies will be spoken out loud.")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

if "kani" not in st.session_state:
    engine = OpenAIEngine(model="gpt-4o")
    kani = Kani(engine, system_prompt="You are Angela. Respond intelligently, kindly, and clearly in your own voice.")
    st.session_state.kani = kani

if "loop" not in st.session_state:
    st.session_state.loop = asyncio.new_event_loop()

# Create a callback to handle the submission
def handle_submit():
    if st.session_state.user_input.strip():
        # Get user input from session state
        user_message = st.session_state.user_input
        
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_message})
        
        # Clear the input
        st.session_state.user_input = ""
        
        # Process the bot's response
        try:
            loop = st.session_state.loop
            reply = loop.run_until_complete(st.session_state.kani.chat_round(user_message))
            
            # Add the assistant's reply to the conversation history
            st.session_state.chat_history.append({"role": "assistant", "content": str(reply.content)})

            # Generate audio for the bot's reply
            audio_bytes = b"".join(eleven.generate(
                text=str(reply.content),
                voice=ANGELA_VOICE_ID,
                model="eleven_monolingual_v1"
            ))
            
            # Encode audio to base64 for HTML playback
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            st.session_state.current_audio = audio_base64
            
        except Exception as e:
            st.error(f"Error: {e}")

# Create a form for user input at the top
with st.container():
    st.text_input(
        "Type your message here...", 
        key="user_input", 
        placeholder="Ask Angela anything...",
        on_change=handle_submit
    )
    
    # Optional send button
    if st.button("Send"):
        handle_submit()

# Create the chat container for rendering history
chat_container = st.container()

# Render chat history
with chat_container:
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="message user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="message bot-message">{message["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Auto-play audio if available
if "current_audio" in st.session_state:
    audio_html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{st.session_state.current_audio}" type="audio/mp3">
    </audio>
    """
    st.components.v1.html(audio_html, height=0)