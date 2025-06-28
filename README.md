# 🤖 AI Booking Agent

A sophisticated AI-powered booking assistant with enhanced conversation capabilities, intelligent entity extraction, and robust error handling. Works seamlessly with or without real LLM API keys.

## ✨ Key Features

### 🧠 Enhanced AI Capabilities
- **Multi-Provider LLM Support**: OpenAI, Anthropic, and local/mock providers
- **Intelligent Entity Extraction**: Advanced regex-based parsing for dates, times, durations, and purposes
- **Smart Conversation Flow**: Context-aware booking workflows with automatic stage transitions
- **Confirmation Detection**: Natural language understanding for yes/no responses

### 🔧 Robust Architecture
- **Mock Provider Fallback**: Full functionality without API keys for development and testing
- **Session Persistence**: Automatic conversation state management across restarts
- **Error Recovery**: Graceful handling of API failures and invalid inputs
- **Caching System**: Performance optimization with intelligent response caching

### 🎯 Booking Intelligence
- **Natural Language Processing**: Understands various date/time formats
- **Smart Validation**: Automatic data cleaning and format standardization
- **Progressive Information Gathering**: Guides users through missing booking details
- **Booking Summaries**: Clear, formatted display of meeting information

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI
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
   cd booking-agent/backend
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

```bash
# Start with mock mode
python start_project.py
```

**Features available in mock mode:**
- ✅ Complete booking conversation flow
- ✅ Entity extraction from natural language
- ✅ Date/time parsing (tomorrow, next Monday, 2:30 PM, etc.)
- ✅ Duration parsing (1 hour, 30 minutes, etc.)
- ✅ Purpose extraction
- ✅ Confirmation detection
- ✅ Booking validation and formatting

### With Real LLM API Keys
For production use with real AI models:

1. **Set your API keys in `.env`:**
   ```env
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

2. **Start the system:**
   ```bash
   python start_project.py
   ```

## 🧪 Testing

### Comprehensive Test Suite
Run the enhanced test suite to verify all features:

```bash
cd booking-agent/backend
python test_llm_services.py
```

**Test Coverage:**
- ✅ Mock provider entity extraction
- ✅ LLM service generation
- ✅ Agent conversation flow
- ✅ Booking entity validation
- ✅ Confirmation logic
- ✅ Error handling and recovery

### Manual Testing
1. **Start the system:**
   ```bash
   python start_project.py
   ```

2. **Open the frontend:** http://localhost:8501 (or 8502 if 8501 is busy)

3. **Test conversation flows:**
   ```
   User: "Hello, I'd like to book a meeting"
   Agent: "Great! I'd be happy to help you book a meeting. Could you please provide the date, time, and duration?"
   
   User: "Tomorrow at 2:30 PM for 1 hour"
   Agent: "Perfect! I have all the information. Let me confirm your booking:
          📅 Date: 2024-01-16
          🕐 Time: 14:30
          ⏱️ Duration: 1h
          Is this correct?"
   
   User: "Yes, that's perfect"
   Agent: "🎉 Perfect! Your booking has been confirmed..."
   ```

## 🔧 Configuration

### Environment Variables
```env
# LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
BOOKING_AGENT_LLM_PROVIDER=openai  # openai, anthropic, local
BOOKING_AGENT_LLM_MODEL=gpt-3.5-turbo

# Backend Configuration
BOOKING_AGENT_BACKEND_HOST=0.0.0.0
BOOKING_AGENT_BACKEND_PORT=8000
BOOKING_AGENT_DEBUG=true

# Frontend Configuration
BOOKING_AGENT_FRONTEND_PORT=8501
BOOKING_AGENT_API_URL=http://localhost:8000

# Calendar Integration (Optional)
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials/google_credentials.json
BOOKING_AGENT_MOCK_CALENDAR=true  # Use mock calendar for testing
```

### Mock Mode Benefits
- **No API Costs**: Test and develop without spending money
- **Instant Responses**: No network latency for faster development
- **Predictable Behavior**: Consistent responses for testing
- **Offline Development**: Work without internet connection
- **Learning Tool**: Understand how the system works

## 🏗️ Architecture

### Enhanced LLM Service
```
LLMService
├── Provider Management
│   ├── OpenAI Provider
│   ├── Anthropic Provider
│   └── Mock Provider (Enhanced)
├── Entity Extraction
│   ├── Date/Time Parsing
│   ├── Duration Extraction
│   └── Purpose Detection
├── Caching Layer
└── Error Handling
```

### Intelligent Agent Service
```
AgentService
├── Conversation State Management
├── Stage Transitions
│   ├── Greeting → Collecting Info
│   ├── Collecting Info → Confirming
│   └── Confirming → Completed
├── Entity Validation
├── Confirmation Logic
└── Booking Creation
```

### Robust Frontend
```
Streamlit Frontend
├── Real-time Chat Interface
├── API Health Monitoring
├── Session Management
├── Error Recovery
└── Booking Status Display
```

## 🎯 Advanced Features

### Smart Entity Extraction
The enhanced mock provider can extract booking information from natural language:

**Date Patterns:**
- "tomorrow" → 2024-01-16
- "next Monday" → 2024-01-22
- "2024-01-15" → 2024-01-15
- "1/15/2024" → 2024-01-15

**Time Patterns:**
- "2:30 PM" → 14:30
- "2 PM" → 14:00
- "14:30" → 14:30

**Duration Patterns:**
- "1 hour" → 60 minutes
- "30 minutes" → 30 minutes
- "1 hour 30 minutes" → 90 minutes

**Purpose Extraction:**
- "for project review" → "project review"
- "about budget planning" → "budget planning"

### Intelligent Conversation Flow
The agent automatically manages conversation stages:

1. **Greeting**: Welcomes user and identifies booking intent
2. **Collecting Info**: Extracts and validates booking details
3. **Confirming**: Presents summary and asks for confirmation
4. **Completed**: Creates booking and provides confirmation

### Error Recovery
- **Session Persistence**: Conversations survive backend restarts
- **API Fallbacks**: Automatic fallback to mock provider
- **Input Validation**: Graceful handling of invalid data
- **Network Resilience**: Retry logic for failed requests

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Environment Setup
```bash
# Production environment
export BOOKING_AGENT_ENV=production
export BOOKING_AGENT_DEBUG=false
export BOOKING_AGENT_LLM_PROVIDER=openai
```

### Monitoring
- **Health Checks**: `/health` endpoint for monitoring
- **Admin Endpoints**: `/admin/sessions` for session management
- **Logging**: Comprehensive logging for debugging

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Run tests**: `python test_llm_services.py`
5. **Submit a pull request**

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Check what's using the port
netstat -ano | findstr :8000
# Kill the process or use a different port
```

**API Connection Errors:**
- Check if backend is running: `http://localhost:8000/health`
- Verify environment variables
- Try mock mode for testing

**Session Loss:**
- Sessions are automatically recreated
- Check backend logs for errors
- Verify file permissions for session storage

### Getting Help
- Check the logs in the terminal
- Verify your `.env` configuration
- Test with mock mode first
- Review the test output for clues

---

**🎉 Ready to use!** The AI Booking Agent now provides a complete, production-ready booking experience with or without real LLM API keys.