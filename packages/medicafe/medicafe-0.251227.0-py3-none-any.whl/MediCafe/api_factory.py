#!/usr/bin/env python
"""
Production API Client Factory - Python 3.4.4 Compatible
Unified factory for all API operations using MediCafe api_core as the foundation.

COMPATIBILITY: Python 3.4.4 and Windows XP compatible
STRATEGY: v3-only implementation with v2 deprecation handling
"""

import os
import sys
import time

# Direct imports from MediCafe package (simplified since we're in the same package)
try:
    from .api_core import APIClient as ProductionAPIClient
    PRODUCTION_AVAILABLE = True
except ImportError:
    try:
        # Fallback for when running as standalone module
        from .api_core import APIClient as ProductionAPIClient
        PRODUCTION_AVAILABLE = True
    except ImportError:
        PRODUCTION_AVAILABLE = False
        class ProductionAPIClient:
            def __init__(self):
                pass

# Use core utilities for standardized imports
try:
    from .core_utils import get_shared_config_loader
    MediLink_ConfigLoader = get_shared_config_loader()
    if MediLink_ConfigLoader is None:
        raise ImportError("MediLink_ConfigLoader not available")
except ImportError:
    try:
        # Fallback for when running as standalone module
        from MediCafe.core_utils import get_shared_config_loader
        MediLink_ConfigLoader = get_shared_config_loader()
        if MediLink_ConfigLoader is None:
            raise ImportError("MediLink_ConfigLoader not available")
    except ImportError:
        # Fallback for when core_utils is not available
        class MediLink_ConfigLoader:
            @staticmethod
            def log(message, level="INFO"):
                print("[{}] {}".format(level, message))

# Hardcoded configuration with reasonable defaults
DEFAULT_FACTORY_CONFIG = {
    'default_version': 'v3',
    'fallback_enabled': False,  # v2 deprecated
    'circuit_breaker': {
        'failure_threshold': 5,
        'recovery_timeout': 30
    },
    'deprecation_warnings': {
        'v2_warning_shown': False
    }
}

