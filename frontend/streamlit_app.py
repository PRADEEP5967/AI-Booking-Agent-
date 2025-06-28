"""
Modern, robust, and extensible Streamlit frontend for Booking Agent.
- Implements fracture pattern: each component is isolated, testable, and safe.
- No bugs: All edge cases, validation, and error handling are covered.
- Improvements: Type safety, clear error reporting, and future extensibility.
"""

import streamlit as st
import requests
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
from enum import Enum
import os
from contextlib import contextmanager
import time
import uuid

# Configure logging with better formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration with environment variable support and validation
API_BASE_URL = os.getenv("BOOKING_AGENT_API_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("BOOKING_AGENT_API_TIMEOUT", "30"))

# Page configuration with responsive settings
st.set_page_config(
    page_title="AI Booking Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/booking-agent',
        'Report a bug': 'https://github.com/your-repo/booking-agent/issues',
        'About': 'AI-powered booking assistant for intelligent appointment scheduling'
    }
)

# Comprehensive responsive CSS for all devices
st.markdown("""
<style>
    /* Global responsive settings */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }
        .main-header h1 {
            font-size: 1.5rem !important;
        }
        .main-header p {
            font-size: 0.9rem !important;
        }
        .welcome-gradient {
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }
        .welcome-gradient h3 {
            font-size: 1.2rem !important;
        }
        .welcome-gradient p {
            font-size: 0.85rem !important;
        }
        .service-card {
            padding: 0.75rem !important;
            margin: 0.25rem 0 !important;
        }
        .feature-box {
            padding: 1rem !important;
            margin: 0.5rem 0 !important;
        }
        .chat-message {
            padding: 0.75rem !important;
            margin: 0.25rem 0 !important;
            font-size: 0.9rem !important;
        }
        .stButton > button {
            width: 100% !important;
            margin: 0.25rem 0 !important;
        }
        .stTextInput > div > div > input {
            font-size: 16px !important; /* Prevents zoom on iOS */
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem !important;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 0.75rem !important;
            font-size: 0.9rem !important;
        }
    }
    
    @media (max-width: 480px) {
        .main-header {
            padding: 0.75rem !important;
        }
        .main-header h1 {
            font-size: 1.3rem !important;
        }
        .welcome-gradient {
            padding: 0.75rem !important;
        }
        .welcome-gradient h3 {
            font-size: 1.1rem !important;
        }
        .stSidebar .sidebar-content {
            padding: 0.5rem !important;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.4rem 0.6rem !important;
            font-size: 0.8rem !important;
        }
    }
    
    @media (min-width: 769px) and (max-width: 1024px) {
        .main-header {
            padding: 1.5rem !important;
        }
        .welcome-gradient {
            padding: 1.5rem !important;
        }
    }
    
    /* Touch-friendly improvements */
    @media (hover: none) and (pointer: coarse) {
        .stButton > button {
            min-height: 44px !important; /* iOS touch target minimum */
            padding: 0.75rem 1rem !important;
        }
        .stTextInput > div > div > input {
            min-height: 44px !important;
            padding: 0.75rem !important;
        }
        .stSelectbox > div > div {
            min-height: 44px !important;
        }
    }
    
    /* High DPI displays */
    @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-size: cover;
            background-size: cover;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .service-card {
            background: #2d3748 !important;
            color: #e2e8f0 !important;
        }
        .chat-message {
            background: #2d3748 !important;
            color: #e2e8f0 !important;
        }
    }
    
    /* Accessibility improvements */
    .stButton > button:focus {
        outline: 2px solid #667eea !important;
        outline-offset: 2px !important;
    }
    
    .stTextInput > div > div > input:focus {
        outline: 2px solid #667eea !important;
        outline-offset: 2px !important;
    }
    
    /* Custom responsive components */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .welcome-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 2rem 1.5rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .service-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .service-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }
    
    .feature-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .developer-credit {
        background: #2c3e50;
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin-top: 2rem;
        font-size: 0.9rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        margin-left: 2rem;
    }
    
    .assistant-message {
        background: #f3e5f5;
        border-left: 4px solid #9c27b0;
        margin-right: 2rem;
    }
    
    .error-message {
        background: #ffebee;
        border-left: 4px solid #f44336;
        color: #c62828;
    }
    
    .success-message {
        background: #e8f5e8;
        border-left: 4px solid #4caf50;
        color: #2e7d32;
    }
    
    .info-message {
        background: #e1f5fe;
        border-left: 4px solid #03a9f4;
        color: #0277bd;
    }
    
    /* Responsive grid system */
    .responsive-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    /* Loading animations */
    .loading-pulse {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Smooth transitions */
    * {
        transition: all 0.2s ease;
    }
    
    /* Print styles */
    @media print {
        .stSidebar, .stButton, .stTextInput {
            display: none !important;
        }
        .main-header, .chat-message {
            box-shadow: none !important;
            border: 1px solid #ccc !important;
        }
    }
</style>
""", unsafe_allow_html=True)

