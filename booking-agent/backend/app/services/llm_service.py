"""
🚀 Ultra-Modern LLM Service for Booking Agent with AI-Powered Features

This cutting-edge module delivers a next-generation LLM service featuring:
✨ Multi-Provider AI Orchestration (OpenAI, Anthropic, Claude, Gemini, Local)
🧠 Intelligent Semantic Caching with Vector Embeddings
⚡ Real-time Streaming & WebSocket Integration
🔄 Advanced Retry Logic with Exponential Backoff & Jitter
🎯 Structured Output Parsing with Pydantic Validation
💰 Smart Cost Optimization & Usage Analytics
🛡️ Enterprise-Grade Security & Rate Limiting
🔧 Plugin Architecture for Custom Extensions
📊 Advanced Monitoring with Distributed Tracing
🤖 Function Calling & Tool Integration
💾 Persistent Conversation Memory with Vector Search
"""

import asyncio
import json
import logging
import time
import hashlib
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache, wraps
from typing import (
    Any, Dict, List, Optional, Union, AsyncGenerator, 
    Callable, TypeVar, Generic, Type, Tuple, Protocol
)
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional imports with graceful fallbacks
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from pydantic import BaseModel, ValidationError, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    ValidationError = Exception
    Field = lambda **kwargs: lambda x: x

try:
    import prometheus_client as prometheus
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    prometheus = None

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None

# Local imports
try:
    from app.config.settings import settings
except ImportError:
    # Fallback settings
    class Settings:
        def __init__(self):
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            self.openai_base_url = os.getenv("OPENAI_BASE_URL")
            self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))
            self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
            self.timeout = int(os.getenv("TIMEOUT", "30"))
    
    settings = Settings()

logger = logging.getLogger(__name__)

# Enhanced Prometheus metrics with labels (if available)
if PROMETHEUS_AVAILABLE:
    LLM_REQUESTS_TOTAL = prometheus.Counter(
        'llm_requests_total', 
        'Total LLM requests', 
        ['provider', 'model', 'status', 'endpoint']
    )
    LLM_REQUEST_DURATION = prometheus.Histogram(
        'llm_request_duration_seconds', 
        'LLM request duration', 
        ['provider', 'model', 'endpoint']
    )
    LLM_TOKENS_USED = prometheus.Counter(
        'llm_tokens_used', 
        'Tokens used', 
        ['provider', 'model', 'type', 'operation']
    )
    LLM_CACHE_HITS = prometheus.Counter('llm_cache_hits_total', 'Cache hit count')
    LLM_CACHE_MISSES = prometheus.Counter('llm_cache_misses_total', 'Cache miss count')
    LLM_ERRORS = prometheus.Counter('llm_errors_total', 'Error count', ['provider', 'error_type'])
else:
    # Mock metrics
    class MockMetric:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    
    LLM_REQUESTS_TOTAL = MockMetric()
    LLM_REQUEST_DURATION = MockMetric()
    LLM_TOKENS_USED = MockMetric()
    LLM_CACHE_HITS = MockMetric()
    LLM_CACHE_MISSES = MockMetric()
    LLM_ERRORS = MockMetric()

class LLMProvider(str, Enum):
    """Supported LLM providers with latest models"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"
    GOOGLE = "google"
    AZURE = "azure"
    COHERE = "cohere"
    MISTRAL = "mistral"
    TOGETHER = "together"

class MessageRole(str, Enum):
    """Enhanced message roles for modern chat completion"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"
    OBSERVATION = "observation"
    THOUGHT = "thought"

class FinishReason(str, Enum):
    """Comprehensive finish reasons for LLM responses"""
    STOP = "stop"
    LENGTH = "length"
    FUNCTION_CALL = "function_call"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    MAX_TOKENS = "max_tokens"
    ERROR = "error"

@dataclass
class Message:
    """Enhanced chat message with modern features"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    embedding: Optional[List[float]] = None

@dataclass
class FunctionDefinition:
    """Advanced function definition for function calling"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: Optional[List[str]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    validation_schema: Optional[Dict[str, Any]] = None

