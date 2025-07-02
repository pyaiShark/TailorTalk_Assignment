import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Backend URL configuration
BACKEND_URL = os.getenv("BACKEND_URL", "https://tailortalkprivate-production.up.railway.app/chat")

# App setup
st.set_page_config(page_title="TailorTalk", page_icon="📅")
st.title("📅 TailorTalk Appointment Booking")
st.caption("Conversational AI for Appointments booking")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your TailorTalk assistant. How can I help you book an appointment today?"}
    ]
    
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Display's chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Type your message here..."):

    # Adds user messages to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Displays user messages
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.spinner("Thinking..."):
        try:
            response = requests.post(
                BACKEND_URL,
                json={
                    "message": prompt,
                    "session_id": st.session_state.session_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_response = data.get("response", "Sorry, I didn't get that.")
                
                # Update session ID
                if data.get("session_id"):
                    st.session_state.session_id = data["session_id"]
            else:
                assistant_response = f"Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            assistant_response = f"Connection error: {str(e)}"
    
    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(assistant_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