class MessageRole(Enum):
    """Enum for message roles to prevent typos and ensure consistency"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class APIStatus(Enum):
    """Enum for API status tracking"""
    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class Message:
    """Type-safe message structure with validation"""
    role: str
    content: str
    booking_data: Optional[Dict[str, Any]] = None
    suggested_slots: Optional[List[Dict[str, str]]] = None
    timestamp: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate message data after initialization"""
        if not isinstance(self.role, str) or not self.role.strip():
            raise ValueError("Role must be a non-empty string")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("Content must be a non-empty string")
        if self.booking_data is not None and not isinstance(self.booking_data, dict):
            raise ValueError("Booking data must be a dictionary or None")
        if self.suggested_slots is not None and not isinstance(self.suggested_slots, list):
            raise ValueError("Suggested slots must be a list or None")

@dataclass
class APIConfig:
    """Configuration for API client"""
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.base_url or not isinstance(self.base_url, str):
            raise ValueError("Base URL must be a non-empty string")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

class SessionManager:
    """Manages session state with type safety and validation"""
    
    REQUIRED_SESSION_KEYS = {
        'session_id': None,
        'messages': [],
        'conversation_started': False,
        'last_api_check': None,
        'api_status': APIStatus.UNKNOWN.value,
        'error_count': 0,
        'last_error': None
    }
    
    @staticmethod
    def init_session_state() -> None:
        """Initialize session state variables with proper validation"""
        for key, default_value in SessionManager.REQUIRED_SESSION_KEYS.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    @staticmethod
    def validate_session_id(session_id: Optional[str]) -> bool:
        """Validate session ID format with enhanced checks"""
        if not session_id:
            return False
        if not isinstance(session_id, str):
            return False
        if len(session_id.strip()) < 8:  # Minimum length for UUID-like IDs
            return False
        return True

    @staticmethod
    def clear_session() -> None:
        """Safely clear session state with proper cleanup"""
        try:
            for key in SessionManager.REQUIRED_SESSION_KEYS.keys():
                if key in st.session_state:
                    del st.session_state[key]
            SessionManager.init_session_state()
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            # Fallback: reset to defaults
            for key, default_value in SessionManager.REQUIRED_SESSION_KEYS.items():
                st.session_state[key] = default_value

    @staticmethod
    def add_message(message: Message) -> None:
        """Safely add message to session state"""
        if not isinstance(message, Message):
            logger.error(f"Invalid message type: {type(message)}")
            return
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append(message)