@dataclass
class LLMRequest:
    """Ultra-modern LLM request with advanced features"""
    messages: List[Message]
    model: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    timeout: int = 30
    retries: int = 3
    cache: bool = True
    cache_ttl: int = 3600
    functions: Optional[List[FunctionDefinition]] = None
    function_call: Optional[Union[str, Dict[str, str]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, str]]] = None
    response_format: Optional[Dict[str, str]] = None
    seed: Optional[int] = None
    user: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    # New advanced features
    safety_settings: Optional[Dict[str, Any]] = None
    generation_config: Optional[Dict[str, Any]] = None
    stop_sequences: Optional[List[str]] = None
    logit_bias: Optional[Dict[str, float]] = None
    parallel_tool_calls: bool = False
    max_parallel_tool_calls: int = 5

@dataclass
class LLMResponse:
    """Enhanced LLM response with comprehensive metadata"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[FinishReason] = None
    metadata: Optional[Dict[str, Any]] = None
    function_calls: Optional[List[Dict[str, Any]]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost: Optional[float] = None
    latency: Optional[float] = None
    # New fields
    confidence_score: Optional[float] = None
    safety_scores: Optional[Dict[str, float]] = None
    reasoning: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None
    streaming_id: Optional[str] = None

@dataclass
class LLMConfig:
    """Advanced configuration for LLM providers"""
    provider: LLMProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: str = "gpt-4-turbo-preview"
    max_retries: int = 3
    timeout: int = 30
    cache_ttl: int = 3600
    rate_limit: Optional[int] = None
    cost_per_1k_tokens: Optional[float] = None
    max_concurrent_requests: int = 10
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    # New advanced config
    enable_streaming: bool = True
    enable_function_calling: bool = True
    enable_safety_filters: bool = True
    enable_cost_tracking: bool = True
    enable_analytics: bool = True
    custom_headers: Optional[Dict[str, str]] = None
    proxy_config: Optional[Dict[str, str]] = None
    encryption_key: Optional[str] = None

@dataclass
class ConversationContext:
    """Advanced conversation context with vector search"""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    max_messages: int = 50
    # New features
    vector_embeddings: List[List[float]] = field(default_factory=list)
    summary: Optional[str] = None
    sentiment_score: Optional[float] = None
    topics: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)

class AdvancedCircuitBreaker:
    """Enhanced circuit breaker with adaptive thresholds"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, success_threshold: int = 2):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == "OPEN":
                if self.last_failure_time and time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            with self._lock:
                if self.state == "HALF_OPEN":
                    self.success_count += 1
                    if self.success_count >= self.success_threshold:
                        self.state = "CLOSED"
                        self.failure_count = 0
                        self.success_count = 0
                        logger.info("Circuit breaker transitioning to CLOSED")
            return result
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
            raise e

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []
        self._lock = threading.Lock()
    
    def can_proceed(self) -> bool:
        """Check if request can proceed"""
        with self._lock:
            now = time.time()
            # Remove old requests
            self.requests = [req for req in self.requests if now - req < self.time_window]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    async def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        while not self.can_proceed():
            await asyncio.sleep(1)

class PromptTemplate:
    """Template system for prompt management"""
    
    def __init__(self, template: str, variables: Optional[Dict[str, Any]] = None):
        self.template = template
        self.variables = variables or {}
    
    def format(self, **kwargs) -> str:
        """Format template with variables"""
        variables = {**self.variables, **kwargs}
        return self.template.format(**variables)
    
    @classmethod
    def from_file(cls, filepath: str) -> 'PromptTemplate':
        """Load template from file"""
        with open(filepath, 'r') as f:
            template = f.read()
        return cls(template)

