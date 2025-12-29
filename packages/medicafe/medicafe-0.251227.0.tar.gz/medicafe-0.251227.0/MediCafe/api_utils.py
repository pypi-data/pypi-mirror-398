# MediLink_api_utils.py
# Enhanced API utilities for circuit breaker, caching, and rate limiting
# Extracted from enhanced implementations for safe production integration
# Python 3.4.4 compatible implementation

import time

# Use core utilities for standardized imports
from MediCafe.core_utils import get_shared_config_loader
MediLink_ConfigLoader = get_shared_config_loader()

# CRITICAL: Ensure MediLink_ConfigLoader is available - this module requires it
if MediLink_ConfigLoader is None:
    raise ImportError(
        "[api_utils] CRITICAL: MediLink_ConfigLoader module import failed. "
        "This module requires MediLink_ConfigLoader to function. "
        "Check PYTHONPATH, module dependencies, and ensure MediCafe package is properly installed."
    )

# Token cache for API authentication
class TokenCache:
    """Token cache for API authentication"""
    def __init__(self):
        self.tokens = {}

    def get(self, endpoint_name, current_time):
        """Get cached token if valid"""
        token_info = self.tokens.get(endpoint_name, {})
        if token_info:
            expires_at = token_info['expires_at']
            # Log cache hit and expiration time
            log_message = "Token for {} expires at {}. Current time: {}".format(endpoint_name, expires_at, current_time)
            MediLink_ConfigLoader.log(log_message, level="DEBUG")

            if expires_at > current_time:
                time_remaining = expires_at - current_time
                MediLink_ConfigLoader.log(
                    "Using cached token for {} (valid for {:.1f} more seconds)".format(endpoint_name, time_remaining),
                    level="DEBUG"
                )
                return token_info['access_token']
            else:
                # Token expired in cache
                time_expired = current_time - expires_at
                MediLink_ConfigLoader.log(
                    "Cached token for {} expired {} seconds ago".format(endpoint_name, time_expired),
                    level="INFO"
                )

        # Log cache miss (no token or expired)
        if not token_info:
            MediLink_ConfigLoader.log("No valid token found for {} (no token in cache)".format(endpoint_name), level="INFO")
        return None

    def set(self, endpoint_name, access_token, expires_in, current_time):
        """Set cached token with expiration"""
        # Ensure numeric types
        if isinstance(current_time, str):
            try:
                current_time = float(current_time)
            except ValueError:
                raise ValueError("Cannot convert current_time to numeric type")
        
        if isinstance(expires_in, str):
            try:
                expires_in = float(expires_in)
            except ValueError:
                raise ValueError("Cannot convert expires_in to numeric type")

        # Log the expires_in value to debug
        log_message = "Token expires in: {} seconds for {}".format(expires_in, endpoint_name)
        MediLink_ConfigLoader.log(log_message, level="INFO")

        # Adjust expiration time by subtracting a buffer of 120 seconds
        expires_at = current_time + expires_in - 120
        log_message = "Setting token for {}. Expires at: {}".format(endpoint_name, expires_at)
        MediLink_ConfigLoader.log(log_message, level="INFO")

        self.tokens[endpoint_name] = {
            'access_token': access_token,
            'expires_at': expires_at
        }

    def clear(self, endpoint_name, reason="unspecified"):
        """Clear cached token for a specific endpoint"""
        if endpoint_name in self.tokens:
            token_info = self.tokens[endpoint_name]
            expires_at = token_info.get('expires_at', 'unknown')
            current_time = time.time()
            time_remaining = expires_at - current_time if isinstance(expires_at, (int, float)) else 'unknown'
            del self.tokens[endpoint_name]
            MediLink_ConfigLoader.log(
                "Cleared token cache for endpoint: {} (reason: {}, was valid for {} more seconds)".format(
                    endpoint_name, reason, time_remaining),
                level="INFO"
            )