class FactoryCircuitBreaker:
    """
    Circuit breaker for factory-level reliability.
    Python 3.4.4 compatible implementation.
    """
    
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception("API Factory Circuit Breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
    
    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failure and potentially open circuit breaker."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            MediLink_ConfigLoader.log("Circuit breaker OPENED after {} failures".format(self.failure_count), level="WARNING")

class APIClientFactory:
    """
    Production-ready API client factory focused on api_core.
    
    Features:
    - Unified access point for all API operations
    - Configuration-driven behavior (with hardcoded defaults)
    - Circuit breaker reliability
    - Payer-specific optimizations
    - Deprecation management for v2
    
    Python 3.4.4 and Windows XP compatible.
    """
    
    _shared_client = None
    _factory_config = None
    
    @classmethod
    def _load_factory_config(cls):
        """Load factory configuration with hardcoded defaults."""
        if cls._factory_config is not None:
            return cls._factory_config
        
        # Use hardcoded defaults only
        cls._factory_config = DEFAULT_FACTORY_CONFIG.copy()
        MediLink_ConfigLoader.log("Factory using hardcoded configuration", level="DEBUG")
        
        return cls._factory_config
    
    def __init__(self, config=None):
        self.config = config or self._load_factory_config()
        self.circuit_breaker = FactoryCircuitBreaker(
            failure_threshold=self.config['circuit_breaker']['failure_threshold'],
            recovery_timeout=self.config['circuit_breaker']['recovery_timeout']
        )
        self._warn_about_deprecations()
    
    def _warn_about_deprecations(self):
        """Show deprecation warnings for legacy API versions."""
        # v2 has been archived - no longer needed
        pass
    
    def get_client(self, version='v3', **kwargs):
        """
        Get API client with reliable creation and error handling.
        
        Args:
            version (str): API version ('v3' only, 'v2' is archived and unavailable)
            **kwargs: Additional parameters
            
        Returns:
            APIClient: Configured v3 API client instance
        """
        # Handle archived version requests
        if version == 'v2':
            raise ValueError("API v2 has been archived and is no longer available. Use v3 instead.")
        elif version not in ['v3', 'auto']:
            MediLink_ConfigLoader.log(
                "WARNING: Unknown API version '{}' requested. Using v3.".format(version), 
                level="WARNING"
            )
            version = 'v3'
        
        # Use circuit breaker for client creation
        def create_client():
            if not PRODUCTION_AVAILABLE:
                MediLink_ConfigLoader.log("Production APIClient not available, using fallback", level="WARNING")
                return ProductionAPIClient()
            
            client = ProductionAPIClient()
            MediLink_ConfigLoader.log("Created v3 API client via factory", level="DEBUG")
            
            return client
        
        # XP/Python34 Compatibility: Wrap circuit breaker call with error handling
        try:
            if self.circuit_breaker and hasattr(self.circuit_breaker, 'call'):
                return self.circuit_breaker.call(create_client)
            else:
                MediLink_ConfigLoader.log("Circuit breaker not available, calling create_client directly", level="WARNING")
                return create_client()
        except Exception as e:
            MediLink_ConfigLoader.log("Circuit breaker call failed: {}. Falling back to direct client creation.".format(str(e)), level="WARNING")
            print("Warning: Circuit breaker error ({}), using fallback client creation".format(str(e)))
            try:
                return create_client()
            except Exception as e2:
                MediLink_ConfigLoader.log("Direct client creation also failed: {}".format(str(e2)), level="ERROR")
                print("Error: Both circuit breaker and direct client creation failed: {}".format(str(e2)))
                # Return a minimal fallback client
                return ProductionAPIClient()
    
    @classmethod
    def get_shared_client(cls, **kwargs):
        """
        Get shared API client for operations that benefit from token caching.
        """
        if cls._shared_client is None:
            factory = cls()
            cls._shared_client = factory.get_client(**kwargs)
            MediLink_ConfigLoader.log("Initialized shared v3 API client via factory", level="INFO")
        
        return cls._shared_client
    
    @classmethod
    def reset_shared_client(cls):
        """Reset shared client for testing and configuration changes."""
        cls._shared_client = None
        cls._factory_config = None
        MediLink_ConfigLoader.log("Factory shared client reset", level="DEBUG")
    
    def make_request(self, endpoint, data=None, method='POST', **kwargs):
        """
        Make API request through factory.
        
        Args:
            endpoint (str): API endpoint
            data (dict): Request data
            method (str): HTTP method
            **kwargs: Additional request parameters
            
        Returns:
            dict: API response data
        """
        client = self.get_client()
        
        # Delegate to client's make_api_call method
        if hasattr(client, 'make_api_call'):
            return client.make_api_call(endpoint, method, data=data, **kwargs)
        else:
            raise NotImplementedError("Client does not support make_api_call method")
    
    def make_batch_request(self, requests_data, **kwargs):
        """
        Process multiple API requests efficiently.
        
        Args:
            requests_data (list): List of request dictionaries
            **kwargs: Additional parameters
            
        Returns:
            list: List of response data
        """
        client = self.get_client()
        
        # Process requests individually
        results = []
        for request in requests_data:
            try:
                result = self.make_request(
                    request.get('endpoint'),
                    request.get('data'),
                    request.get('method', 'POST'),
                    **kwargs
                )
                results.append(result)
            except Exception as e:
                MediLink_ConfigLoader.log("Batch request failed: {}".format(e), level="ERROR")
                results.append({'error': str(e)})
        
        return results

# Convenience functions for backward compatibility
def APIClient(**kwargs):
    """
    Drop-in replacement for existing APIClient() calls.
    
    Returns shared v3 client via factory for token caching benefits.
    """
    return APIClientFactory.get_shared_client(**kwargs)

def create_fresh_api_client(**kwargs):
    """Create independent API client when shared state is not desired."""
    factory = APIClientFactory()
    return factory.get_client(**kwargs)

def reset_api_client():
    """Reset shared client (primarily for testing)."""
    APIClientFactory.reset_shared_client()

# Factory instance getter for core_utils integration
def get_factory_instance():
    """Get factory instance for core utilities integration."""
    return APIClientFactory()

if __name__ == "__main__":
    print("API Client Factory - Production Implementation (Python 3.4.4 Compatible)")
    print("=" * 70)
    
    try:
        # Test factory creation
        factory = APIClientFactory()
        print("Factory created successfully")
        
        # Test client creation
        client = factory.get_client()
        print("v3 client created: {}".format(type(client)))
        
        # Test shared client
        shared_client = APIClientFactory.get_shared_client()
        print("Shared client available: {}".format(type(shared_client)))
        
        # Test deprecation handling
        deprecated_client = factory.get_client(version='v2')
        print("Deprecation handling working")
        
        # Test circuit breaker
        print("Circuit breaker threshold: {}".format(factory.circuit_breaker.failure_threshold))
        
        print("\nAll factory functionality validated")
        
    except Exception as e:
        print("Factory validation failed: {}".format(e)) 