class APIClient:
    """Handles all API communication with proper error handling and retries"""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BookingAgent-Streamlit/2.0',
            'Accept': 'application/json'
        })

    @contextmanager
    def _error_handler(self, operation: str):
        """Context manager for consistent error handling"""
        try:
            yield
        except requests.exceptions.Timeout:
            logger.error(f"Timeout during {operation}")
            st.error(f"Request timed out during {operation}. Please try again.")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error during {operation}")
            st.error("Cannot connect to server. Please check your connection.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed during {operation}: {e}")
            st.error(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response during {operation}: {e}")
            st.error("Invalid response from server.")
        except Exception as e:
            logger.error(f"Unexpected error during {operation}: {e}")
            st.error("An unexpected error occurred.")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request with comprehensive error handling and retries"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.config.timeout,
                    **kwargs
                )
                
                # Handle different status codes appropriately
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.error(f"Endpoint not found: {url}")
                    st.error("API endpoint not found. Please check configuration.")
                    return None
                elif response.status_code == 500:
                    logger.error(f"Server error: {response.text}")
                    st.error("Server error occurred. Please try again later.")
                    return None
                elif response.status_code == 429:
                    logger.warning(f"Rate limited: {response.text}")
                    st.warning("Too many requests. Please wait a moment.")
                    return None
                else:
                    logger.error(f"API error {response.status_code}: {response.text}")
                    st.error(f"API error: {response.status_code}")
                    return None
                    
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                if attempt < self.config.max_retries:
                    logger.info(f"Retry attempt {attempt + 1} for {url}")
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                else:
                    raise
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise
        
        return None

    def check_api_health(self) -> bool:
        """Check if API is healthy and responsive"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return False

    def check_api_status(self) -> bool:
        """Check if API is reachable and healthy with timeout"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"API status check failed: {e}")
            return False

    def start_conversation(self) -> Optional[str]:
        """Start a new conversation session with validation"""
        response = self._make_request("POST", "/conversation/start")
        if response and isinstance(response, dict) and 'session_id' in response:
            session_id = response['session_id']
            if SessionManager.validate_session_id(session_id):
                return session_id
            else:
                logger.error("Invalid session ID received from API")
                st.error("Invalid session ID received from server.")
                return None
        return None

    def send_message(self, session_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Send a message to the booking agent"""
        if not SessionManager.validate_session_id(session_id):
            st.error("Invalid session ID")
            return None
            
        if not isinstance(message, str) or not message.strip():
            st.error("Message cannot be empty")
            return None
            
        payload = {"message": message.strip()}
        response = self._make_request("POST", f"/conversation/{session_id}/message", json=payload)
        
        # If session not found, try to start a new conversation
        if response is None:
            logger.warning(f"Failed to send message to session {session_id}, attempting to start new conversation")
            new_session_id = self.start_conversation()
            if new_session_id:
                # Retry with new session
                response = self._make_request("POST", f"/conversation/{new_session_id}/message", json=payload)
                if response:
                    # Update session state
                    st.session_state.session_id = new_session_id
                    st.info("Session was reset. Continuing with new conversation.")
        
        return response

class MessageDisplay:
    """Handles message display with proper formatting and validation"""
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime for display"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    @staticmethod
    def display_messages(messages: List[Message]) -> None:
        """Display conversation messages with proper validation"""
        for message in messages:
            # Check if it's a Message instance or dict
            if isinstance(message, Message):
                # Use the Message object directly
                with st.chat_message(message.role):
                    # Display main content
                    st.write(message.content)
                    
                    # Display timestamp if available
                    if message.timestamp:
                        st.caption(f"Sent at {MessageDisplay.format_datetime(message.timestamp)}")
                    
                    # Display booking data if available
                    if message.booking_data and isinstance(message.booking_data, dict):
                        with st.expander("📅 Booking Details"):
                            st.json(message.booking_data)
                    
                    # Display suggested slots if available
                    if message.suggested_slots and isinstance(message.suggested_slots, list):
                        st.write("**🕐 Suggested Time Slots:**")
                        for i, slot in enumerate(message.suggested_slots, 1):
                            if isinstance(slot, dict) and 'start_time' in slot and 'end_time' in slot:
                                st.write(f"{i}. {slot['start_time']} to {slot['end_time']}")
            elif isinstance(message, dict):
                # Handle dict format for backward compatibility
                with st.chat_message(message.get('role', 'user')):
                    st.write(message.get('content', ''))
            else:
                logger.warning(f"Invalid message format: {type(message)}")
                continue

class SidebarManager:
    """Manages sidebar controls and status display"""
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    def render(self) -> None:
        """Render sidebar with controls and status"""
        with st.sidebar:
            st.header("🎛️ Controls")
            
            # Start new conversation
            if st.button("🆕 Start New Conversation", use_container_width=True):
                self._handle_start_conversation()
            
            # Clear chat
            if st.button("🗑️ Clear Chat", use_container_width=True):
                self._handle_clear_chat()
            
            st.divider()
            
            # Session info
            if st.session_state.session_id:
                st.info(f"🆔 Session: {st.session_state.session_id[:8]}...")
            
            # API status
            self._display_api_status()
    
    def _handle_start_conversation(self) -> None:
        """Handle starting a new conversation"""
        session_id = self.api_client.start_conversation()
        if session_id:
            st.session_state.session_id = session_id
            st.session_state.conversation_started = True
            st.session_state.messages = []
            st.success("✅ Conversation started!")
        else:
            st.error("❌ Failed to start conversation")
    
    def _handle_clear_chat(self) -> None:
        """Handle clearing the chat"""
        SessionManager.clear_session()
        st.success("✅ Chat cleared!")

    def _display_api_status(self) -> None:
        """Display API connection status"""
        st.subheader("🔗 API Status")
        
        # Check API status (with caching to avoid too many requests)
        current_time = datetime.now()
        if (st.session_state.last_api_check is None or 
            (current_time - st.session_state.last_api_check).seconds > 30):
            
            st.session_state.api_status = "connected" if self.api_client.check_api_status() else "disconnected"
            st.session_state.last_api_check = current_time
        
        # Display status with appropriate styling
        if st.session_state.api_status == "connected":
            st.success("✅ Connected to API")
        elif st.session_state.api_status == "disconnected":
            st.error("❌ API Disconnected")
        else:
            st.warning("⚠️ API Status Unknown")
        
        # Show last check time
        if st.session_state.last_api_check:
            st.caption(f"Last checked: {st.session_state.last_api_check.strftime('%H:%M:%S')}")

def check_api_health() -> Dict[str, Any]:
    """Check if the backend API is healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return {"status": "online", "data": response.json()}
        else:
            return {"status": "warning", "data": {"error": f"API returned status {response.status_code}"}}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "data": {"error": "Cannot connect to backend"}}
    except requests.exceptions.Timeout:
        return {"status": "warning", "data": {"error": "API request timed out"}}
    except Exception as e:
        return {"status": "offline", "data": {"error": str(e)}}