# Circuit breaker pattern for API resilience
class APICircuitBreaker:
    """Circuit breaker pattern for API resilience"""
    def __init__(self, failure_threshold=5, timeout=300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self):
        """Check if circuit breaker allows execution"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
                MediLink_ConfigLoader.log("Circuit breaker moving to HALF_OPEN state", level="INFO")
                return True
            else:
                return False
        return True
    
    def record_success(self):
        """Record successful API call"""
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            self.failure_count = 0
            MediLink_ConfigLoader.log("Circuit breaker reset to CLOSED state", level="INFO")
    
    def record_failure(self):
        """Record failed API call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            MediLink_ConfigLoader.log("Circuit breaker OPENED due to {} failures".format(self.failure_count), level="ERROR")
    
    def call_with_breaker(self, api_function, *args, **kwargs):
        """Call API function with circuit breaker protection"""
        if not self.can_execute():
            raise Exception("API circuit breaker is OPEN - too many failures")
        
        try:
            result = api_function(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise e

# Cache for API responses to reduce redundant calls
class APICache:
    """Simple time-based cache for API responses"""
    def __init__(self, cache_duration=3600):  # 1 hour cache
        self.cache = {}
        self.cache_duration = cache_duration
    
    def _generate_cache_key(self, *args, **kwargs):
        """Generate cache key from function arguments"""
        key_parts = []
        for arg in args:
            key_parts.append(str(arg))
        for k, v in sorted(kwargs.items()):
            key_parts.append("{}:{}".format(k, v))
        return "|".join(key_parts)
    
    def get(self, *args, **kwargs):
        """Get cached result if available and not expired"""
        cache_key = self._generate_cache_key(*args, **kwargs)
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_duration:
                MediLink_ConfigLoader.log("Cache hit for key: {}".format(cache_key[:50]), level="DEBUG")
                return cached_data['result']
        return None
    
    def set(self, result, *args, **kwargs):
        """Cache result"""
        cache_key = self._generate_cache_key(*args, **kwargs)
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
        MediLink_ConfigLoader.log("Cached result for key: {}".format(cache_key[:50]), level="DEBUG")
    
    def clear_expired(self):
        """Remove expired cache entries"""
        now = time.time()
        expired_keys = []
        for key, data in self.cache.items():
            if now - data['timestamp'] >= self.cache_duration:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            MediLink_ConfigLoader.log("Cleared {} expired cache entries".format(len(expired_keys)), level="DEBUG")

# Rate limiter to prevent API overload
class APIRateLimiter:
    """Rate limiter to prevent API overload"""
    def __init__(self, max_calls_per_minute=60):
        self.max_calls = max_calls_per_minute
        self.calls = []
    
    def can_make_call(self):
        """Check if we can make another API call within rate limits"""
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        can_call = len(self.calls) < self.max_calls
        if not can_call:
            MediLink_ConfigLoader.log("Rate limit reached: {} calls in last minute".format(len(self.calls)), level="WARNING")
        return can_call
    
    def record_call(self):
        """Record that an API call was made"""
        self.calls.append(time.time())
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        if not self.can_make_call():
            # Wait until oldest call expires
            if self.calls:
                wait_time = 60 - (time.time() - self.calls[0])
                if wait_time > 0:
                    MediLink_ConfigLoader.log("Rate limit reached, waiting {:.1f} seconds".format(wait_time), level="INFO")
                    time.sleep(wait_time)

# Enhanced API client wrapper
class EnhancedAPIWrapper:
    """Wrapper that adds circuit breaker, caching, and rate limiting to any API client"""
    
    def __init__(self, base_client, enable_circuit_breaker=True, enable_caching=True, enable_rate_limiting=True):
        self.base_client = base_client
        
        # Initialize enhancement components
        self.circuit_breaker = APICircuitBreaker() if enable_circuit_breaker else None
        self.cache = APICache() if enable_caching else None
        self.rate_limiter = APIRateLimiter() if enable_rate_limiting else None
        
        MediLink_ConfigLoader.log("Enhanced API wrapper initialized with circuit_breaker={}, caching={}, rate_limiting={}".format(
            enable_circuit_breaker, enable_caching, enable_rate_limiting), level="INFO")
    
    def make_enhanced_call(self, method_name, *args, **kwargs):
        """Make API call with all enhancements applied"""
        # Check cache first
        if self.cache:
            cached_result = self.cache.get(method_name, *args, **kwargs)
            if cached_result is not None:
                return cached_result
        
        # Check rate limits
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()
        
        # Get the method from base client
        if not hasattr(self.base_client, method_name):
            raise AttributeError("Base client does not have method: {}".format(method_name))
        
        method = getattr(self.base_client, method_name)
        
        # Execute with circuit breaker protection
        if self.circuit_breaker:
            result = self.circuit_breaker.call_with_breaker(method, *args, **kwargs)
        else:
            result = method(*args, **kwargs)
        
        # Record rate limit call
        if self.rate_limiter:
            self.rate_limiter.record_call()
        
        # Cache result
        if self.cache:
            self.cache.set(result, method_name, *args, **kwargs)
        
        return result

# Utility functions for API enhancement integration
def create_enhanced_api_client(base_client_class, *args, **kwargs):
    """
    Factory function to create enhanced API client from base client class.
    Returns base client wrapped with enhancements.
    """
    try:
        # Create base client
        base_client = base_client_class(*args, **kwargs)
        
        # Wrap with enhancements
        enhanced_client = EnhancedAPIWrapper(base_client)
        
        MediLink_ConfigLoader.log("Created enhanced API client from {}".format(base_client_class.__name__), level="INFO")
        return enhanced_client
        
    except Exception as e:
        MediLink_ConfigLoader.log("Failed to create enhanced API client: {}".format(str(e)), level="ERROR")
        # Return base client as fallback
        return base_client_class(*args, **kwargs)

def safe_api_call(api_function, *args, **kwargs):
    """
    Safe wrapper for any API call with error handling and fallback.
    Returns (result, success_flag, error_message)
    """
    try:
        result = api_function(*args, **kwargs)
        return result, True, None
    except Exception as e:
        error_msg = str(e)
        MediLink_ConfigLoader.log("API call failed: {}".format(error_msg), level="ERROR")
        return None, False, error_msg

def validate_api_response(response, required_fields=None):
    """
    Validate API response has required structure and fields.
    Returns True if valid, False otherwise.
    """
    if not response:
        return False
    
    if required_fields:
        for field in required_fields:
            if field not in response:
                MediLink_ConfigLoader.log("Missing required field in API response: {}".format(field), level="WARNING")
                return False
    
    return True

# API health monitoring
class APIHealthMonitor:
    """Monitor API health and performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'cache_hits': 0,
            'circuit_breaker_trips': 0,
            'rate_limit_hits': 0,
            'start_time': time.time()
        }
    
    def record_call(self, success=True):
        """Record API call outcome"""
        self.metrics['total_calls'] += 1
        if success:
            self.metrics['successful_calls'] += 1
        else:
            self.metrics['failed_calls'] += 1
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics['cache_hits'] += 1
    
    def record_circuit_breaker_trip(self):
        """Record circuit breaker trip"""
        self.metrics['circuit_breaker_trips'] += 1
    
    def record_rate_limit_hit(self):
        """Record rate limit hit"""
        self.metrics['rate_limit_hits'] += 1
    
    def get_health_summary(self):
        """Get health summary statistics"""
        total_calls = self.metrics['total_calls']
        if total_calls == 0:
            return {'status': 'NO_CALLS', 'metrics': self.metrics}
        
        success_rate = self.metrics['successful_calls'] / float(total_calls)
        cache_hit_rate = self.metrics['cache_hits'] / float(total_calls)
        
        runtime = time.time() - self.metrics['start_time']
        calls_per_minute = (total_calls / runtime) * 60 if runtime > 0 else 0
        
        summary = {
            'status': 'HEALTHY' if success_rate > 0.95 else 'DEGRADED' if success_rate > 0.80 else 'UNHEALTHY',
            'success_rate': success_rate,
            'cache_hit_rate': cache_hit_rate,
            'calls_per_minute': calls_per_minute,
            'runtime_seconds': runtime,
            'metrics': self.metrics
        }
        
        MediLink_ConfigLoader.log("API Health Summary: {}".format(str(summary)), level="INFO")
        return summary

# Global API health monitor instance
_global_health_monitor = APIHealthMonitor()

def get_api_health_monitor():
    """Get global API health monitor instance"""
    return _global_health_monitor