"""
PHASE 7: SECURITY & RATE LIMITING
Day 10 Part 2 - Production-Ready Security Hardening

Implements:
- Rate limiting (1000 req/min default, configurable)
- Audit logging (who did what, when)
- API key authentication
- Request validation
- Security context tracking

Architecture:
1. RateLimiter - token bucket algorithm
2. AuditLogger - comprehensive security audit trail
3. SecurityContext - request authentication/authorization
4. RequestValidator - input validation
"""

import time
import hashlib
import hmac
import secrets
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class ActionType(Enum):
    """Types of auditable actions"""
    BLOCK_CREATE = "BLOCK_CREATE"
    APPROVAL_GRANT = "APPROVAL_GRANT"
    APPROVAL_DENY = "APPROVAL_DENY"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    AUTH_FAILURE = "AUTH_FAILURE"
    RATE_LIMIT = "RATE_LIMIT"
    DATA_ACCESS = "DATA_ACCESS"


@dataclass
class AuditEntry:
    """Single audit log entry"""
    timestamp: str
    action: ActionType
    actor: str  # Who performed action
    resource: str  # What was affected
    result: str  # What happened (success/failure)
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, requests_per_minute: int = 1000):
        self.capacity = requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        
        # Per-client tracking
        self.buckets = defaultdict(lambda: {"tokens": self.capacity, "last_refill": time.time()})
        self.lock = threading.Lock()
        
        # Metrics
        self.total_requests = 0
        self.rejected_requests = 0
    
    def _refill_tokens(self, client_id: str):
        """Refill tokens based on elapsed time"""
        bucket = self.buckets[client_id]
        now = time.time()
        elapsed = now - bucket["last_refill"]
        
        new_tokens = elapsed * self.refill_rate
        bucket["tokens"] = min(
            self.capacity,
            bucket["tokens"] + new_tokens
        )
        bucket["last_refill"] = now
    
    def allow_request(self, client_id: str, tokens_needed: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed under rate limit"""
        with self.lock:
            self.total_requests += 1
            
            # Refill tokens first
            self._refill_tokens(client_id)
            
            bucket = self.buckets[client_id]
            
            if bucket["tokens"] >= tokens_needed:
                bucket["tokens"] -= tokens_needed
                return True, {
                    "allowed": True,
                    "remaining_tokens": int(bucket["tokens"]),
                    "capacity": self.capacity
                }
            else:
                self.rejected_requests += 1
                # Calculate retry-after seconds
                tokens_short = tokens_needed - bucket["tokens"]
                retry_after = tokens_short / self.refill_rate
                
                return False, {
                    "allowed": False,
                    "remaining_tokens": int(bucket["tokens"]),
                    "retry_after_seconds": retry_after,
                    "capacity": self.capacity
                }
    
    def get_client_status(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit status for client"""
        with self.lock:
            self._refill_tokens(client_id)
            bucket = self.buckets[client_id]
            
            return {
                "client_id": client_id,
                "tokens_available": int(bucket["tokens"]),
                "capacity": self.capacity,
                "rejection_rate": self.rejected_requests / max(1, self.total_requests)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        with self.lock:
            return {
                "total_requests": self.total_requests,
                "rejected_requests": self.rejected_requests,
                "acceptance_rate": 1.0 - (self.rejected_requests / max(1, self.total_requests)),
                "active_clients": len(self.buckets)
            }
    
    def reset_stats(self):
        """Reset statistics"""
        with self.lock:
            self.total_requests = 0
            self.rejected_requests = 0


class AuditLogger:
    """Comprehensive security audit trail"""
    
    def __init__(self, max_entries: int = 100000):
        self.audit_log = deque(maxlen=max_entries)
        self.lock = threading.Lock()
        
        # Metrics
        self.action_counts = defaultdict(int)
        self.risk_summary = defaultdict(int)
    
    def log_action(self,
                   action: ActionType,
                   actor: str,
                   resource: str,
                   result: str,
                   details: Dict[str, Any] = None,
                   ip_address: Optional[str] = None,
                   risk_level: str = "LOW") -> AuditEntry:
        """Log an action to audit trail"""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            action=action,
            actor=actor,
            resource=resource,
            result=result,
            details=details or {},
            ip_address=ip_address,
            risk_level=risk_level
        )
        
        with self.lock:
            self.audit_log.append(entry)
            self.action_counts[action.value] += 1
            self.risk_summary[risk_level] += 1
        
        return entry
    
    def get_audit_trail(self,
                       actor: Optional[str] = None,
                       action: Optional[ActionType] = None,
                       hours: int = 24) -> List[AuditEntry]:
        """Query audit log"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with self.lock:
            results = []
            for entry in self.audit_log:
                if datetime.fromisoformat(entry.timestamp) < cutoff:
                    continue
                if actor and entry.actor != actor:
                    continue
                if action and entry.action != action:
                    continue
                results.append(entry)
            
            return results
    
    def get_high_risk_activities(self, hours: int = 24) -> List[AuditEntry]:
        """Get high-risk activities"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with self.lock:
            return [
                e for e in self.audit_log
                if e.risk_level in ["HIGH", "CRITICAL"] and
                   datetime.fromisoformat(e.timestamp) > cutoff
            ]
    
    def get_actor_summary(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get summary of actions per actor"""
        trail = self.get_audit_trail(hours=hours)
        summary = defaultdict(lambda: {"actions": 0, "failures": 0, "high_risk": 0})
        
        for entry in trail:
            summary[entry.actor]["actions"] += 1
            if entry.result == "failure":
                summary[entry.actor]["failures"] += 1
            if entry.risk_level in ["HIGH", "CRITICAL"]:
                summary[entry.actor]["high_risk"] += 1
        
        return dict(summary)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        with self.lock:
            return {
                "total_entries": len(self.audit_log),
                "action_counts": dict(self.action_counts),
                "risk_summary": dict(self.risk_summary),
                "high_risk_count": self.risk_summary.get("HIGH", 0) + self.risk_summary.get("CRITICAL", 0)
            }


class SecurityContext:
    """Request security context and authentication"""
    
    def __init__(self):
        self.api_keys = {}  # key -> metadata
        self.sessions = {}  # session_id -> expiry
        self.lock = threading.Lock()
    
    def generate_api_key(self, name: str, permissions: List[str] = None) -> str:
        """Generate API key with metadata"""
        api_key = f"sk_{secrets.token_hex(32)}"
        
        with self.lock:
            self.api_keys[api_key] = {
                "name": name,
                "created": datetime.utcnow().isoformat(),
                "permissions": permissions or [],
                "active": True,
                "last_used": None
            }
        
        return api_key
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key"""
        with self.lock:
            if api_key in self.api_keys:
                self.api_keys[api_key]["active"] = False
                return True
            return False
    
    def validate_api_key(self, api_key: str, required_permissions: List[str] = None) -> Tuple[bool, Optional[str]]:
        """Validate API key and permissions"""
        with self.lock:
            if api_key not in self.api_keys:
                return False, "Invalid API key"
            
            key_info = self.api_keys[api_key]
            
            if not key_info["active"]:
                return False, "API key revoked"
            
            if required_permissions:
                key_perms = set(key_info["permissions"])
                required = set(required_permissions)
                if not required.issubset(key_perms):
                    return False, f"Missing permissions: {required - key_perms}"
            
            # Update last_used
            self.api_keys[api_key]["last_used"] = datetime.utcnow().isoformat()
            
            return True, None
    
    def get_api_keys_summary(self) -> Dict[str, Any]:
        """Get API keys summary (for admin)"""
        with self.lock:
            return {
                "total_keys": len(self.api_keys),
                "active_keys": sum(1 for k in self.api_keys.values() if k["active"]),
                "revoked_keys": sum(1 for k in self.api_keys.values() if not k["active"])
            }


class RequestValidator:
    """Input validation for security"""
    
    @staticmethod
    def validate_json_structure(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate JSON against schema"""
        for key, expected_type in schema.items():
            if key not in data:
                return False, f"Missing required field: {key}"
            
            if not isinstance(data[key], expected_type):
                return False, f"Field {key} has wrong type: expected {expected_type.__name__}, got {type(data[key]).__name__}"
        
        return True, None
    
    @staticmethod
    def validate_string_length(value: str, min_len: int = 1, max_len: int = 1000) -> Tuple[bool, Optional[str]]:
        """Validate string length"""
        if len(value) < min_len:
            return False, f"String too short: minimum {min_len}"
        if len(value) > max_len:
            return False, f"String too long: maximum {max_len}"
        return True, None
    
    @staticmethod
    def validate_ip_address(ip: str) -> Tuple[bool, Optional[str]]:
        """Validate IP address format"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False, "Invalid IPv4 address"
        
        try:
            for part in parts:
                num = int(part)
                if not (0 <= num <= 255):
                    return False, "IP octets must be 0-255"
        except ValueError:
            return False, "IP parts must be numeric"
        
        return True, None


class SecurityManager:
    """Main security coordinator"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=1000)
        self.audit_logger = AuditLogger()
        self.security_context = SecurityContext()
        self.validator = RequestValidator()
    
    def authenticate_request(self, api_key: str, client_ip: str) -> Tuple[bool, Optional[str]]:
        """Authenticate incoming request"""
        # Validate API key
        valid, msg = self.security_context.validate_api_key(api_key)
        if not valid:
            self.audit_logger.log_action(
                ActionType.AUTH_FAILURE,
                actor="unknown",
                resource="api_access",
                result="failure",
                details={"reason": msg},
                ip_address=client_ip,
                risk_level="MEDIUM"
            )
            return False, msg
        
        # Check rate limit
        allowed, rate_info = self.rate_limiter.allow_request(client_ip)
        if not allowed:
            self.audit_logger.log_action(
                ActionType.RATE_LIMIT,
                actor=api_key,
                resource="rate_limit",
                result="blocked",
                details=rate_info,
                ip_address=client_ip,
                risk_level="LOW"
            )
            return False, f"Rate limit exceeded. Retry after {rate_info['retry_after_seconds']:.1f}s"
        
        return True, None
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get overall security status"""
        return {
            "rate_limiter": self.rate_limiter.get_stats(),
            "api_keys": self.security_context.get_api_keys_summary(),
            "audit": self.audit_logger.get_statistics(),
            "high_risk_activities": len(self.audit_logger.get_high_risk_activities(hours=24))
        }


# Testing
def test_security():
    """Validate security implementation"""
    manager = SecurityManager()
    
    # Test 1: Generate and validate API key
    api_key = manager.security_context.generate_api_key("test_app", ["read", "write"])
    valid, msg = manager.security_context.validate_api_key(api_key, ["read"])
    assert valid, "API key should be valid"
    
    # Test 2: Rate limiting
    for i in range(100):
        allowed, _ = manager.rate_limiter.allow_request("client1")
        assert allowed, f"Request {i} should be allowed"
    
    # Test 3: Audit logging
    manager.audit_logger.log_action(
        ActionType.BLOCK_CREATE,
        actor="test_user",
        resource="block_123",
        result="success",
        risk_level="LOW"
    )
    
    trail = manager.audit_logger.get_audit_trail(actor="test_user")
    assert len(trail) > 0, "Should have audit entries"
    
    # Test 4: Authentication
    valid, msg = manager.authenticate_request(api_key, "192.168.1.1")
    assert valid, f"Authentication should succeed: {msg}"
    
    print("✅ Security tests passed")
    return True


if __name__ == "__main__":
    test_security()
