import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Project Baseline", page_icon="🤖")

st.title("🤖 Project Baseline")

if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

api_key = st.sidebar.text_input("Enter your Groq API Key:", type="password", value=st.session_state.groq_api_key)

model_options = {
    "Llama 3.1 8B (Fast & Free)": "llama-3.1-8b-instant",
    "Groq Compound (Tools)": "groq-compound",
    "Llama 3.3 70B": "llama-3.3-70b-versatile"
}

selected_model = st.sidebar.selectbox(
    "Choose Model:",
    options=list(model_options.keys()),
    index=0
)

if api_key:
    st.session_state.groq_api_key = api_key
    client = Groq(api_key=api_key)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = client.chat.completions.create(
                    model=model_options[selected_model],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    max_tokens=1024,
                    temperature=0.7,
                )
                
                assistant_response = response.choices[0].message.content
                st.markdown(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
else:
    st.info("Please enter your Groq API key in the sidebar to start chatting.")

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()