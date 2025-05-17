import streamlit as st
from dotenv import load_dotenv
from server import get_response

load_dotenv()

st.title(":brain: Chatbot")

if "chat_history" not in st.session_state:
    st.session_state['chat_history'] = []

with st.form("llm-form"):
    text = st.text_area("Enter your question here.")
    submit = st.form_submit_button("Submit")

if submit and text:
    with st.spinner("Generating response..."):
        response = get_response(text)
        st.session_state['chat_history'].append({
            'user': text,
            'assistant': response
        })

st.write('## Chat History')
for chat in reversed(st.session_state['chat_history']):
    st.write(f"**🧑 User**: {chat['user']}")
    st.write(f"**🧠 Assistant**: {chat['assistant']}")
    st.write("---")
