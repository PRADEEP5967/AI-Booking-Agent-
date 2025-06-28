import streamlit as st
import requests

st.title("AI Booking Agent")

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

user_input = st.text_input("You:")
if st.button("Send") and user_input:
    st.session_state['messages'].append(("user", user_input))
    response = requests.post(
        "http://localhost:8000/chat",
        json={"message": user_input}
    )
    agent_reply = response.json().get("response", "[No response]")
    st.session_state['messages'].append(("agent", agent_reply))

for sender, msg in st.session_state['messages']:
    st.write(f"**{sender.capitalize()}:** {msg}") 