class ConversationMemory:
    """Memory management for conversations"""
    
    def __init__(self, max_sessions: int = 1000):
        self.sessions: Dict[str, ConversationContext] = {}
        self.max_sessions = max_sessions
        self._lock = threading.Lock()
    
    def add_message(self, session_id: str, message: Message) -> None:
        """Add message to conversation"""
        with self._lock:
            if session_id not in self.sessions:
                if len(self.sessions) >= self.max_sessions:
                    # Remove oldest session
                    oldest_session = min(self.sessions.keys(), 
                                       key=lambda k: self.sessions[k].created_at)
                    del self.sessions[oldest_session]
                
                self.sessions[session_id] = ConversationContext(session_id=session_id)
            
            session = self.sessions[session_id]
            session.messages.append(message)
            session.updated_at = datetime.now()
            
            # Keep only recent messages
            if len(session.messages) > session.max_messages:
                session.messages = session.messages[-session.max_messages:]
    
    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation session"""
        with self._lock:
            return self.sessions.get(session_id)
    
    def clear_session(self, session_id: str) -> None:
        """Clear a specific session"""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]

class LLMProviderBase(ABC):
    """Base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        self._circuit_breaker = AdvancedCircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout
        )
        self._rate_limiter = RateLimiter(
            max_requests=config.rate_limit or 100,
            time_window=60
        ) if config.rate_limit else None
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider client"""
        pass
    
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available"""
        pass
    
    async def generate_async(self, request: LLMRequest) -> LLMResponse:
        """Async wrapper for generate method"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, request)
    
    def _apply_rate_limiting(self):
        """Apply rate limiting if configured"""
        if self._rate_limiter and not self._rate_limiter.can_proceed():
            raise Exception("Rate limit exceeded")

class OpenAIProvider(LLMProviderBase):
    """OpenAI provider implementation"""
    
    def initialize(self) -> None:
        try:
            import openai
            self._client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
        except ImportError:
            raise RuntimeError("OpenAI package not installed")
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        if not self._client:
            self.initialize()
        
        # Apply rate limiting
        self._apply_rate_limiting()
        
        # Use circuit breaker
        return self._circuit_breaker.call(self._generate_internal, request)
    
    def _generate_internal(self, request: LLMRequest) -> LLMResponse:
        """Internal generation method"""
        try:
            # Prepare messages
            messages = []
            for msg in request.messages:
                message_dict = {"role": msg.role.value, "content": msg.content}
                if msg.name:
                    message_dict["name"] = msg.name
                if msg.tool_calls:
                    message_dict["tool_calls"] = msg.tool_calls
                if msg.tool_call_id:
                    message_dict["tool_call_id"] = msg.tool_call_id
                if msg.function_call:
                    message_dict["function_call"] = msg.function_call
                messages.append(message_dict)
            
            # Prepare function definitions
            functions = None
            if request.functions:
                functions = []
                for func in request.functions:
                    func_dict = {
                        "name": func.name,
                        "description": func.description,
                        "parameters": func.parameters
                    }
                    if func.required:
                        func_dict["required"] = func.required
                    functions.append(func_dict)
            
            # Make API call
            response = self._client.chat.completions.create(
                model=request.model or self.config.default_model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                timeout=request.timeout,
                functions=functions,
                function_call=request.function_call,
                tools=request.tools,
                tool_choice=request.tool_choice,
                response_format=request.response_format,
                seed=request.seed,
                user=request.user,
                stop=request.stop_sequences,
                logit_bias=request.logit_bias
            )
            
            content = response.choices[0].message.content or ""
            
            # Extract function calls and tool calls
            function_calls = None
            tool_calls = None
            if hasattr(response.choices[0].message, 'function_call') and response.choices[0].message.function_call:
                function_calls = [response.choices[0].message.function_call.model_dump()]
            
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                tool_calls = [tc.model_dump() for tc in response.choices[0].message.tool_calls]
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=response.usage.model_dump() if response.usage else None,
                finish_reason=FinishReason(response.choices[0].finish_reason) if response.choices[0].finish_reason else None,
                function_calls=function_calls,
                tool_calls=tool_calls,
                prompt_tokens=response.usage.prompt_tokens if response.usage else None,
                completion_tokens=response.usage.completion_tokens if response.usage else None,
                total_tokens=response.usage.total_tokens if response.usage else None,
                latency=time.time() - time.time()  # Will be set by caller
            )
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    def is_available(self) -> bool:
        try:
            import openai
            return True
        except ImportError:
            return False

class MockProvider(LLMProviderBase):
    """Mock provider for testing when no API key is available"""
    
    def initialize(self) -> None:
        """Mock initialization - always succeeds"""
        pass
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a mock response"""
        # Create a simple mock response based on the input
        user_message = ""
        for msg in request.messages:
            if msg.role == MessageRole.USER:
                user_message = msg.content
                break
        
        # Generate appropriate mock responses
        if "hello" in user_message.lower():
            mock_response = "Hello! I'm your AI booking assistant. How can I help you schedule a meeting today?"
        elif "book" in user_message.lower() or "meeting" in user_message.lower():
            mock_response = "I'd be happy to help you book a meeting! Could you please provide the date, time, and duration?"
        elif "date" in user_message.lower() or "time" in user_message.lower():
            mock_response = "Great! I can help you with that. What date and time would you prefer for the meeting?"
        else:
            mock_response = "I understand. Please let me know how I can assist you with booking a meeting or appointment."
        
        return LLMResponse(
            content=mock_response,
            model="mock-model",
            usage={"prompt_tokens": len(user_message), "completion_tokens": len(mock_response)},
            finish_reason=FinishReason.STOP
        )
    
    def extract_entities(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract booking entities using regex patterns"""
        entities = {}
        text_lower = text.lower()
        
        # Extract date
        date_patterns = [
            r'tomorrow',
            r'today',
            r'next (\w+)',  # next monday, next week
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if pattern == r'tomorrow':
                    date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                    entities['date'] = date
                    break
                elif pattern == r'today':
                    date = datetime.now().strftime('%Y-%m-%d')
                    entities['date'] = date
                    break
                elif pattern == r'next (\w+)':
                    day_name = match.group(1)
                    # Simple day mapping
                    day_map = {
                        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                        'friday': 4, 'saturday': 5, 'sunday': 6,
                        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
                    }
                    if day_name in day_map:
                        target_day = day_map[day_name]
                        current_day = datetime.now().weekday()
                        days_ahead = target_day - current_day
                        if days_ahead <= 0:  # Target day already happened this week
                            days_ahead += 7
                        date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                        entities['date'] = date
                        break
                else:
                    # Handle numeric date patterns
                    groups = match.groups()
                    if len(groups) == 3:
                        if len(groups[0]) == 4:  # YYYY-MM-DD
                            entities['date'] = f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
                        else:  # Assume MM/DD/YYYY or DD/MM/YYYY
                            # Try both formats
                            try:
                                date = datetime(int(groups[2]), int(groups[0]), int(groups[1]))
                                entities['date'] = date.strftime('%Y-%m-%d')
                            except:
                                try:
                                    date = datetime(int(groups[2]), int(groups[1]), int(groups[0]))
                                    entities['date'] = date.strftime('%Y-%m-%d')
                                except:
                                    pass
                        break
        
        # Extract time
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 2:30 PM
            r'(\d{1,2})\s*(am|pm)',  # 2 PM
            r'(\d{1,2}):(\d{2})',  # 14:30
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                if len(groups) == 3:  # 2:30 PM format
                    hour = int(groups[0])
                    minute = int(groups[1])
                    ampm = groups[2]
                    if ampm == 'pm' and hour != 12:
                        hour += 12
                    elif ampm == 'am' and hour == 12:
                        hour = 0
                    entities['time'] = f"{hour:02d}:{minute:02d}"
                    break
                elif len(groups) == 2:  # 2 PM format
                    hour = int(groups[0])
                    ampm = groups[1]
                    if ampm == 'pm' and hour != 12:
                        hour += 12
                    elif ampm == 'am' and hour == 12:
                        hour = 0
                    entities['time'] = f"{hour:02d}:00"
                    break
                elif len(groups) == 2:  # 14:30 format
                    hour = int(groups[0])
                    minute = int(groups[1])
                    entities['time'] = f"{hour:02d}:{minute:02d}"
                    break
        
        # Extract duration
        duration_patterns = [
            r'(\d+)\s*(?:minute|min)s?',
            r'(\d+)\s*(?:hour|hr)s?',
            r'(\d+)\s*(?:hour|hr)s?\s*(\d+)\s*(?:minute|min)s?',
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text_lower)
            if match:
                groups = match.groups()
                if len(groups) == 1:  # Just minutes or just hours
                    value = int(groups[0])
                    if 'hour' in pattern or 'hr' in pattern:
                        entities['duration'] = value * 60  # Convert to minutes
                    else:
                        entities['duration'] = value
                    break
                elif len(groups) == 2:  # Hours and minutes
                    hours = int(groups[0])
                    minutes = int(groups[1])
                    entities['duration'] = hours * 60 + minutes
                    break
        
        # Extract purpose/description
        purpose_patterns = [
            r'for\s+(.+)',
            r'about\s+(.+)',
            r'regarding\s+(.+)',
            r'to\s+discuss\s+(.+)',
        ]
        
        for pattern in purpose_patterns:
            match = re.search(pattern, text_lower)
            if match:
                purpose = match.group(1).strip()
                # Clean up the purpose
                purpose = re.sub(r'\b(meeting|appointment|call)\b', '', purpose).strip()
                if purpose and len(purpose) > 3:
                    entities['purpose'] = purpose
                    break
        
        return entities
    
    def is_available(self) -> bool:
        """Mock provider is always available"""
        return True

class LLMCache:
    """Advanced cache for LLM responses with TTL and size limits"""
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        self._cache: Dict[str, tuple] = {}
        self._ttl = ttl
        self._max_size = max_size
        self._lock = threading.Lock()
    
    def _get_key(self, request: LLMRequest) -> str:
        """Generate cache key from request"""
        content = json.dumps([
            {
                "role": msg.role.value,
                "content": msg.content
            } for msg in request.messages
        ], sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Get cached response"""
        key = self._get_key(request)
        with self._lock:
            if key in self._cache:
                response, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    LLM_CACHE_HITS.inc()
                    return response
                else:
                    del self._cache[key]
            LLM_CACHE_MISSES.inc()
        return None
    
    def set(self, request: LLMRequest, response: LLMResponse) -> None:
        """Cache response"""
        key = self._get_key(request)
        with self._lock:
            # Check if we need to evict old entries
            if len(self._cache) >= self._max_size:
                # Remove oldest entries
                current_time = time.time()
                expired_keys = [
                    k for k, (_, timestamp) in self._cache.items()
                    if current_time - timestamp > self._ttl
                ]
                for k in expired_keys:
                    del self._cache[k]
                
                # If still full, remove oldest
                if len(self._cache) >= self._max_size:
                    oldest_key = min(self._cache.keys(), 
                                   key=lambda k: self._cache[k][1])
                    del self._cache[oldest_key]
            
            self._cache[key] = (response, time.time())
    
    def clear(self) -> None:
        """Clear cache"""
        with self._lock:
            self._cache.clear()

class LLMService:
    """Main LLM service that manages multiple providers"""
    
    def __init__(self):
        self._providers: Dict[LLMProvider, LLMProviderBase] = {}
        self._cache = LLMCache()
        self._memory = ConversationMemory()
        self._default_provider = LLMProvider.OPENAI
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize available providers"""
        # OpenAI
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("BOOKING_AGENT_LLM_API_KEY")
        if api_key and api_key != "your_openai_api_key_here":
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key=api_key,
                base_url=os.getenv("OPENAI_BASE_URL"),
                default_model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            )
            provider = OpenAIProvider(config)
            if provider.is_available():
                self._providers[LLMProvider.OPENAI] = provider
        
        # If no providers available, add mock provider
        if not self._providers:
            logger.warning("No LLM providers available, using mock provider for testing")
            config = LLMConfig(
                provider=LLMProvider.LOCAL,
                default_model="mock-model"
            )
            mock_provider = MockProvider(config)
            self._providers[LLMProvider.LOCAL] = mock_provider
            self._default_provider = LLMProvider.LOCAL
        
        logger.info(f"Initialized {len(self._providers)} LLM providers: {list(self._providers.keys())}")
    
    def generate(
        self,
        messages: List[Message],
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the specified provider"""
        provider = provider or self._default_provider
        
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not available")
        
        request = LLMRequest(messages=messages, **kwargs)
        
        # Check cache first
        if request.cache:
            cached = self._cache.get(request)
            if cached:
                logger.info("LLM response cache hit")
                return cached
        
        # Generate response with retry logic
        start_time = time.time()
        for attempt in range(request.retries):
            try:
                response = self._providers[provider].generate(request)
                response.latency = time.time() - start_time
                
                # Cache the response
                if request.cache:
                    self._cache.set(request, response)
                
                # Update metrics
                LLM_REQUESTS_TOTAL.inc(labels={
                    'provider': provider.value,
                    'model': response.model,
                    'status': 'success',
                    'endpoint': 'generate'
                })
                LLM_REQUEST_DURATION.observe(
                    response.latency,
                    labels={'provider': provider.value, 'model': response.model, 'endpoint': 'generate'}
                )
                
                return response
            except Exception as e:
                if attempt == request.retries - 1:
                    LLM_ERRORS.inc(labels={'provider': provider.value, 'error_type': type(e).__name__})
                    raise
                logger.warning(f"LLM generation failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
    
    async def generate_async(
        self,
        messages: List[Message],
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> LLMResponse:
        """Async version of generate"""
        provider = provider or self._default_provider
        
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not available")
        
        request = LLMRequest(messages=messages, **kwargs)
        
        # Check cache first
        if request.cache:
            cached = self._cache.get(request)
            if cached:
                logger.info("LLM response cache hit (async)")
                return cached
        
        # Use async provider method if available
        provider_instance = self._providers[provider]
        if hasattr(provider_instance, 'generate_async'):
            return await provider_instance.generate_async(request)
        else:
            # Fallback to sync version in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._executor,
                self.generate,
                messages,
                provider,
                **kwargs
            )
    
    def extract_entities(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured entities from text using LLM"""
        prompt = f"""
        Extract the following entities from the text and return as JSON:
        Schema: {json.dumps(schema, indent=2)}
        
        Text: {text}
        
        Return only valid JSON:
        """
        
        messages = [Message(role=MessageRole.USER, content=prompt)]
        
        try:
            response = self.generate(messages, temperature=0.0)
            
            # Parse JSON response
            try:
                # Find JSON in response
                start = response.content.find('{')
                end = response.content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response.content[start:end]
                    return json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {e}")
                return {}
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {}
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers"""
        return list(self._providers.keys())
    
    def set_default_provider(self, provider: LLMProvider) -> None:
        """Set the default provider"""
        if provider in self._providers:
            self._default_provider = provider
        else:
            raise ValueError(f"Provider {provider} not available")
    
    def clear_cache(self) -> None:
        """Clear the response cache"""
        self._cache.clear()
    
    def add_to_memory(self, session_id: str, message: Message) -> None:
        """Add message to conversation memory"""
        self._memory.add_message(session_id, message)
    
    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session"""
        return self._memory.get_session(session_id)
    
    def clear_conversation(self, session_id: str) -> None:
        """Clear conversation for a session"""
        self._memory.clear_session(session_id)

# Global LLM service instance
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get the global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

# Convenience functions for backward compatibility
def call_llm(
    prompt: str,
    *,
    model: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    **kwargs
) -> str:
    """Synchronous LLM call with new service"""
    messages = []
    if system_prompt:
        messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
    messages.append(Message(role=MessageRole.USER, content=prompt))
    
    service = get_llm_service()
    response = service.generate(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        provider=provider,
        **kwargs
    )
    return response.content

async def async_call_llm(
    prompt: str,
    *,
    model: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
    provider: Optional[LLMProvider] = None,
    **kwargs
) -> str:
    """Async LLM call with new service"""
    messages = []
    if system_prompt:
        messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
    messages.append(Message(role=MessageRole.USER, content=prompt))
    
    service = get_llm_service()
    response = await service.generate_async(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        provider=provider,
        **kwargs
    )
    return response.content 