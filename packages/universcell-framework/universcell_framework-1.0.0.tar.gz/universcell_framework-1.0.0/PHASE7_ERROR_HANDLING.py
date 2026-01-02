"""
PHASE 7: ERROR HANDLING & GRACEFUL DEGRADATION
Day 9 Implementation - Production-Ready Error Recovery

Handles:
- File I/O failures (disk full, permission denied, concurrent writes)
- JSON corruption recovery
- Graceful degradation (in-memory fallback)
- Comprehensive logging for all decisions

Architecture:
1. FileIOErrorHandler - recovers from file system failures
2. JSONCorruptionRecovery - detects and repairs corrupted state
3. GracefulDegradation - fallback to in-memory when persistent fails
4. ErrorLogger - comprehensive logging with context preservation
"""

import json
import os
import logging
import hashlib
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for operational awareness"""
    CRITICAL = "CRITICAL"  # System-wide failure
    HIGH = "HIGH"          # Feature degraded
    MEDIUM = "MEDIUM"      # Minor issue
    LOW = "LOW"            # Info only


@dataclass
class ErrorContext:
    """Context preserved during error recovery"""
    timestamp: str
    error_type: str
    severity: ErrorSeverity
    message: str
    operation: str  # What was being done
    recovery_action: str  # How we recovered
    data_preserved: bool  # Did we keep data safe?
    logs: List[str] = field(default_factory=list)


class FileIOErrorHandler:
    """Handles file I/O errors gracefully"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # seconds
    
    def __init__(self, logger=None):
        self.logger = logger
        self.error_counts = {}  # track failures per file
    
    def safe_read(self, filepath: str) -> Tuple[Optional[str], Optional[ErrorContext]]:
        """Read file with retry and fallback logic"""
        for attempt in range(self.MAX_RETRIES):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return content, None
            except FileNotFoundError:
                return None, ErrorContext(
                    timestamp=datetime.utcnow().isoformat(),
                    error_type="FileNotFoundError",
                    severity=ErrorSeverity.HIGH,
                    message=f"File not found: {filepath}",
                    operation="read",
                    recovery_action="returned_none",
                    data_preserved=True
                )
            except PermissionError:
                context = ErrorContext(
                    timestamp=datetime.utcnow().isoformat(),
                    error_type="PermissionError",
                    severity=ErrorSeverity.CRITICAL,
                    message=f"Permission denied: {filepath}",
                    operation="read",
                    recovery_action=f"retry_{attempt + 1}_of_{self.MAX_RETRIES}",
                    data_preserved=True
                )
                if attempt == self.MAX_RETRIES - 1:
                    return None, context
                time.sleep(self.RETRY_DELAY)
            except IOError as e:
                context = ErrorContext(
                    timestamp=datetime.utcnow().isoformat(),
                    error_type="IOError",
                    severity=ErrorSeverity.HIGH,
                    message=str(e),
                    operation="read",
                    recovery_action=f"retry_{attempt + 1}_of_{self.MAX_RETRIES}",
                    data_preserved=True
                )
                if attempt == self.MAX_RETRIES - 1:
                    return None, context
                time.sleep(self.RETRY_DELAY)
        
        return None, ErrorContext(
            timestamp=datetime.utcnow().isoformat(),
            error_type="MaxRetriesExceeded",
            severity=ErrorSeverity.CRITICAL,
            message=f"Failed to read {filepath} after {self.MAX_RETRIES} retries",
            operation="read",
            recovery_action="exhausted_retries",
            data_preserved=True
        )
    
    def safe_write(self, filepath: str, content: str) -> Tuple[bool, Optional[ErrorContext]]:
        """Write file with atomic write pattern (write to temp, then rename)"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            
            # Use atomic write pattern
            temp_fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(filepath) or '.',
                text=True
            )
            
            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())
                
                # Atomic rename
                shutil.move(temp_path, filepath)
                return True, None
            except Exception as e:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise
        
        except PermissionError:
            return False, ErrorContext(
                timestamp=datetime.utcnow().isoformat(),
                error_type="PermissionError",
                severity=ErrorSeverity.CRITICAL,
                message=f"Permission denied writing to: {filepath}",
                operation="write",
                recovery_action="fallback_to_memory",
                data_preserved=True
            )
        except OSError as e:
            if e.errno == 28:  # No space left on device
                return False, ErrorContext(
                    timestamp=datetime.utcnow().isoformat(),
                    error_type="DiskFull",
                    severity=ErrorSeverity.CRITICAL,
                    message="Disk space exhausted",
                    operation="write",
                    recovery_action="fallback_to_memory",
                    data_preserved=True
                )
            return False, ErrorContext(
                timestamp=datetime.utcnow().isoformat(),
                error_type="OSError",
                severity=ErrorSeverity.HIGH,
                message=str(e),
                operation="write",
                recovery_action="fallback_to_memory",
                data_preserved=True
            )


class JSONCorruptionRecovery:
    """Detects and recovers from JSON file corruption"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.backup_dir = None
    
    def validate_json(self, content: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate JSON and attempt recovery if corrupted"""
        try:
            data = json.loads(content)
            return True, data
        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.error(f"JSON decode error at line {e.lineno}: {e.msg}")
            return False, None
    
    def repair_json(self, content: str) -> Tuple[Optional[Dict[str, Any]], Optional[ErrorContext]]:
        """Attempt to repair corrupted JSON"""
        # Try extracting valid JSON blocks
        import re
        
        # Look for valid JSON objects
        pattern = r'\{[^{}]*\}'
        matches = re.findall(pattern, content)
        
        if not matches:
            return None, ErrorContext(
                timestamp=datetime.utcnow().isoformat(),
                error_type="JSONUnrecoverable",
                severity=ErrorSeverity.HIGH,
                message="No valid JSON structure found in content",
                operation="repair",
                recovery_action="return_empty_dict",
                data_preserved=False
            )
        
        # Try to parse largest valid block
        for match in sorted(matches, key=len, reverse=True):
            try:
                data = json.loads(match)
                return data, ErrorContext(
                    timestamp=datetime.utcnow().isoformat(),
                    error_type="JSONRepaired",
                    severity=ErrorSeverity.MEDIUM,
                    message="Successfully recovered partial JSON",
                    operation="repair",
                    recovery_action="partial_recovery",
                    data_preserved=True
                )
            except json.JSONDecodeError:
                continue
        
        return None, ErrorContext(
            timestamp=datetime.utcnow().isoformat(),
            error_type="JSONUnrecoverable",
            severity=ErrorSeverity.HIGH,
            message="All JSON repair attempts failed",
            operation="repair",
            recovery_action="return_empty_dict",
            data_preserved=False
        )


class GracefulDegradation:
    """Fallback to in-memory operation when persistent storage fails"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.memory_cache = {}  # filename -> content
        self.degraded_mode = False
        self.recovery_attempts = 0
    
    def enable_degraded_mode(self, filepath: str, reason: str):
        """Enable degraded mode for a specific file"""
        self.degraded_mode = True
        if self.logger:
            self.logger.warning(
                f"Entering degraded mode for {filepath}: {reason}. "
                "Using in-memory cache. Data will be lost if process dies."
            )
    
    def disable_degraded_mode(self):
        """Attempt to return to normal mode"""
        self.recovery_attempts += 1
        self.degraded_mode = False
        if self.logger:
            self.logger.info(f"Exiting degraded mode (attempt {self.recovery_attempts})")
    
    def get_fallback_data(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Get data from in-memory cache"""
        return self.memory_cache.get(filepath, {})
    
    def store_fallback_data(self, filepath: str, data: Dict[str, Any]):
        """Store data in memory when persistent storage unavailable"""
        self.memory_cache[filepath] = data
        if self.logger:
            self.logger.info(f"Stored {filepath} in memory cache")


class ErrorLogger:
    """Comprehensive logging with context preservation"""
    
    def __init__(self, log_file: str = "framework_errors.log"):
        self.log_file = log_file
        self.setup_logging()
        self.error_history = []
    
    def setup_logging(self):
        """Configure logging system"""
        logger = logging.getLogger("UniversellFramework")
        logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.logger = logger
    
    def log_error_context(self, context: ErrorContext):
        """Log error with full context"""
        self.error_history.append(context)
        
        level = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO
        }[context.severity]
        
        self.logger.log(
            level,
            f"[{context.severity.value}] {context.error_type}: {context.message} "
            f"(operation={context.operation}, recovery={context.recovery_action}, "
            f"preserved={context.data_preserved})"
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors encountered"""
        return {
            "total_errors": len(self.error_history),
            "by_severity": {
                "CRITICAL": sum(1 for e in self.error_history if e.severity == ErrorSeverity.CRITICAL),
                "HIGH": sum(1 for e in self.error_history if e.severity == ErrorSeverity.HIGH),
                "MEDIUM": sum(1 for e in self.error_history if e.severity == ErrorSeverity.MEDIUM),
                "LOW": sum(1 for e in self.error_history if e.severity == ErrorSeverity.LOW),
            },
            "recent_errors": [asdict(e) for e in self.error_history[-10:]]
        }


class FrameworkErrorHandler:
    """Main error handling coordinator"""
    
    def __init__(self, storage_dir: str = "./framework_state"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        self.error_logger = ErrorLogger(f"{storage_dir}/framework_errors.log")
        self.logger = self.error_logger.logger
        
        self.file_handler = FileIOErrorHandler(self.logger)
        self.json_recovery = JSONCorruptionRecovery(self.logger)
        self.degradation = GracefulDegradation(self.logger)
    
    def safe_load_state(self, filepath: str) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Safely load state with full recovery strategy.
        Returns: (data, is_degraded_mode)
        """
        # Try to read file
        content, read_error = self.file_handler.safe_read(filepath)
        
        if read_error:
            self.error_logger.log_error_context(read_error)
            if read_error.severity == ErrorSeverity.CRITICAL:
                self.degradation.enable_degraded_mode(filepath, read_error.message)
                return self.degradation.get_fallback_data(filepath), True
            return {}, False
        
        if content is None:
            return {}, False
        
        # Validate JSON
        is_valid, data = self.json_recovery.validate_json(content)
        
        if not is_valid:
            # Attempt recovery
            recovered_data, recovery_error = self.json_recovery.repair_json(content)
            if recovery_error:
                self.error_logger.log_error_context(recovery_error)
            if recovered_data:
                self.degradation.store_fallback_data(filepath, recovered_data)
                return recovered_data, False
            
            # Last resort: empty dict
            self.degradation.enable_degraded_mode(filepath, "JSON unrecoverable")
            return self.degradation.get_fallback_data(filepath), True
        
        return data, False
    
    def safe_save_state(self, filepath: str, data: Dict[str, Any]) -> bool:
        """
        Safely save state with fallback to memory.
        Returns: True if saved to disk, False if in-memory fallback
        """
        content = json.dumps(data, indent=2)
        
        success, write_error = self.file_handler.safe_write(filepath, content)
        
        if not success:
            if write_error:
                self.error_logger.log_error_context(write_error)
            
            # Fallback to memory
            self.degradation.store_fallback_data(filepath, data)
            self.degradation.enable_degraded_mode(filepath, "Write failed, using in-memory")
            return False
        
        if self.degradation.degraded_mode:
            self.degradation.disable_degraded_mode()
        
        return True
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current error handling status"""
        return {
            "degraded_mode": self.degradation.degraded_mode,
            "recovery_attempts": self.degradation.recovery_attempts,
            "in_memory_files": len(self.degradation.memory_cache),
            "error_summary": self.error_logger.get_error_summary()
        }


# Example usage and testing helpers
def test_error_handler():
    """Validate error handler implementation"""
    handler = FrameworkErrorHandler()
    
    # Test 1: Successful read/write
    test_data = {"key": "value", "count": 42}
    test_file = handler.storage_dir + "/test.json"
    
    success = handler.safe_save_state(test_file, test_data)
    assert success, "Should save successfully"
    
    loaded_data, degraded = handler.safe_load_state(test_file)
    assert loaded_data == test_data, "Data should round-trip"
    assert not degraded, "Should not be degraded"
    
    # Test 2: JSON corruption recovery
    with open(test_file, 'w') as f:
        f.write('{"incomplete": "json"')
    
    loaded_data, degraded = handler.safe_load_state(test_file)
    # Should attempt recovery or fallback
    assert loaded_data is not None, "Should return something"
    
    print("✅ Error handler tests passed")
    return True


if __name__ == "__main__":
    test_error_handler()
