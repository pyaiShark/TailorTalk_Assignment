# AI-Powered Appointment Booking System

## Overview
TailorTalk is a conversational AI agent that enables natural language appointment booking via Google Calendar integration. This solution transforms traditional scheduling into an intuitive chat-based experience using state-of-the-art language models and cloud-native architecture.

## Key Features ✨
- 🗣️ **Natural Language Understanding**: Engage in human-like conversations to schedule appointments.
- 📅 **Calendar Intelligence**: Real-time availability checking and smart slot suggestions.
- ⚡ **Contextual Conversations**: Maintains context across multiple interactions.
- 🔒 **Secure Integration**: Service account-based Google Calendar access.
- ☁️ **Cloud-Ready**: Fully containerized and deployable to any cloud platform.
- 🎨 **Responsive UI**: Elegant chat interface powered by Streamlit.

## Features
- Natural language understanding for appointment requests.
- Real-time calendar availability checks.
- Smart time slot suggestions.
- Context-aware conversation handling.
- Secure Google Calendar integration.
- Cloud-native deployment ready.

## Technology Stack
| Component              | Technology                |
|------------------------|---------------------------|
| **Backend Framework**  | FastAPI                   |
| **AI Agent**           | LangChain                 |
| **Language Model**     | Google Gemini             |
| **Frontend**           | Streamlit                 |
| **Calendar Integration**| Google Calendar API      |
| **Deployment**         | Railway/Docker            |

## Getting Started

### Prerequisites
- Python 3.9+
- Google Cloud Platform account
- Google Gemini API key
- Google Service Account credentials

### Installation
```bash
# Clone repository
git clone https://github.com/pyaiShark/TailorTalk_Assignment.git
cd tailortalk

# Setup environment
python3.9 -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt
