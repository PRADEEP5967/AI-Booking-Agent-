# 🤖 AI Booking Agent

A modern, intelligent booking agent powered by AI that can handle natural language conversations to schedule meetings and appointments.

## ✨ Features

- **Natural Language Processing**: Understand booking requests in plain English
- **Multi-Provider LLM Support**: OpenAI, Anthropic, and local models
- **Smart Entity Extraction**: Automatically extract dates, times, durations, and purposes
- **Conversation Management**: Intelligent conversation flow with state management
- **Calendar Integration**: Google Calendar integration (with mock mode for testing)
- **Modern Frontend**: Beautiful Streamlit interface with real-time chat
- **Robust Backend**: FastAPI with comprehensive error handling
- **Mock Mode**: Full functionality without API keys for development

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd booking-agent
   ```

2. **Set up environment**
   ```bash
   # Copy environment template
   cp env_template.txt .env
   
   # Edit .env with your configuration
   # For testing without API keys, leave LLM keys empty
   ```

3. **Install dependencies**
   ```bash
   # Backend dependencies
   cd backend
   pip install -r requirements.txt
   
   # Frontend dependencies
   cd ../frontend
   pip install -r requirements.txt
   ```

4. **Start the system**
   ```bash
   # From the root directory
   python start_project.py
   ```

## 🎮 Usage

### Without API Keys (Mock Mode)
The system works perfectly without any LLM API keys using the enhanced mock provider:
Assistant • 14:18
I couldn't understand the date. Could you please specify a date? For example: 'tomorrow', 'December 15th', 'next Monday', or '2024-12-15'.
👤
User • 14:18
Can you schedule a meeting for next Monday at 10 AM for 30 minutes?
��
Assistant • 14:18
"response": "Here are the available time slots for June 30, 2025:\n\n1. 09:00 AM\n2. 09:30 AM\n3. 10:00 AM\n4. 10:30 AM\n5. 11:00 AM\n\nWhich time would you prefer?",
"booking_data": {
  "service_type": "meeting",
  "preferred_date": "2025-06-30",
  "preferred_time": "10:00",
  "duration_minutes": 30,
  "scheduled_date": "2025-06-30"
},
"suggested_slots": [...],
"stage": "confirming",
"requires_confirmation": false