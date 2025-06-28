"""
Booking Agent Module

This module provides a clean interface to the BookingAgent functionality.
It handles the import and re-export of the BookingAgent class for better
module organization and cleaner imports throughout the application.
"""

import logging
import os
import sys
import importlib.util
import traceback
from typing import TYPE_CHECKING, Optional, Any, Union, Protocol
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


# Configure logging for this module
logger = logging.getLogger(__name__)


# Type checking imports to avoid circular dependencies
if TYPE_CHECKING:
    from ..services.agent_service import BookingAgent

class ImportStatus(Enum):
    """Enumeration for import status tracking"""
    SUCCESS = "success"
    FAILED = "failed"
    FALLBACK = "fallback"
    NOT_FOUND = "not_found"

@dataclass
class ImportResult:
    """Data class for structured import results"""
    status: ImportStatus
    agent_class: Optional[Any] = None
    error_message: Optional[str] = None
    source_path: Optional[Path] = None

class BookingAgentProtocol(Protocol):
    """Protocol defining the expected BookingAgent interface"""
    def __init__(self, *args, **kwargs) -> None: ...
    def process_message(self, *args, **kwargs) -> Any: ...
    def get_response(self, *args, **kwargs) -> Any: ...

class BookingAgentImporter:
    """Modern, robust importer for BookingAgent with comprehensive error handling"""
    
    def __init__(self):
        self.current_file = Path(__file__).resolve()
        self.possible_paths = self._generate_possible_paths()
        self.required_methods = ['__init__', 'process_message', 'get_response']
        self.required_attributes = ['__name__', '__class__', '__module__']
    
    def _generate_possible_paths(self) -> list[Path]:
        """Generate all possible paths for agent_service.py"""
        return [
            self.current_file.parent.parent / "services" / "agent_service.py",
            self.current_file.parent.parent / "app" / "services" / "agent_service.py",
            Path.cwd() / "app" / "services" / "agent_service.py",
            Path.cwd() / "backend" / "app" / "services" / "agent_service.py",
            Path.cwd() / "services" / "agent_service.py"
        ]
    
    def _validate_file_access(self, file_path: Path) -> bool:
        """Validate file accessibility and permissions"""
        try:
            if not file_path.exists():
                logger.debug(f"File does not exist: {file_path}")
                return False
            
            if not file_path.is_file():
                logger.error(f"Path exists but is not a file: {file_path}")
                return False
            
            if not os.access(file_path, os.R_OK):
                logger.error(f"File exists but is not readable: {file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file access for {file_path}: {e}")
            return False
    
    def _validate_class_content(self, file_path: Path) -> bool:
        """Validate that file contains BookingAgent class"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'class BookingAgent' in content
        except Exception as e:
            logger.error(f"Error reading file content: {e}")
            return False
    
    def _find_agent_service_file(self) -> Optional[Path]:
        """Find the agent_service.py file using multiple strategies"""
        for path in self.possible_paths:
            if self._validate_file_access(path):
                if self._validate_class_content(path):
                    logger.info(f"Found valid agent_service.py at: {path}")
                    return path
                else:
                    logger.warning(f"File found but BookingAgent class not detected: {path}")
        
        logger.error("agent_service.py not found in any expected location")
        return None
    
    def _import_from_path(self, file_path: Path) -> Optional[Any]:
        """Import BookingAgent from a specific file path"""
        try:
            spec = importlib.util.spec_from_file_location("agent_service", file_path)
            if not spec or not spec.loader:
                logger.error(f"Failed to create spec for {file_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'BookingAgent'):
                return module.BookingAgent
            else:
                logger.error(f"BookingAgent class not found in module at {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error importing from {file_path}: {e}")
            return None
    
    def _validate_imported_class(self, agent_class: Any) -> bool:
        """Validate the imported BookingAgent class structure"""
        try:
            # Check if it's actually a class
            if not isinstance(agent_class, type):
                logger.error(f"BookingAgent is not a class (type: {type(agent_class).__name__})")
                return False
            
            # Check required attributes
            missing_attrs = [attr for attr in self.required_attributes if not hasattr(agent_class, attr)]
            if missing_attrs:
                logger.error(f"BookingAgent missing required attributes: {missing_attrs}")
                return False
            
            # Check required methods
            missing_methods = [method for method in self.required_methods if not hasattr(agent_class, method)]
            if missing_methods:
                logger.warning(f"BookingAgent missing required methods: {missing_methods}")
                # Don't fail here, just warn
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating imported class: {e}")
            return False
    
    def import_booking_agent(self) -> ImportResult:
        """Main import method with comprehensive error handling"""
        try:
            # Step 1: Find the agent_service.py file
            file_path = self._find_agent_service_file()
            if not file_path:
                return ImportResult(
                    status=ImportStatus.NOT_FOUND,
                    error_message="agent_service.py not found in any expected location"
                )
            
            # Step 2: Import from the found path
            agent_class = self._import_from_path(file_path)
            if not agent_class:
                return ImportResult(
                    status=ImportStatus.FAILED,
                    error_message="Failed to import BookingAgent from found file"
                )
            
            # Step 3: Validate the imported class
            if not self._validate_imported_class(agent_class):
                return ImportResult(
                    status=ImportStatus.FAILED,
                    error_message="Imported BookingAgent class validation failed"
                )
            
            # Step 4: Try primary import as fallback validation
            try:
                from ..services.agent_service import BookingAgent as PrimaryBookingAgent
                if agent_class == PrimaryBookingAgent:
                    logger.debug("Primary import matches fallback import")
                else:
                    logger.warning("Primary and fallback imports differ")
            except ImportError:
                logger.info("Primary import failed, using fallback import")
            
            return ImportResult(
                status=ImportStatus.SUCCESS,
                agent_class=agent_class,
                source_path=file_path
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during import: {e}")
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return ImportResult(
                status=ImportStatus.FAILED,
                error_message=str(e)
            )

def validate_import_path() -> bool:
    """Validate the import path for BookingAgent"""
    try:
        from ..services.agent_service import BookingAgent
        return True
    except Exception as e:
        logger.error(f"Error validating import path: {e}")
        logger.error(f"Current working directory: {Path.cwd()}")
        logger.error(f"Current file location: {Path(__file__).resolve()}")
        return False

def safe_import_booking_agent() -> Optional[Any]:
    """Safely import BookingAgent with comprehensive error handling and fallback strategies"""
    # Enhanced validation with multiple strategies
    if not validate_import_path():
        logger.warning("Primary import path validation failed, attempting fallback import")
        
        # Fallback import attempt
        try:
            current_file = Path(__file__).resolve()
            
            # Try multiple possible locations
            possible_paths = [
                current_file.parent.parent / "services" / "agent_service.py",
                current_file.parent.parent / "app" / "services" / "agent_service.py",
                Path.cwd() / "app" / "services" / "agent_service.py",
                Path.cwd() / "backend" / "app" / "services" / "agent_service.py"
            ]
            
            for path in possible_paths:
                if path.exists():
                    spec = importlib.util.spec_from_file_location("agent_service", path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, 'BookingAgent'):
                            logger.info(f"Successfully imported BookingAgent from fallback path: {path}")
                            return module.BookingAgent
            
        except Exception as fallback_error:
            logger.error(f"Fallback import also failed: {fallback_error}")
    
    # Primary import attempt
    try:
        # Import the BookingAgent class from agent_service.py
        from ..services.agent_service import BookingAgent
        
        # Enhanced validation with comprehensive class structure verification
        if not hasattr(BookingAgent, '__name__') or not hasattr(BookingAgent, '__class__'):
            logger.error("BookingAgent import appears to be invalid - missing core attributes")
            return None
        
        # Validate class structure and required interface
        required_attributes = ['__name__', '__class__', '__module__']
        missing_attrs = [attr for attr in required_attributes if not hasattr(BookingAgent, attr)]
        
        if missing_attrs:
            logger.error(f"BookingAgent missing required attributes: {missing_attrs}")
            return None
        
        # Verify it's actually a class, not an instance or other object
        if not isinstance(BookingAgent, type):
            logger.error(f"BookingAgent is not a class (type: {type(BookingAgent).__name__})")
            return None
        
        # Log successful import with additional context
        logger.debug(f"Successfully imported BookingAgent from {BookingAgent.__module__}")
        return BookingAgent
        
    except ImportError as e:
        # Enhanced import error handling with specific error categorization
        error_msg = str(e)
        logger.error(f"Failed to import BookingAgent: {error_msg}")
        
        # Provide specific guidance based on error type
        if "No module named" in error_msg:
            logger.error("Module not found - check PYTHONPATH and project structure")
            logger.error("Ensure agent_service.py exists in the services directory")
        elif "cannot import name" in error_msg:
            logger.error("Class not found in module - check if BookingAgent class exists in agent_service.py")
        elif "circular import" in error_msg.lower():
            logger.error("Circular import detected - review import structure")
        
        logger.error("Please ensure agent_service.py exists and contains BookingAgent class")
        logger.error("Check that all dependencies are properly installed")
        return None
        
    except Exception as e:
        # Comprehensive error analysis with structured logging and recovery suggestions
        error_type = type(e).__name__
        error_details = str(e)
        
        logger.error(f"Unexpected error importing BookingAgent: {error_details}")
        logger.error(f"Error type: {error_type}")
        logger.error(f"Error details: {error_details}")
        
        # Enhanced error categorization and recovery guidance
        if "ModuleNotFoundError" in error_type:
            logger.error("Module path issue detected - check PYTHONPATH and relative imports")
            logger.error("Verify project structure and __init__.py files")
        elif "AttributeError" in error_type:
            logger.error("Missing attribute detected - verify BookingAgent class definition")
            logger.error("Check for typos in class name or missing imports")
        elif "SyntaxError" in error_type:
            logger.error("Syntax error in source file - validate agent_service.py syntax")
            logger.error("Check for missing brackets, quotes, or invalid Python syntax")
        elif "IndentationError" in error_type:
            logger.error("Indentation error detected - check code formatting in agent_service.py")
        elif "NameError" in error_type:
            logger.error("Name error detected - check for undefined variables or imports")
        else:
            logger.error(f"Unknown error type: {error_type} - check system compatibility")
        
        import traceback
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        
        # Check if this is a common import issue and provide specific guidance
        if "ModuleNotFoundError" in str(type(e).__name__):
            logger.error("This appears to be a module path issue - check PYTHONPATH and relative imports")
        elif "AttributeError" in str(type(e).__name__):
            logger.error("This appears to be a missing attribute - check if BookingAgent class exists in agent_service.py")
        elif "SyntaxError" in str(type(e).__name__):
            logger.error("This appears to be a syntax error in agent_service.py - check file syntax")
        
        # Return None to indicate import failure, allowing fallback mechanisms to activate
        return None

# Enhanced BookingAgent import with comprehensive validation and error recovery
try:
    # Attempt to import BookingAgent with fallback mechanisms
    BookingAgent = safe_import_booking_agent()
    
    # Additional validation for imported class
    if BookingAgent is not None:
        # Verify class has required methods and attributes
        required_methods = ['__init__', 'process_message', 'get_response']
        missing_methods = [method for method in required_methods if not hasattr(BookingAgent, method)]
        
        if missing_methods:
            logger.warning(f"BookingAgent missing required methods: {missing_methods}")
            # Try to provide a fallback or mock implementation
            BookingAgent = None
    
    # Re-export for cleaner imports and better module organization
    __all__ = ['BookingAgent']
    
    # Comprehensive validation and logging
    if BookingAgent is None:
        logger.error("BookingAgent import failed - implementing fallback mechanism")
        # Create a minimal fallback class to prevent import errors
        class FallbackBookingAgent:
            def __init__(self, *args, **kwargs):
                logger.warning("Using fallback BookingAgent - limited functionality")
                raise NotImplementedError("BookingAgent not properly imported")
        
        BookingAgent = FallbackBookingAgent
        __all__ = ['BookingAgent']
    
    # Final validation and success logging
    logger.info("BookingAgent module successfully initialized")
    
except Exception as e:
    logger.critical(f"Critical error during BookingAgent initialization: {e}")
    # Ensure module doesn't crash completely
    BookingAgent = None
    __all__ = ['BookingAgent']

# Final validation checks
if BookingAgent is None:
    logger.error("BookingAgent import failed - module may not function correctly")
elif not hasattr(BookingAgent, '__call__'):
    logger.warning("BookingAgent may not be properly initialized as a callable class")
elif not hasattr(BookingAgent, '__init__'):
    logger.warning("BookingAgent appears to be missing proper initialization method")

def import_booking_agent():
    try:
        from ..services.agent_service import BookingAgent
        # Validate class
        if not isinstance(BookingAgent, type):
            raise TypeError("BookingAgent is not a class.")
        for method in ['__init__', 'process_message', 'get_response']:
            if not hasattr(BookingAgent, method):
                raise AttributeError(f"BookingAgent missing required method: {method}")
        return BookingAgent
    except Exception as e:
        logger.error(f"Failed to import BookingAgent: {e}")
        raise ImportError(
            "BookingAgent could not be imported or is invalid. "
            "Check that backend/app/services/agent_service.py defines a BookingAgent class "
            "with required methods: __init__, process_message, get_response."
        ) from e

BookingAgent = import_booking_agent()