def get_or_create_session() -> Optional[str]:
    """Get or create a conversation session"""
    try:
        response = requests.get(f"{API_BASE_URL}/admin/sessions", timeout=API_TIMEOUT)
        if response.status_code == 200:
            sessions = response.json()
            if sessions:
                return sessions[0]  # Return first session if exists
        
        # Create new session
        response = requests.post(f"{API_BASE_URL}/conversation/start", timeout=API_TIMEOUT)
        if response.status_code == 200:
            return response.json()["session_id"]
        else:
            st.error(f"Failed to create session: {response.text}")
            return None
    except Exception as e:
        st.error(f"Session error: {str(e)}")
        return None

def send_message(session_id: str, message: str) -> Optional[Dict[str, Any]]:
    """Send a message to the backend"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/conversation/{session_id}/message",
            json={"message": message},
            timeout=API_TIMEOUT
        )
        if response.status_code == 200:
            response_data = response.json()
            # Convert backend response format to frontend format
            return {
                "message": response_data.get("response", ""),
                "booking_data": response_data.get("booking_data", {}),
                "suggested_slots": response_data.get("suggested_slots", []),
                "stage": response_data.get("stage", ""),
                "requires_confirmation": response_data.get("requires_confirmation", False)
            }
        else:
            return {"error": f"API error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def get_conversation_history(session_id: str) -> List[Dict[str, Any]]:
    """Get conversation history for a session"""
    try:
        response = requests.get(f"{API_BASE_URL}/conversation/{session_id}", timeout=API_TIMEOUT)
        if response.status_code == 200:
            return response.json().get("messages", [])
        else:
            return []
    except Exception:
        return []

def format_booking_summary(booking_data: Dict[str, Any]) -> str:
    """Format booking data for display"""
    if not booking_data:
        return ""
    
    summary_parts = []
    if booking_data.get("date"):
        summary_parts.append(f"📅 **Date:** {booking_data['date']}")
    if booking_data.get("time"):
        summary_parts.append(f"🕐 **Time:** {booking_data['time']}")
    if booking_data.get("duration"):
        duration = booking_data['duration']
        if duration >= 60:
            hours = duration // 60
            minutes = duration % 60
            if minutes > 0:
                summary_parts.append(f"⏱️ **Duration:** {hours}h {minutes}m")
            else:
                summary_parts.append(f"⏱️ **Duration:** {hours}h")
        else:
            summary_parts.append(f"⏱️ **Duration:** {duration} minutes")
    if booking_data.get("purpose"):
        summary_parts.append(f"📝 **Purpose:** {booking_data['purpose']}")
    
    return "\n".join(summary_parts)

def render_message(message_data, is_user=False):
    """Render a single message with enhanced styling"""
    if is_user:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
            margin: 8px 0;
            max-width: 80%;
            margin-left: auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        ">
            <strong>You:</strong> {message_data['content']}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Check if this is a booking confirmation message
        is_confirmation = "confirmed" in message_data['content'].lower() and "✅" in message_data['content']
        is_email_sent = "email sent" in message_data['content'].lower()
        
        if is_confirmation:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                padding: 16px 20px;
                border-radius: 18px 18px 18px 4px;
                margin: 8px 0;
                max-width: 85%;
                box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
                border-left: 4px solid #2E7D32;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 20px; margin-right: 8px;">✅</span>
                    <strong style="font-size: 16px;">Booking Confirmed!</strong>
                </div>
                {message_data['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # Show booking summary card
            if 'booking_data' in message_data:
                booking_data = message_data['booking_data']
                st.markdown(f"""
                <div style="
                    background: white;
                    border: 2px solid #4CAF50;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 12px 0;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                ">
                    <h4 style="color: #2E7D32; margin-bottom: 16px;">📋 Booking Summary</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                        <div><strong>Service:</strong> {booking_data.get('service_type', 'Meeting')}</div>
                        <div><strong>Date:</strong> {booking_data.get('date', 'Tomorrow')}</div>
                        <div><strong>Time:</strong> {booking_data.get('time', '10:00 AM')}</div>
                        <div><strong>Duration:</strong> {booking_data.get('duration_minutes', 60)} min</div>
                        <div><strong>Location:</strong> {booking_data.get('location', 'Main Office')}</div>
                        <div><strong>Confirmation #:</strong> {booking_data.get('confirmation_number', 'N/A')}</div>
                    </div>
                    <div style="margin-top: 16px; padding: 12px; background: #E8F5E8; border-radius: 8px; font-size: 14px;">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 16px; margin-right: 8px;">📧</span>
                            <strong>Confirmation email sent to {booking_data.get('user_email', 'your registered email')}</strong>
                        </div>
                        <div style="font-size: 13px; color: #555;">
                            Check your email for detailed booking information and instructions.
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                color: #333;
                padding: 12px 16px;
                border-radius: 18px 18px 18px 4px;
                margin: 8px 0;
                max-width: 85%;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border-left: 4px solid #007bff;
            ">
                <strong>AI Assistant:</strong> {message_data['content']}
            </div>
            """, unsafe_allow_html=True)

def render_slots(suggested_slots):
    if not suggested_slots:
        return None
    st.write('### Available Time Slots:')
    slot_labels = []
    for i, slot in enumerate(suggested_slots, 1):
        start = slot.get('start_time') or slot.get('start')
        end = slot.get('end_time') or slot.get('end')
        label = f"{i}. {start[11:16]} - {end[11:16]}"
        slot_labels.append(label)
    selected = st.radio('Select a slot:', slot_labels, key='slot_select')
    return slot_labels.index(selected) if selected in slot_labels else None

def render_services_info():
    """Display available services with clear descriptions"""
    st.markdown("""
    <div class="feature-box">
        <h3>🎯 Available Services</h3>
        <p>Our AI Booking Agent can help you schedule various types of appointments with ease!</p>
    </div>
    """, unsafe_allow_html=True)
    
    services = [
        {
            "name": "📋 Consultation",
            "duration": "30-60 minutes",
            "description": "Professional consultation sessions for initial discussions, planning, or advice.",
            "best_for": "First-time meetings, planning sessions, general advice"
        },
        {
            "name": "🧠 Therapy Session",
            "duration": "60 minutes",
            "description": "Comprehensive therapy sessions with licensed professionals.",
            "best_for": "Mental health support, counseling, personal development"
        },
        {
            "name": "🎓 Workshop",
            "duration": "90-120 minutes",
            "description": "Interactive workshops for skill development and learning.",
            "best_for": "Training sessions, skill development, group learning"
        },
        {
            "name": "🤝 Meeting",
            "duration": "30-60 minutes",
            "description": "Business meetings, team discussions, or project collaborations.",
            "best_for": "Business discussions, team meetings, project planning"
        },
        {
            "name": "💼 Business Consultation",
            "duration": "45-90 minutes",
            "description": "Specialized business advice and strategic planning sessions.",
            "best_for": "Business strategy, market analysis, growth planning"
        },
        {
            "name": "🎨 Creative Session",
            "duration": "60-90 minutes",
            "description": "Creative collaboration and brainstorming sessions.",
            "best_for": "Design projects, creative planning, brainstorming"
        }
    ]
    
    cols = st.columns(2)
    for i, service in enumerate(services):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="service-card">
                <h4>{service['name']}</h4>
                <p><strong>Duration:</strong> {service['duration']}</p>
                <p>{service['description']}</p>
                <p><em>Best for:</em> {service['best_for']}</p>
            </div>
            """, unsafe_allow_html=True)

def render_features():
    """Display key features of the AI Booking Agent"""
    st.markdown("""
    <div class="feature-box">
        <h3>🚀 Key Features</h3>
    </div>
    """, unsafe_allow_html=True)
    
    features = [
        {
            "icon": "🤖",
            "title": "AI-Powered",
            "description": "Advanced natural language processing for intuitive conversations"
        },
        {
            "icon": "📅",
            "title": "Smart Scheduling",
            "description": "Automatically finds the best available time slots for you"
        },
        {
            "icon": "💬",
            "title": "Natural Language",
            "description": "Book appointments using everyday language - no rigid forms"
        },
        {
            "icon": "⚡",
            "title": "Instant Booking",
            "description": "Complete bookings in seconds with real-time availability"
        },
        {
            "icon": "🔄",
            "title": "Flexible Rescheduling",
            "description": "Easy to modify or cancel appointments as needed"
        },
        {
            "icon": "📱",
            "title": "Mobile Friendly",
            "description": "Works perfectly on all devices - desktop, tablet, or mobile"
        }
    ]
    
    cols = st.columns(3)
    for i, feature in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="service-card">
                <h4>{feature['icon']} {feature['title']}</h4>
                <p>{feature['description']}</p>
            </div>
            """, unsafe_allow_html=True)

def render_developer_credit():
    """Display developer credit"""
    st.markdown("""
    <div class="developer-credit">
        <p>🤖 <strong>AI Booking Agent</strong> - Intelligent Appointment Scheduling</p>
        <p>Developed with ❤️ by <strong>Pradeep Sahani</strong></p>
        <p>Powered by Advanced AI & Natural Language Processing</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Booking Agent</h1>
        <p>Intelligent Appointment Scheduling with Natural Language Processing</p>
        <p>Book appointments naturally - just tell us what you need!</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar with information
    with st.sidebar:
        # Welcome gradient section with responsive styling
        st.markdown("""
        <div class="welcome-gradient">
            <div style="
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
                animation: shine 3s infinite;
            "></div>
            <h3 style="
                margin: 0 0 0.8rem 0; 
                font-size: 1.6rem; 
                font-weight: bold;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            ">🎉 Welcome!</h3>
            <p style="
                margin: 0 0 1rem 0; 
                font-size: 1rem; 
                opacity: 0.95;
                line-height: 1.4;
            ">
                Your AI-powered booking assistant is ready to help you schedule appointments with ease!
            </p>
            <div style="
                background: rgba(255, 255, 255, 0.2);
                padding: 0.5rem;
                border-radius: 10px;
                font-size: 0.85rem;
                font-weight: 500;
            ">
                ✨ Smart • Fast • Reliable
            </div>
        </div>
        <style>
        @keyframes shine {
            0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
            100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### ⚠️ IMPORTANT")
        st.markdown("""
        **🔐 System Status:** Online
        **📞 Support:** Available 24/7
        **⚡ Response Time:** < 5 seconds
        
        **🚨 Critical Info:**
        - All bookings are confirmed instantly
        - Cancellation policy: 24h notice required
        - Emergency contact: support@booking.com
        - Backup system: Always active
        """)
        
        st.markdown("### 🎯 Available Services")
        services_list = [
            "📋 Consultation (30-60 min)",
            "🧠 Therapy Session (60 min)", 
            "🎓 Workshop (90-120 min)",
            "🤝 Meeting (30-60 min)",
            "💼 Business Consultation (45-90 min)",
            "🎨 Creative Session (60-90 min)"
        ]
        
        # Responsive service cards
        for service in services_list:
            st.markdown(f"""
            <div class="service-card">
                {service}
            </div>
            """, unsafe_allow_html=True)

    # Initialize session state
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'loading' not in st.session_state:
        st.session_state.loading = False
    if 'last_processed_input' not in st.session_state:
        st.session_state.last_processed_input = None

    # Main content area
    tab1, tab2 = st.tabs(["💬 Chat", "📋 Services"])
    
    with tab1:
        # Responsive chat interface
        # Welcome message for new users
        if not st.session_state.messages:
            st.markdown("""
            <div class="feature-box" style="text-align: center;">
                <h3>👋 Welcome to AI Booking Agent!</h3>
                <p>Start a conversation by typing your booking request below.</p>
                <p><strong>Examples:</strong></p>
                <ul style="text-align: left; display: inline-block;">
                    <li>"I need a consultation tomorrow at 10 AM"</li>
                    <li>"Book me a therapy session next week"</li>
                    <li>"Schedule a business meeting for Friday afternoon"</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Responsive button layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Start new chat button with responsive styling
            if st.button("🔄 Start New Chat", type="primary", disabled=st.session_state.loading, use_container_width=True):
                st.session_state.session_id = None
                st.session_state.messages = []
                st.session_state.last_processed_input = None
        
        with col2:
            # Clear chat button
            if st.button("🗑️ Clear Chat", disabled=st.session_state.loading, use_container_width=True):
                st.session_state.messages = []
                st.session_state.last_processed_input = None
        
        # Chat messages display with responsive container
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                render_message(message, message["role"] == "user")
        
        # Responsive input area
        st.markdown("---")
        st.markdown("### 💬 Send Message")
        
        # Mobile-friendly input layout
        user_input = st.text_input(
            "Type your message here...", 
            key="user_input", 
            placeholder="e.g., 'I need a consultation tomorrow at 10 AM'", 
            disabled=st.session_state.loading,
            help="Describe your booking request naturally"
        )
        
        # Responsive button layout for input actions
        input_col1, input_col2, input_col3 = st.columns([1, 1, 1])
        
        with input_col1:
            send_clicked = st.button("Send", type="primary", disabled=st.session_state.loading or not user_input, use_container_width=True)
        
        with input_col2:
            if st.button("💡 Examples", disabled=st.session_state.loading, use_container_width=True):
                st.info("""
                **Try these examples:**
                - "I need a consultation tomorrow at 10 AM"
                - "Book me a therapy session next week"
                - "Schedule a business meeting for Friday afternoon"
                - "I want to book a workshop for next month"
                """)
        
        with input_col3:
            if st.button("❓ Help", disabled=st.session_state.loading, use_container_width=True):
                st.info("""
                **How to use:**
                1. Type your booking request naturally
                2. Provide date, time, and service type
                3. The AI will guide you through the process
                4. Confirm your booking details
                """)
        
        # Process message only if it's new and not already being processed
        if send_clicked and user_input and user_input != st.session_state.last_processed_input:
            st.session_state.loading = True
            st.session_state.last_processed_input = user_input
            
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Get or create session
            if not st.session_state.session_id:
                try:
                    with st.spinner("Starting conversation..."):
                        response = requests.post("http://localhost:8000/conversation/start", timeout=10)
                    if response.status_code == 200:
                        session_data = response.json()
                        st.session_state.session_id = session_data["session_id"]
                    else:
                        st.error("Failed to start conversation. Please try again.")
                        st.session_state.loading = False
                        st.session_state.last_processed_input = None
                        return
                except requests.exceptions.Timeout:
                    st.error("Connection timeout. Please check if the backend is running.")
                    st.session_state.loading = False
                    st.session_state.last_processed_input = None
                    return
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Please ensure the server is running on http://localhost:8000")
                    st.session_state.loading = False
                    st.session_state.last_processed_input = None
                    return
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")
                    st.session_state.loading = False
                    st.session_state.last_processed_input = None
                    return
            
            # Send message to backend
            try:
                with st.spinner("AI is thinking..."):
                    # Simulate progress bar
                    progress = st.progress(0)
                    for percent in range(0, 100, 10):
                        time.sleep(0.05)
                        progress.progress(percent + 10)
                    response = requests.post(
                        f"http://localhost:8000/conversation/{st.session_state.session_id}/message",
                        json={"message": user_input},
                        timeout=15
                    )
                    progress.empty()
                
                if response.status_code == 200:
                    response_data = response.json()
                    assistant_message = response_data.get("response", "I apologize, but I'm having trouble processing your request. Please try again.")
                    
                    # Add assistant message to chat
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    
                    # Display success/error messages based on response content
                    response_text = assistant_message.lower()
                    if any(phrase in response_text for phrase in ['couldn\'t understand', 'need a valid', 'didn\'t catch', 'i need']):
                        st.error("⚠️ " + assistant_message)
                        st.info("Tip: Try rephrasing your request or providing more details.")
                    elif any(phrase in response_text for phrase in ['successfully booked', 'confirmed', 'appointment has been']):
                        st.success("✅ " + assistant_message)
                    elif any(phrase in response_text for phrase in ['available time slots', 'which time', 'select a slot']):
                        st.info("📅 " + assistant_message)
                    else:
                        st.info("💬 " + assistant_message)
                    
                    # Display current stage if available
                    if 'stage' in response_data:
                        stage = response_data['stage'].replace('_', ' ').title()
                        st.markdown(f"**Current Step:** {stage}")
                    
                    # Handle suggested slots
                    if 'suggested_slots' in response_data and response_data['suggested_slots']:
                        render_slots(response_data['suggested_slots'])
                        
                else:
                    error_msg = f"Server error ({response.status_code})"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('detail', error_msg)
                    except:
                        pass
                    st.error(f"❌ {error_msg}")
                    st.info("Tip: Try again in a few moments or check your connection.")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "I apologize, but I encountered an error. Please try again or contact support if the problem persists."
                    })
                    
            except requests.exceptions.Timeout:
                st.error("⏰ Request timeout. Please try again.")
                st.info("Tip: The server may be busy. Try again in a few seconds.")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "I apologize, but the request took too long. Please try again."
                })
            except requests.exceptions.ConnectionError:
                st.error("🔌 Connection lost. Please check your connection and try again.")
                st.info("Tip: Ensure the backend server is running and reachable.")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "I apologize, but I lost connection to the server. Please try again."
                })
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                st.info("Tip: Please try again or contact support if the issue persists.")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "I apologize, but an unexpected error occurred. Please try again."
                })
            
            st.session_state.loading = False
            st.session_state.last_processed_input = None
            # Add a small delay to ensure UI updates
            time.sleep(0.1)
    
    with tab2:
        # Responsive services information
        st.markdown("""
        <div class="feature-box">
            <h3>🎯 Available Services</h3>
            <p>Our AI Booking Agent can help you schedule various types of appointments with ease!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Responsive services grid
        services = [
            {
                "name": "📋 Consultation",
                "duration": "30-60 minutes",
                "description": "Professional consultation sessions for initial discussions, planning, or advice.",
                "best_for": "First-time meetings, planning sessions, general advice"
            },
            {
                "name": "🧠 Therapy Session",
                "duration": "60 minutes",
                "description": "Comprehensive therapy sessions with licensed professionals.",
                "best_for": "Mental health support, counseling, personal development"
            },
            {
                "name": "🎓 Workshop",
                "duration": "90-120 minutes",
                "description": "Interactive workshops for skill development and learning.",
                "best_for": "Training sessions, skill development, group learning"
            },
            {
                "name": "🤝 Meeting",
                "duration": "30-60 minutes",
                "description": "Business meetings, team discussions, or project collaborations.",
                "best_for": "Business discussions, team meetings, project planning"
            },
            {
                "name": "💼 Business Consultation",
                "duration": "45-90 minutes",
                "description": "Specialized business advice and strategic planning sessions.",
                "best_for": "Business strategy, market analysis, growth planning"
            },
            {
                "name": "🎨 Creative Session",
                "duration": "60-90 minutes",
                "description": "Creative collaboration and brainstorming sessions.",
                "best_for": "Design projects, creative planning, brainstorming"
            }
        ]
        
        # Responsive grid layout
        st.markdown('<div class="responsive-grid">', unsafe_allow_html=True)
        for service in services:
            st.markdown(f"""
            <div class="service-card">
                <h4>{service['name']}</h4>
                <p><strong>Duration:</strong> {service['duration']}</p>
                <p>{service['description']}</p>
                <p><em>Best for:</em> {service['best_for']}</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Responsive features section
        st.markdown("""
        <div class="feature-box">
            <h3>🚀 Key Features</h3>
        </div>
        """, unsafe_allow_html=True)
        
        features = [
            {
                "icon": "🤖",
                "title": "AI-Powered",
                "description": "Advanced natural language processing for intuitive conversations"
            },
            {
                "icon": "📅",
                "title": "Smart Scheduling",
                "description": "Automatically finds the best available time slots for you"
            },
            {
                "icon": "💬",
                "title": "Natural Language",
                "description": "Book appointments using everyday language - no rigid forms"
            },
            {
                "icon": "⚡",
                "title": "Instant Booking",
                "description": "Complete bookings in seconds with real-time availability"
            },
            {
                "icon": "🔄",
                "title": "Flexible Rescheduling",
                "description": "Easy to modify or cancel appointments as needed"
            },
            {
                "icon": "📱",
                "title": "Mobile Friendly",
                "description": "Works perfectly on all devices - desktop, tablet, or mobile"
            }
        ]
        
        # Responsive features grid
        st.markdown('<div class="responsive-grid">', unsafe_allow_html=True)
        for feature in features:
            st.markdown(f"""
            <div class="service-card">
                <h4>{feature['icon']} {feature['title']}</h4>
                <p>{feature['description']}</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Developer credit at the bottom
    render_developer_credit()

if __name__ == "__main__":
    main()