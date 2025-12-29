# MediCafe/api_core.py
"""
Core API functionality for MediCafe.
Moved from MediLink to centralize shared API operations.

COMPATIBILITY: Python 3.4.4 and Windows XP compatible
"""

import time, json, os, traceback, sys

# Import centralized logging configuration
try:
    from MediCafe.logging_config import DEBUG, CONSOLE_LOGGING
except ImportError:
    # Fallback to local flags if centralized config is not available
    DEBUG = False
    CONSOLE_LOGGING = False

# Set up project paths first
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    import yaml
except ImportError:
    yaml = None
try:
    import requests
except ImportError:
    requests = None

# Use core utilities for standardized imports
try:
    from MediCafe.core_utils import get_shared_config_loader
    MediLink_ConfigLoader = get_shared_config_loader()
except ImportError:
    try:
        from .core_utils import get_shared_config_loader
        MediLink_ConfigLoader = get_shared_config_loader()
    except ImportError:
        # Fallback to direct import
        from MediCafe.MediLink_ConfigLoader import MediLink_ConfigLoader

# CRITICAL: Ensure MediLink_ConfigLoader is available - this module requires it
if MediLink_ConfigLoader is None:
    raise ImportError(
        "[api_core] CRITICAL: MediLink_ConfigLoader module import failed. "
        "This module requires MediLink_ConfigLoader to function. "
        "Check PYTHONPATH, module dependencies, and ensure MediCafe package is properly installed."
    )

try:
    from MediCafe.network_route_helpers import handle_route_mismatch_404
except ImportError:
    def handle_route_mismatch_404(*args, **kwargs):
        return


try:
    from MediCafe import graphql_utils as MediLink_GraphQL
except ImportError:
    try:
        from MediLink import MediLink_GraphQL
    except ImportError:
        try:
            import graphql_utils as MediLink_GraphQL
        except ImportError:
            # Create a dummy module if graphql_utils is not available
            # BUG (minimally fixed): When graphql_utils is unavailable, DummyGraphQL
            # lacked OPTUMAI claims inquiry helpers used by get_claim_summary_by_provider.
            # Minimal fix implemented elsewhere: a capability guard disables OPTUMAI when
            # these methods are missing so fallback to UHCAPI proceeds without AttributeError.
            # Recommended next steps:
            # - Provide explicit no-op stubs here that raise NotImplementedError for clarity.
            # - Add a small shim that always exposes required methods to decouple import shapes.
            # - Add a config feature flag to enable/disable OPTUMAI claims inquiry.
            # - Add environment-based guard (dev/test default off) and metrics counter for use.
            # - Add unit tests for both capability-present and capability-absent paths.
            class DummyGraphQL:
                @staticmethod
                def transform_eligibility_response(response):
                    return response
            MediLink_GraphQL = DummyGraphQL()

"""
TODO At some point it might make sense to test their acknoledgment endpoint. body is transactionId.
This API is used to extract the claim acknowledgement details for the given transactionid which was 
generated for 837 requests in claim submission process. Claims Acknowledgement (277CA) will provide 
a status of claim-level acknowledgement of all claims received in the front-end processing system and 
adjudication system.
"""

class ConfigLoader:
    @staticmethod
    def load_configuration(config_path=os.path.join(os.path.dirname(__file__), '..', 'json', 'config.json'), 
                           crosswalk_path=os.path.join(os.path.dirname(__file__), '..', 'json', 'crosswalk.json')):
        return MediLink_ConfigLoader.load_configuration(config_path, crosswalk_path)

    @staticmethod
    def load_swagger_file(swagger_path):
        try:
            print("Attempting to load Swagger file: {}".format(swagger_path))
            with open(swagger_path, 'r') as swagger_file:
                if swagger_path.endswith('.yaml') or swagger_path.endswith('.yml'):
                    if yaml is None:
                        print("YAML parsing not available (PyYAML not installed). Please install PyYAML or provide a JSON Swagger file.")
                        return None
                    print("Parsing YAML file: {}".format(swagger_path))
                    swagger_data = yaml.safe_load(swagger_file)
                elif swagger_path.endswith('.json'):
                    print("Parsing JSON file: {}".format(swagger_path))
                    swagger_data = json.load(swagger_file)
                else:
                    raise ValueError("Unsupported Swagger file format.")
            print("Successfully loaded Swagger file: {}".format(swagger_path))
            return swagger_data
        except ValueError as e:
            print("Error parsing Swagger file {}: {}".format(swagger_path, e))
            MediLink_ConfigLoader.log("Error parsing Swagger file {}: {}".format(swagger_path, e), level="ERROR")
        except FileNotFoundError:
            print("Swagger file not found: {}".format(swagger_path))
            MediLink_ConfigLoader.log("Swagger file not found: {}".format(swagger_path), level="ERROR")
        except Exception as e:
            print("Unexpected error loading Swagger file {}: {}".format(swagger_path, e))
            MediLink_ConfigLoader.log("Unexpected error loading Swagger file {}: {}".format(swagger_path, e), level="ERROR")
        return None

# Function to ensure numeric type
def ensure_numeric(value):
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            raise ValueError("Cannot convert {} to a numeric type".format(value))
    return value

# Import utilities from api_utils
try:
    from MediCafe.api_utils import TokenCache
except ImportError:
    # Fallback if api_utils is not available
    class TokenCache:
        def __init__(self):
            self.tokens = {}

# -----------------------------------------------------------------------------
# Endpoint-specific payer ID management (crosswalk-backed with hardcoded default)
# -----------------------------------------------------------------------------
# Intent:
# - Validate payer IDs against the endpoint actually being called.
# - Persist endpoint-specific payer ID lists into the crosswalk so they can be
#   updated over time without changing code.
# - For OPTUMAI: use the augmented list (includes LIFE1, WELM2, etc.).
# - For UHCAPI (including its Super Connector fallback): strictly enforce the
#   known-good UHC payer IDs only.
# - Future: OPTUMAI will expose a dedicated endpoint that returns its current
#   valid payer list. When available, this function should fetch and refresh the
#   crosswalk entry automatically (likely weekly/monthly), replacing the
#   hardcoded default below. The UHCAPI Super Connector will eventually be
#   deprecated; when removed, cleanup the UHC-specific paths accordingly.

try:
    # Prefer using existing crosswalk persistence utilities
    from MediBot.MediBot_Crosswalk_Utils import ensure_full_config_loaded, save_crosswalk
except Exception:
    ensure_full_config_loaded = None
    save_crosswalk = None

def _get_default_endpoint_payer_ids(endpoint_name):
    """
    Return hardcoded default payer IDs for a given endpoint.

    NOTE: Defaults are used when crosswalk does not yet contain a list.
    """
    # UHC-only list – keep STRICT. Do not augment with non-UHC payers.
    uhc_payer_ids = [
        "87726", "03432", "96385", "95467", "86050", "86047", "95378", "06111", "37602"
    ]

    # OPTUMAI – augmented list (subject to growth once the API adds a payer-list endpoint)
    optumai_payer_ids = [
        # Supported Payer IDs per Optum Real Claims Inquiry (partial swagger)
        "87726", "25463", "39026", "74227", "LIFE1", "WELM2", "06111",
        "96385", "37602", "03432", "95467", "86050", "86047", "95378"
    ]

    if endpoint_name == 'OPTUMAI':
        return optumai_payer_ids
    # Default to UHCAPI for any other endpoint name
    return uhc_payer_ids

def get_valid_payer_ids_for_endpoint(client, endpoint_name):
    """
    Resolve the valid payer IDs for a specific endpoint using crosswalk storage
    with a safe fallback to hardcoded defaults.

    Behavior:
    - Attempts to read crosswalk['endpoint_payer_ids'][endpoint_name].
    - If missing, initializes with hardcoded defaults and persists to crosswalk
      (non-interactive) so that future sessions use the saved list.
    - Future: For OPTUMAI, replace the hardcoded default by calling the API's
      payer-list endpoint once available, then update the crosswalk.
    """
    try:
        # Load full config + crosswalk (non-destructive)
        base_config = None
        crosswalk = None
        if ensure_full_config_loaded is not None:
            base_config, crosswalk = ensure_full_config_loaded(
                getattr(client, 'config', None),
                getattr(client, 'crosswalk', None)
            )
        else:
            # Fallback: attempt to load via MediLink_ConfigLoader directly
            # If we reach this fallback, it means ensure_full_config_loaded is not available.
            # This is unexpected in normal operation and should be alerted.
            print("Warning: IN api_core, ensure_full_config_loaded is not available; falling back to MediLink_ConfigLoader.load_configuration().")
            MediLink_ConfigLoader.log(
                "Fallback: ensure_full_config_loaded not available in get_valid_payer_ids_for_endpoint; using MediLink_ConfigLoader.load_configuration().",
                level="WARNING"
            )
            base_config, crosswalk = MediLink_ConfigLoader.load_configuration()

        # Extract any existing stored list
        cw_ep = crosswalk.get('endpoint_payer_ids', {}) if isinstance(crosswalk, dict) else {}
        existing = cw_ep.get(endpoint_name)
        if isinstance(existing, list) and len(existing) > 0:
            return existing

        # Initialize from defaults and persist to crosswalk
        defaults = _get_default_endpoint_payer_ids(endpoint_name)
        if isinstance(crosswalk, dict):
            if 'endpoint_payer_ids' not in crosswalk:
                crosswalk['endpoint_payer_ids'] = {}
            crosswalk['endpoint_payer_ids'][endpoint_name] = list(defaults)

            # Persist without interactive prompts; ignore errors silently to avoid breaking flows
            if save_crosswalk is not None:
                try:
                    save_crosswalk(client, base_config, crosswalk, skip_api_operations=True)
                except Exception:
                    pass
        return defaults
    except Exception:
        # As a last resort, return a safe default for the endpoint
        return _get_default_endpoint_payer_ids(endpoint_name)

class BaseAPIClient:
    def __init__(self, config):
        self.config = config
        self.token_cache = TokenCache()
        # Log when a new APIClient instance is created (helps diagnose token cache issues)
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("New APIClient instance created (token cache is instance-specific)", level="DEBUG")

    def get_access_token(self, endpoint_name):
        raise NotImplementedError("Subclasses should implement this!")

    def make_api_call(self, endpoint_name, call_type, url_extension="", params=None, data=None, headers=None):
        raise NotImplementedError("Subclasses should implement this!")

class APIClient(BaseAPIClient):
    def __init__(self):
        config, _ = MediLink_ConfigLoader.load_configuration()
        super().__init__(config)
        
        # Add enhanced features if available
        # XP/Python34 Compatibility: Enhanced error handling with verbose output
        try:
            from MediCafe.api_utils import APICircuitBreaker, APICache, APIRateLimiter
            MediLink_ConfigLoader.log("Successfully imported MediCafe.api_utils", level="DEBUG")
        except ImportError as e:
            MediLink_ConfigLoader.log("Warning: MediCafe.api_utils not available: {}".format(str(e)), level="WARNING")
            print("Warning: MediCafe.api_utils import failed: {}".format(str(e)))
            APICircuitBreaker = None
            APICache = None
            APIRateLimiter = None
        except Exception as e:
            MediLink_ConfigLoader.log("Unexpected error importing MediCafe.api_utils: {}".format(str(e)), level="ERROR")
            print("Error: Unexpected MediCafe.api_utils import error: {}".format(str(e)))
            APICircuitBreaker = None
            APICache = None
            APIRateLimiter = None
        
        try:
            try:
                from MediLink import MediLink_insurance_utils
            except Exception:
                MediLink_insurance_utils = None
            if MediLink_insurance_utils is None:
                import importlib
                MediLink_insurance_utils = importlib.import_module('MediLink.MediLink_insurance_utils')
            get_feature_flag = MediLink_insurance_utils.get_feature_flag
            MediLink_ConfigLoader.log("Successfully imported MediLink.MediLink_insurance_utils", level="DEBUG")
        except ImportError as e:
            MediLink_ConfigLoader.log("Warning: MediLink.MediLink_insurance_utils not available: {}".format(str(e)), level="WARNING")
            print("Warning: MediLink.MediLink_insurance_utils import failed: {}".format(str(e)))
            # Provide fallback function
            def get_feature_flag(flag_name, default=False):
                MediLink_ConfigLoader.log("Using fallback get_feature_flag for '{}', returning default: {}".format(flag_name, default), level="DEBUG")
                return default
        except Exception as e:
            MediLink_ConfigLoader.log("Unexpected error importing MediLink.MediLink_insurance_utils: {}".format(str(e)), level="ERROR")
            print("Error: Unexpected MediLink.MediLink_insurance_utils import error: {}".format(str(e)))
            # Provide fallback function
            def get_feature_flag(flag_name, default=False):
                MediLink_ConfigLoader.log("Using fallback get_feature_flag for '{}', returning default: {}".format(flag_name, default), level="DEBUG")
                return default
        
        # Initialize enhancements with error handling
        try:
            enable_circuit_breaker = get_feature_flag('api_circuit_breaker', default=False)
            enable_caching = get_feature_flag('api_caching', default=False)
            enable_rate_limiting = get_feature_flag('api_rate_limiting', default=False)
            
            self.circuit_breaker = APICircuitBreaker() if (enable_circuit_breaker and APICircuitBreaker) else None
            self.api_cache = APICache() if (enable_caching and APICache) else None
            self.rate_limiter = APIRateLimiter() if (enable_rate_limiting and APIRateLimiter) else None
            
            if any([enable_circuit_breaker, enable_caching, enable_rate_limiting]):
                MediLink_ConfigLoader.log("Enhanced API client initialized with circuit_breaker={}, caching={}, rate_limiting={}".format(
                    enable_circuit_breaker, enable_caching, enable_rate_limiting), level="INFO")
            else:
                MediLink_ConfigLoader.log("API enhancements disabled or not available, using standard client", level="DEBUG")
        except Exception as e:
            MediLink_ConfigLoader.log("Error initializing API enhancements: {}. Using standard client.".format(str(e)), level="WARNING")
            print("Warning: API enhancement initialization failed: {}".format(str(e)))
            self.circuit_breaker = None
            self.api_cache = None
            self.rate_limiter = None

    def detect_environment(self, endpoint_name='UHCAPI'):
        """Detect if we're running in staging/test environment for a specific endpoint"""
        try:
            # Look for api_url in the specified endpoint configuration
            from MediCafe.core_utils import extract_medilink_config
            medi = extract_medilink_config(self.config)
            api_url = medi.get('endpoints', {}).get(endpoint_name, {}).get('api_url', '')
            MediLink_ConfigLoader.log("DEBUG: Found API URL for {}: {}".format(endpoint_name, api_url), level="DEBUG")
            
            if 'stg' in api_url.lower() or 'stage' in api_url.lower() or 'test' in api_url.lower():
                MediLink_ConfigLoader.log("DEBUG: Detected staging environment for {} from URL: {}".format(endpoint_name, api_url), level="DEBUG")
                return 'sandbox'
            else:
                MediLink_ConfigLoader.log("DEBUG: No staging indicators found in {} URL: {}".format(endpoint_name, api_url), level="DEBUG")
        except Exception as e:
            MediLink_ConfigLoader.log("DEBUG: Error in environment detection for {}: {}".format(endpoint_name, e), level="DEBUG")
        
        # Default to production (no env parameter)
        return None

    def add_environment_headers(self, headers, endpoint_name):
        """Add environment-specific headers based on detected environment"""
        # TODO: ENVIRONMENT DETECTION ARCHITECTURE ISSUE
        # 
        # Design proposal:
        # - Make env handling strictly per-endpoint and opt-in via config:
        #   config['MediLink_Config']['endpoints'][ep]['use_env_header'] = true|false
        #   config['MediLink_Config']['endpoints'][ep]['env_header_name'] = 'env' (overrideable per endpoint)
        #   config['MediLink_Config']['endpoints'][ep]['staging_indicators'] = ['stg', 'stage', 'test']
        # - If not configured, do NOT inject headers for that endpoint.
        # - Keep current UHC behavior as a fallback to preserve existing behavior.
        # - XP note: keep logic lightweight; avoid heavy regex on each call.
        # 
        # Current Implementation (compat mode):
        if endpoint_name == 'UHCAPI':
            environment = self.detect_environment(endpoint_name)
            if environment:
                headers['env'] = environment
                MediLink_ConfigLoader.log("Added env parameter for staging environment: {}".format(environment), level="INFO", console_output=CONSOLE_LOGGING)
            else:
                MediLink_ConfigLoader.log("No env parameter - using production environment", level="INFO", console_output=CONSOLE_LOGGING)
        return headers

    def get_access_token(self, endpoint_name):
        MediLink_ConfigLoader.log("[Get Access Token] Called for {}".format(endpoint_name), level="DEBUG")
        current_time = time.time()
        cached_token = self.token_cache.get(endpoint_name, current_time)
        
        if cached_token:
            expires_at = self.token_cache.tokens[endpoint_name]['expires_at']
            MediLink_ConfigLoader.log("Cached token expires at {}".format(expires_at), level="DEBUG")
            return cached_token
        
        # Validate that we actually need a token before fetching
        # Check if the endpoint configuration exists and is valid
        try:
            from MediCafe.core_utils import extract_medilink_config
            medi = extract_medilink_config(self.config)
            endpoint_config = medi.get('endpoints', {}).get(endpoint_name)
            if not endpoint_config:
                MediLink_ConfigLoader.log("No configuration found for endpoint: {}".format(endpoint_name), level="ERROR")
                return None
                
            # Validate required configuration fields
            required_fields = ['token_url', 'client_id', 'client_secret']
            missing_fields = [field for field in required_fields if field not in endpoint_config]
            if missing_fields:
                MediLink_ConfigLoader.log("Missing required configuration fields for {}: {}".format(endpoint_name, missing_fields), level="ERROR")
                return None
                
        except KeyError:
            MediLink_ConfigLoader.log("Endpoint {} not found in configuration".format(endpoint_name), level="ERROR")
            return None
        except Exception as e:
            MediLink_ConfigLoader.log("Error validating endpoint configuration for {}: {}".format(endpoint_name, str(e)), level="ERROR")
            return None
        
        # If no valid token, fetch a new one
        token_url = endpoint_config['token_url']
        data = {
            'grant_type': 'client_credentials',
            'client_id': endpoint_config['client_id'],
            'client_secret': endpoint_config['client_secret']
        }

        # NOTE: Scope parameter is OPTIONAL for OPTUM API token requests.
        # According to OPTUM API documentation and investigation (see docs/OPTUMAI_TOKEN_SCOPE_INVESTIGATION.md),
        # scopes are auto-granted based on client credentials and subscription configuration in the OPTUMAI portal.
        # The scope parameter in the token request is not required - OPTUM determines available scopes
        # (e.g., read_healthcheck for eligibility endpoint) based on the client's subscription.
        # We include scope in the request if present in config for informational/debugging purposes,
        # but it is not validated as it's not part of the standard OPTUM token request flow.
        # For other endpoints that may require explicit scope, the conditional logic below handles it.
        if 'scope' in endpoint_config:
            data['scope'] = endpoint_config['scope']
            # Log scope value for informational/debugging purposes (OPTUM doesn't require it)
            if endpoint_name == 'OPTUMAI':
                MediLink_ConfigLoader.log(
                    "Scope '{}' found in OPTUMAI config (informational only - OPTUM auto-grants scopes via subscription)".format(
                        endpoint_config['scope']),
                    level="DEBUG"
                )

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        try:
            response = requests.post(token_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data['access_token']
            # Use actual expires_in from response (OPTUM docs state 3600 seconds, but use actual value)
            expires_in = token_data.get('expires_in', 3600)
            
            # Log token acquisition details (without exposing secrets)
            if 'scope' in endpoint_config:
                scope_info = "scope: {}".format(endpoint_config['scope'])
            else:
                scope_info = "scope: none (OPTUM auto-grants via subscription)"
            MediLink_ConfigLoader.log(
                "Obtained NEW token for endpoint: {} (expires_in: {}s, {})".format(
                    endpoint_name, expires_in, scope_info),
                level="INFO",
                console_output=CONSOLE_LOGGING
            )
            
            # Log if expires_in differs from expected 3600 (per OPTUM docs)
            if expires_in != 3600:
                MediLink_ConfigLoader.log(
                    "Token expiration time ({}) differs from OPTUM documented value (3600s). Using actual value from response.".format(
                        expires_in),
                    level="INFO"
                )

            self.token_cache.set(endpoint_name, access_token, expires_in, current_time)
            return access_token
        except requests.exceptions.RequestException as e:
            MediLink_ConfigLoader.log("Failed to obtain token for {}: {}".format(endpoint_name, str(e)), level="ERROR")
            # Emit concise connectivity hint for DNS/proxy issues (best-effort, console-gated)
            try:
                from MediCafe.api_hints import emit_network_hint
                emit_network_hint(endpoint_name, token_url, e, console=CONSOLE_LOGGING)
            except Exception:
                pass
            return None
        except (KeyError, ValueError) as e:
            MediLink_ConfigLoader.log("Invalid token response for {}: {}".format(endpoint_name, str(e)), level="ERROR")
            return None

    def make_api_call(self, endpoint_name, call_type, url_extension="", params=None, data=None, headers=None):
        # Try enhanced API call if available
        if hasattr(self, 'circuit_breaker') and self.circuit_breaker:
            try:
                return self._make_enhanced_api_call(endpoint_name, call_type, url_extension, params, data, headers)
            except Exception as e:
                MediLink_ConfigLoader.log("Enhanced API call failed, falling back to standard: {}".format(str(e)), level="WARNING")
        
        # Standard API call logic
        return self._make_standard_api_call(endpoint_name, call_type, url_extension, params, data, headers)
    
    def _make_enhanced_api_call(self, endpoint_name, call_type, url_extension="", params=None, data=None, headers=None):
        """Enhanced API call with circuit breaker, caching, and rate limiting"""
        # Check cache first (for GET requests)
        if self.api_cache and call_type == 'GET':
            cached_result = self.api_cache.get(endpoint_name, call_type, url_extension, params)
            if cached_result is not None:
                MediLink_ConfigLoader.log("Cache hit for {} {} {}".format(call_type, endpoint_name, url_extension), level="DEBUG")
                return cached_result
        
        # Check rate limits
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed()
        
        # Make call with circuit breaker protection
        result = self.circuit_breaker.call_with_breaker(
            self._make_standard_api_call, endpoint_name, call_type, url_extension, params, data, headers)
        
        # Record rate limit call
        if self.rate_limiter:
            self.rate_limiter.record_call()
        
        # Cache result (for GET requests)
        if self.api_cache and call_type == 'GET':
            self.api_cache.set(result, endpoint_name, call_type, url_extension, params)
        
        return result
    
    def _make_standard_api_call(self, endpoint_name, call_type, url_extension="", params=None, data=None, headers=None):
        """Standard API call logic preserved for compatibility"""
        token = self.get_access_token(endpoint_name)
        if token:
            MediLink_ConfigLoader.log("[Make API Call] Token found for {}".format(endpoint_name), level="DEBUG")
        else:
            MediLink_ConfigLoader.log("[Make API Call] No token obtained for {}".format(endpoint_name), level="ERROR")
            raise ValueError("No access token available for endpoint: {}".format(endpoint_name))

        if headers is None:
            headers = {}
        headers.update({'Authorization': 'Bearer {}'.format(token), 'Accept': 'application/json'})
        
        # Add environment-specific headers automatically
        headers = self.add_environment_headers(headers, endpoint_name)
        
        from MediCafe.core_utils import extract_medilink_config
        medi = extract_medilink_config(self.config)
        base_url = medi.get('endpoints', {}).get(endpoint_name, {}).get('api_url', '')
        if not base_url:
            raise ValueError("Missing api_url for endpoint {}".format(endpoint_name))
        url = base_url + url_extension

        # VERBOSE LOGGING: Log all request details before making the call
        if DEBUG:
            MediLink_ConfigLoader.log("=" * 80, level="INFO")
            MediLink_ConfigLoader.log("VERBOSE API CALL DETAILS", level="INFO")
            MediLink_ConfigLoader.log("=" * 80, level="INFO")
            MediLink_ConfigLoader.log("Endpoint Name: {}".format(endpoint_name), level="INFO")
            MediLink_ConfigLoader.log("Call Type: {}".format(call_type), level="INFO")
            MediLink_ConfigLoader.log("Base URL: {}".format(base_url), level="INFO")
            MediLink_ConfigLoader.log("URL Extension: {}".format(url_extension), level="INFO")
            MediLink_ConfigLoader.log("Full URL: {}".format(url), level="INFO")
            MediLink_ConfigLoader.log("Headers: {}".format(json.dumps(headers, indent=2)), level="INFO")
            if params:
                MediLink_ConfigLoader.log("Query Parameters: {}".format(json.dumps(params, indent=2)), level="INFO")
            else:
                MediLink_ConfigLoader.log("Query Parameters: None", level="INFO")
            if data:
                MediLink_ConfigLoader.log("Request Data: {}".format(json.dumps(data, indent=2)), level="INFO")
            else:
                MediLink_ConfigLoader.log("Request Data: None", level="INFO")
            MediLink_ConfigLoader.log("=" * 80, level="INFO")

        try:
            masked_headers = headers.copy()
            if 'Authorization' in masked_headers:
                masked_headers['Authorization'] = 'Bearer ***'

            def make_request():
                if call_type == 'GET':
                    if DEBUG:
                        MediLink_ConfigLoader.log("Making GET request to: {}".format(url), level="INFO")
                    return requests.get(url, headers=headers, params=params)
                elif call_type == 'POST':
                    # Check if there are custom headers (any headers beyond Authorization and Accept)
                    custom_headers = {k: v for k, v in headers.items() if k not in ['Authorization', 'Accept']}
                    
                    if custom_headers:
                        # Log that custom headers were detected
                        MediLink_ConfigLoader.log("Custom headers detected: {}".format(custom_headers), level="DEBUG")
                    else:
                        # Set default Content-Type if no custom headers
                        headers['Content-Type'] = 'application/json'
                    
                    if DEBUG:
                        MediLink_ConfigLoader.log("Making POST request to: {}".format(url), level="INFO")
                    return requests.post(url, headers=headers, json=data)
                elif call_type == 'DELETE':
                    if DEBUG:
                        MediLink_ConfigLoader.log("Making DELETE request to: {}".format(url), level="INFO")
                    return requests.delete(url, headers=headers)
                else:
                    raise ValueError("Unsupported call type: {}".format(call_type))

            route_retry_performed = False
            trailing_question_tried = False

            while True:
                try:
                    # Make initial request
                    response = make_request()

                    # VERBOSE LOGGING: Log response details
                    if DEBUG:
                        MediLink_ConfigLoader.log("=" * 80, level="INFO")
                        MediLink_ConfigLoader.log("VERBOSE RESPONSE DETAILS", level="INFO")
                        MediLink_ConfigLoader.log("=" * 80, level="INFO")
                        MediLink_ConfigLoader.log("Response Status Code: {}".format(response.status_code), level="INFO")
                        MediLink_ConfigLoader.log("Response Headers: {}".format(json.dumps(dict(response.headers), indent=2)), level="INFO")
                        
                        try:
                            response_json = response.json()
                            MediLink_ConfigLoader.log("Response JSON: {}".format(json.dumps(response_json, indent=2)), level="INFO")
                        except ValueError:
                            MediLink_ConfigLoader.log("Response Text (not JSON): {}".format(response.text), level="INFO")
                        
                        MediLink_ConfigLoader.log("=" * 80, level="INFO")

                    # Handle 401 Unauthorized errors with token refresh and retry
                    if response.status_code == 401:
                        # Parse error response for diagnostics
                        trace_id = None
                        error_type = None
                        try:
                            error_response = response.json()
                            trace_id = error_response.get('traceId') or error_response.get('trace_id')
                            error_type = error_response.get('error') or error_response.get('error_type')
                            error_desc = error_response.get('error_description', '')
                            
                            # Check for "invalid_access_token" specifically
                            is_invalid_token = (error_type == 'invalid_access_token' or 
                                               'invalid_access_token' in error_desc.lower())
                            if is_invalid_token:
                                MediLink_ConfigLoader.log(
                                    "401 Unauthorized: invalid_access_token detected for endpoint {}. "
                                    "Clearing token cache and attempting refresh...".format(endpoint_name),
                                    level="WARNING",
                                    console_output=CONSOLE_LOGGING
                                )
                                if trace_id:
                                    MediLink_ConfigLoader.log("Trace ID: {}".format(trace_id), level="INFO")
                                
                                # Clear token cache for this endpoint (401 invalid_access_token error)
                                self.token_cache.clear(endpoint_name, reason="401 invalid_access_token")
                                
                                # Attempt to get a fresh token
                                fresh_token = self.get_access_token(endpoint_name)
                                if fresh_token:
                                    # Update headers with fresh token
                                    headers['Authorization'] = 'Bearer {}'.format(fresh_token)
                                    MediLink_ConfigLoader.log(
                                        "Token refreshed successfully. Retrying request to {}...".format(url),
                                        level="INFO",
                                        console_output=CONSOLE_LOGGING
                                    )
                                    
                                    # Retry the request once with fresh token
                                    time.sleep(0.5)  # Brief delay before retry
                                    response = make_request()
                                    
                                    # Log retry result
                                    if response.status_code == 200:
                                        MediLink_ConfigLoader.log(
                                            "Retry successful after token refresh! Request to {} now returned 200 status code.".format(url),
                                            level="INFO",
                                            console_output=CONSOLE_LOGGING
                                        )
                                    else:
                                        MediLink_ConfigLoader.log(
                                            "Retry failed after token refresh. Request to {} still returned {} status code.".format(
                                                url, response.status_code),
                                            level="ERROR",
                                            console_output=CONSOLE_LOGGING
                                        )
                                        if trace_id:
                                            MediLink_ConfigLoader.log(
                                                "Trace ID: {}. This may indicate a subscription/configuration issue. "
                                                "Verify client credentials and subscription access in OPTUMAI portal.".format(trace_id),
                                                level="ERROR",
                                                console_output=CONSOLE_LOGGING
                                            )
                                else:
                                    MediLink_ConfigLoader.log(
                                        "Failed to obtain fresh token for endpoint {}. Cannot retry request.".format(endpoint_name),
                                        level="ERROR",
                                        console_output=CONSOLE_LOGGING
                                    )
                        except (ValueError, KeyError) as e:
                            # Error response not in expected format
                            MediLink_ConfigLoader.log(
                                "401 Unauthorized error for endpoint {}. Could not parse error response: {}".format(
                                    endpoint_name, str(e)),
                                level="ERROR",
                                console_output=CONSOLE_LOGGING
                            )
                            # Still attempt token refresh (fallback for unparseable 401 responses)
                            self.token_cache.clear(endpoint_name, reason="401 unparseable error response")
                            fresh_token = self.get_access_token(endpoint_name)
                            if fresh_token:
                                headers['Authorization'] = 'Bearer {}'.format(fresh_token)
                                MediLink_ConfigLoader.log(
                                    "Token refreshed (unparseable 401 response). Retrying request...",
                                    level="INFO",
                                    console_output=CONSOLE_LOGGING
                                )
                                time.sleep(0.5)
                                response = make_request()
                            else:
                                MediLink_ConfigLoader.log(
                                    "Failed to obtain fresh token for endpoint {}. Cannot retry request.".format(endpoint_name),
                                    level="ERROR",
                                    console_output=CONSOLE_LOGGING
                                )

                    # If we get a 5xx error, wait and retry once
                    if 500 <= response.status_code < 600:
                        error_msg = "Received {} error from server for {} request to {}. Waiting 1 second before retry...".format(
                            response.status_code, call_type, url
                        )
                        MediLink_ConfigLoader.log(error_msg, level="WARNING")
                        
                        # Add more verbose logging for 504 errors specifically
                        if response.status_code == 504:
                            MediLink_ConfigLoader.log(
                                "504 Gateway Timeout detected. This usually indicates the server is overloaded or taking too long to respond. " 
                                "Retrying after 1 second delay...", 
                                level="WARNING"
                            )
                        
                        time.sleep(1)
                        response = make_request()
                        
                        # Log the retry result
                        if response.status_code == 200:
                            MediLink_ConfigLoader.log(
                                "Retry successful! Request to {} now returned 200 status code.".format(url),
                                level="INFO"
                            )
                        else:
                            MediLink_ConfigLoader.log(
                                "Retry failed. Request to {} still returned {} status code.".format(url, response.status_code),
                                level="ERROR"
                            )

                    # Handle trailing '?' fallback for POST requests with 404/500 errors
                    # Some API gateways (e.g., UHC Claims API) require trailing '?' for POST requests without query params
                    if (response.status_code in [404, 500] and 
                        call_type == 'POST' and 
                        not trailing_question_tried and
                        (params is None or len(params) == 0) and
                        not url.endswith('?')):
                        
                        original_status_code = response.status_code
                        original_url = url
                        url = url + '?'
                        trailing_question_tried = True
                        
                        MediLink_ConfigLoader.log(
                            "Received {} error on POST request to {}. Retrying with trailing '?' as API gateway may require it...".format(
                                original_status_code, original_url),
                            level="INFO",
                            console_output=CONSOLE_LOGGING
                        )
                        
                        # Brief delay before retry
                        time.sleep(0.5)
                        response = make_request()
                        
                        # Log the retry result
                        if response.status_code == 200 or (200 <= response.status_code < 300):
                            MediLink_ConfigLoader.log(
                                "Retry successful with trailing '?' appended. Original error was {}. New URL: {}".format(
                                    original_status_code, url),
                                level="INFO",
                                console_output=CONSOLE_LOGGING
                            )
                        else:
                            MediLink_ConfigLoader.log(
                                "Retry with trailing '?' failed. Still received {} status code.".format(response.status_code),
                                level="WARNING",
                                console_output=CONSOLE_LOGGING
                            )
                        
                        # Continue the loop to allow full error handling on the retry response
                        continue

                    # Raise an HTTPError if the response was unsuccessful
                    response.raise_for_status()

                    return response.json()

                except requests.exceptions.HTTPError as http_err:
                    response_obj = getattr(http_err, 'response', None)
                    status_code = getattr(response_obj, 'status_code', None)
                    response_content = None
                    response_content_for_log = None

                    if response_obj is not None:
                        try:
                            response_content = response_obj.json()
                            response_content_for_log = json.dumps(response_content, indent=2)
                        except ValueError:
                            response_content = response_obj.text
                            response_content_for_log = response_obj.text

                    should_retry_route = False
                    if response_obj is not None and not route_retry_performed:
                        try:
                            should_retry_route = handle_route_mismatch_404(
                                status_code,
                                response_content,
                                call_type,
                                url,
                                CONSOLE_LOGGING
                            )
                        except Exception as remediation_err:
                            MediLink_ConfigLoader.log(
                                "Route mismatch remediation failed to start: {}".format(str(remediation_err)),
                                level="WARNING",
                                console_output=CONSOLE_LOGGING
                            )

                    if should_retry_route and not route_retry_performed:
                        route_retry_performed = True
                        time.sleep(0.5)
                        continue

                    MediLink_ConfigLoader.log("=" * 80, level="ERROR")
                    MediLink_ConfigLoader.log("VERBOSE HTTP ERROR DETAILS", level="ERROR")
                    MediLink_ConfigLoader.log("=" * 80, level="ERROR")

                    if response_obj is None:
                        log_message = (
                            "HTTPError with no response. "
                            "URL: {url}, "
                            "Method: {method}, "
                            "Params: {params}, "
                            "Data: {data}, "
                            "Headers: {masked_headers}, "
                            "Error: {error}"
                        ).format(
                            url=url,
                            method=call_type,
                            params=params,
                            data=data,
                            masked_headers=masked_headers,
                            error=str(http_err)
                        )
                        MediLink_ConfigLoader.log(log_message, level="ERROR")
                    else:
                        MediLink_ConfigLoader.log("HTTP Error Status Code: {}".format(status_code), level="ERROR")
                        MediLink_ConfigLoader.log("HTTP Error URL: {}".format(url), level="ERROR")
                        MediLink_ConfigLoader.log("HTTP Error Method: {}".format(call_type), level="ERROR")
                        MediLink_ConfigLoader.log("HTTP Error Headers: {}".format(json.dumps(masked_headers, indent=2)), level="ERROR")
                        
                        if params:
                            MediLink_ConfigLoader.log("HTTP Error Query Params: {}".format(json.dumps(params, indent=2)), level="ERROR")
                        if data:
                            MediLink_ConfigLoader.log("HTTP Error Request Data: {}".format(json.dumps(data, indent=2)), level="ERROR")
                        
                        if isinstance(response_content, (dict, list)):
                            MediLink_ConfigLoader.log("HTTP Error Response JSON: {}".format(response_content_for_log), level="ERROR")
                        else:
                            MediLink_ConfigLoader.log("HTTP Error Response Text: {}".format(response_content_for_log), level="ERROR")

                        log_message = (
                            "HTTPError: Status Code: {status}, "
                            "URL: {url}, "
                            "Method: {method}, "
                            "Params: {params}, "
                            "Data: {data}, "
                            "Headers: {masked_headers}, "
                            "Response Content: {content}"
                        ).format(
                            status=status_code,
                            url=url,
                            method=call_type,
                            params=params,
                            data=data,
                            masked_headers=masked_headers,
                            content=response_content
                        )
                        MediLink_ConfigLoader.log(log_message, level="ERROR")
                        # Provide a brief 404 route-match hint when applicable (best-effort, console-gated)
                        try:
                            from MediCafe.api_hints import emit_404_route_hint
                            emit_404_route_hint(call_type, url, status_code, response_content, console=CONSOLE_LOGGING)
                        except Exception:
                            pass

                    MediLink_ConfigLoader.log("=" * 80, level="ERROR")
                    raise

        except requests.exceptions.RequestException as req_err:
            # Log connection-related issues or other request exceptions
            log_message = (
                "RequestException: No response received. "
                "URL: {url}, "
                "Method: {method}, "
                "Params: {params}, "
                "Data: {data}, "
                "Headers: {masked_headers}, "
                "Error: {error}"
            ).format(
                url=url,
                method=call_type,
                params=params,
                data=data,
                masked_headers=masked_headers,
                error=str(req_err)
            )
            MediLink_ConfigLoader.log(log_message, level="ERROR")
            # Emit concise connectivity hint for DNS/proxy issues (best-effort, console-gated)
            try:
                from MediCafe.api_hints import emit_network_hint
                emit_network_hint(endpoint_name, url, req_err, console=CONSOLE_LOGGING)
            except Exception:
                pass
            raise

        except Exception as e:
            # Capture traceback for unexpected exceptions
            tb = traceback.format_exc()
            log_message = (
                "Unexpected error: {error}. "
                "URL: {url}, "
                "Method: {method}, "
                "Params: {params}, "
                "Data: {data}, "
                "Headers: {masked_headers}. "
                "Traceback: {traceback}"
            ).format(
                error=str(e),
                url=url,
                method=call_type,
                params=params,
                data=data,
                masked_headers=masked_headers,
                traceback=tb
            )
            MediLink_ConfigLoader.log(log_message, level="ERROR")
            raise

def fetch_payer_name_from_api(*args, **kwargs):
    """
    Fetch payer name by Payer ID with backward-compatible calling styles.

    Supported call signatures:
    - fetch_payer_name_from_api(client, payer_id, config, primary_endpoint='AVAILITY')
    - fetch_payer_name_from_api(payer_id, config, primary_endpoint='AVAILITY')  # client inferred via factory
    - fetch_payer_name_from_api(payer_id=payer_id, config=config, client=client, primary_endpoint='AVAILITY')
    """
    # Normalize arguments
    client = None
    payer_id = None
    config = None
    primary_endpoint = kwargs.get('primary_endpoint', 'AVAILITY')

    if 'client' in kwargs:
        client = kwargs.get('client')
    if 'payer_id' in kwargs:
        payer_id = kwargs.get('payer_id')
    if 'config' in kwargs:
        config = kwargs.get('config')

    if len(args) >= 3 and isinstance(args[0], APIClient):
        client = args[0]
        payer_id = args[1]
        config = args[2]
        if len(args) >= 4 and 'primary_endpoint' not in kwargs:
            primary_endpoint = args[3]
    elif len(args) >= 2 and isinstance(args[0], str) and client is None:
        # Called as (payer_id, config, [primary_endpoint])
        payer_id = args[0]
        config = args[1]
        if len(args) >= 3 and 'primary_endpoint' not in kwargs:
            primary_endpoint = args[2]
    elif len(args) == 1 and isinstance(args[0], APIClient) and (payer_id is None or config is None):
        # Partial positional with client first, other params via kwargs
        client = args[0]

    # Acquire client via factory if not provided
    if client is None:
        try:
            from MediCafe.core_utils import get_api_client
            client = get_api_client()
            if client is None:
                client = APIClient()
        except Exception:
            client = APIClient()

    # Basic validation
    if not isinstance(client, APIClient):
        error_message = "Invalid client provided. Expected an instance of APIClient."
        MediLink_ConfigLoader.log(error_message, level="ERROR")
        raise ValueError(error_message)
    if payer_id is None or config is None:
        raise ValueError("Missing required arguments: payer_id and config are required")
    
    # TODO: FUTURE IMPLEMENTATION - Remove AVAILITY default when other endpoints have payer-list APIs
    # Currently defaulting to AVAILITY as it's the only endpoint with confirmed payer-list functionality
    # In the future, this should be removed and the system should dynamically detect which endpoints
    # have payer-list capabilities and use them accordingly.
    if primary_endpoint != 'AVAILITY':
        MediLink_ConfigLoader.log("[Fetch payer name from API] Overriding {} with AVAILITY (default until multi-endpoint payer-list support is implemented).".format(primary_endpoint), level="DEBUG")
        primary_endpoint = 'AVAILITY'
    
    try:
        from MediCafe.core_utils import extract_medilink_config
        medi = extract_medilink_config(config)
        endpoints = medi.get('endpoints', {})
    except KeyError as e:
        error_message = "Configuration loading error in fetch_payer_name_from_api: Missing key {0}... Attempting to reload configuration.".format(e)
        # print(error_message)
        MediLink_ConfigLoader.log(error_message, level="ERROR")
        # Attempt to reload configuration if key is missing
        config, _ = MediLink_ConfigLoader.load_configuration()
        # SAFE FALLBACK: if endpoints still missing, fall back to AVAILITY only and proceed.
        from MediCafe.core_utils import extract_medilink_config
        medi = extract_medilink_config(config)
        endpoints = medi.get('endpoints', {})
        if not endpoints:
            MediLink_ConfigLoader.log("Endpoints configuration missing after reload. Falling back to AVAILITY-only logic.", level="WARNING")
        MediLink_ConfigLoader.log("Re-loaded configuration successfully.", level="INFO")
    
    # Sanitize and validate payer_id
    if not isinstance(payer_id, str):
        payer_id = str(payer_id)
    
    payer_id = ''.join(char for char in payer_id if char.isalnum())
    
    if not payer_id:
        error_message = "Invalid payer_id in API v3: {}. Must contain a string of alphanumeric characters.".format(payer_id)
        MediLink_ConfigLoader.log(error_message, level="ERROR")
        print(error_message)
    
    # FUTURE IMPLEMENTATION: Dynamic endpoint selection based on payer-list availability
    # This will replace the hardcoded AVAILITY default when other endpoints have payer-list APIs
    # The logic should:
    # 1. Check all endpoints for 'payer_list_endpoint' configuration
    # 2. Prioritize endpoints that have confirmed payer-list functionality
    # 3. Fall back to endpoints with basic payer lookup if available
    # 4. Use AVAILITY as final fallback
    
    # If HTTP client is unavailable or endpoints missing, use offline fallback only when allowed (TestMode or env flag)
    try:
        http_unavailable = (requests is None)  # type: ignore[name-defined]
    except Exception:
        http_unavailable = True
    # Determine whether offline fallback is permitted
    # Align with main flow: default True when TestMode key is absent
    offline_allowed = True
    try:
        from MediCafe.core_utils import extract_medilink_config
        medi_local = extract_medilink_config(config)
        offline_allowed = bool(medi_local.get('TestMode', True))
    except Exception:
        offline_allowed = True
    try:
        if os.environ.get('MEDICAFE_OFFLINE_PERMISSIVE', '').strip().lower() in ('1', 'true', 'yes', 'y'):
            offline_allowed = True
    except Exception:
        pass

    if offline_allowed and (http_unavailable or not isinstance(endpoints, dict) or not endpoints):
        try:
            # Prefer crosswalk mapping when available
            try:
                _, cw = MediLink_ConfigLoader.load_configuration()
            except Exception:
                cw = {}
            payer_mappings = {}
            try:
                if isinstance(cw, dict):
                    payer_mappings = cw.get('payer_mappings', {}) or {}
            except Exception:
                payer_mappings = {}

            if payer_id in payer_mappings:
                resolved = payer_mappings.get(payer_id)
                MediLink_ConfigLoader.log(
                    "Using crosswalk mapping for payer {} -> {} (offline)".format(payer_id, resolved),
                    level="WARNING",
                    console_output=CONSOLE_LOGGING
                )
                return resolved
            # Safe minimal hardcoded map as last resort (test/offline only)
            fallback_map = {
                '87726': 'UnitedHealthcare',
                '06111': 'Aetna',
                '03432': 'Cigna',
                '95378': 'Anthem Blue Cross',
                '95467': 'Blue Shield',
            }
            if payer_id in fallback_map:
                MediLink_ConfigLoader.log(
                    "Using offline fallback for payer {} -> {}".format(payer_id, fallback_map[payer_id]),
                    level="WARNING",
                    console_output=CONSOLE_LOGGING
                )
                return fallback_map[payer_id]
        except Exception:
            pass

    # Define endpoint rotation logic with payer-list capability detection
    available_endpoints = []
    
    # Check which endpoints have payer-list functionality configured
    for endpoint_name, endpoint_config in endpoints.items():
        if 'payer_list_endpoint' in endpoint_config:
            available_endpoints.append(endpoint_name)
            MediLink_ConfigLoader.log("Found payer-list endpoint for {}: {}".format(endpoint_name, endpoint_config['payer_list_endpoint']), level="DEBUG")
    
    # If no endpoints have payer-list configured, fall back to AVAILITY
    if not available_endpoints:
        MediLink_ConfigLoader.log("No endpoints with payer-list configuration found, using AVAILITY as fallback", level="INFO")
        available_endpoints = ['AVAILITY']
    
    # Prioritize the primary endpoint if it has payer-list capability
    if primary_endpoint in available_endpoints:
        endpoint_order = [primary_endpoint] + [ep for ep in available_endpoints if ep != primary_endpoint]
    else:
        # If primary endpoint doesn't have payer-list, use available endpoints in order
        endpoint_order = available_endpoints
    
    MediLink_ConfigLoader.log("Endpoint order for payer lookup: {}".format(endpoint_order), level="DEBUG")

    for endpoint_name in endpoint_order:
        try:
            endpoint_url = endpoints[endpoint_name].get('payer_list_endpoint', '/availity-payer-list')
            response = client.make_api_call(endpoint_name, 'GET', endpoint_url, {'payerId': payer_id})
            
            # Check if response exists
            if not response:
                log_message = "No response from {0} for Payer ID {1}".format(endpoint_name, payer_id)
                print(log_message)
                MediLink_ConfigLoader.log(log_message, level="ERROR")
                continue
            
            # Check if the status code is not 200
            status_code = response.get('statuscode', 200)
            if status_code != 200:
                log_message = "Invalid response status code {0} from {1} for Payer ID {2}. Message: {3}".format(
                    status_code, endpoint_name, payer_id, response.get('message', 'No message'))
                print(log_message)
                MediLink_ConfigLoader.log(log_message, level="ERROR")
                continue
            
            # Extract payers and validate the response structure
            payers = response.get('payers', [])
            if not payers:
                log_message = "No payer found at {0} for ID {1}. Response: {2}".format(endpoint_name, payer_id, response)
                print(log_message)
                MediLink_ConfigLoader.log(log_message, level="INFO")
                continue
            
            # Extract the payer name from the first payer in the list
            payer_name = payers[0].get('displayName') or payers[0].get('name')
            if not payer_name:
                log_message = "Payer name not found in the response from {0} for ID {1}. Response: {2}".format(
                    endpoint_name, payer_id, response)
                print(log_message)
                MediLink_ConfigLoader.log(log_message, level="ERROR")
                continue
            
            # Log successful payer retrieval
            log_message = "Found payer at {0} for ID {1}: {2}".format(endpoint_name, payer_id, payer_name)
            MediLink_ConfigLoader.log(log_message, level="INFO")
            return payer_name
        
        except Exception as e:
            error_message = "Error calling {0} for Payer ID {1}. Exception: {2}".format(endpoint_name, payer_id, e)
            MediLink_ConfigLoader.log(error_message, level="INFO")

    # Offline/local fallback mapping for common payer IDs when API endpoints are unavailable
    # Only when offline fallback is permitted
    if offline_allowed:
        try:
            # Prefer crosswalk mapping first
            try:
                _, cw = MediLink_ConfigLoader.load_configuration()
            except Exception:
                cw = {}
            payer_mappings = {}
            try:
                if isinstance(cw, dict):
                    payer_mappings = cw.get('payer_mappings', {}) or {}
            except Exception:
                payer_mappings = {}
            if payer_id in payer_mappings:
                resolved = payer_mappings.get(payer_id)
                MediLink_ConfigLoader.log(
                    "Using crosswalk mapping for payer {} -> {} (offline)".format(payer_id, resolved),
                    level="WARNING",
                    console_output=CONSOLE_LOGGING
                )
                return resolved
            # Minimal fallback map if crosswalk has no mapping (still offline-only)
            fallback_map = {
                '87726': 'UnitedHealthcare',
                '06111': 'Aetna',
                '03432': 'Cigna',
                '95378': 'Anthem Blue Cross',
                '95467': 'Blue Shield',
            }
            if payer_id in fallback_map:
                MediLink_ConfigLoader.log(
                    "Using offline fallback for payer {} -> {}".format(payer_id, fallback_map[payer_id]),
                    level="WARNING",
                    console_output=CONSOLE_LOGGING
                )
                return fallback_map[payer_id]
        except Exception:
            pass

    # If all endpoints fail
    final_error_message = "All endpoints exhausted for Payer ID {0}.".format(payer_id)
    print(final_error_message)
    MediLink_ConfigLoader.log(final_error_message, level="CRITICAL")
    raise ValueError(final_error_message)

def get_claim_summary_by_provider(client, tin, first_service_date, last_service_date, payer_id, get_standard_error='false', transaction_id=None, env=None):
    """
    Unified Claims Inquiry that prefers OPTUMAI GraphQL searchClaim with
    legacy response mapping, and falls back to legacy UHCAPI REST endpoint
    to preserve current downstream flows and UI.
    """
    # Verbose input logging
    if DEBUG:
        MediLink_ConfigLoader.log("Claims Inquiry inputs: tin={} start={} end={} payer={} tx={}"
                                  .format(tin, first_service_date, last_service_date, payer_id, transaction_id),
                                  level="INFO")

    from MediCafe.core_utils import extract_medilink_config
    medi = extract_medilink_config(client.config)

    # Determine whether OPTUMAI is available/configured
    endpoints_cfg = medi.get('endpoints', {}) if isinstance(medi, dict) else {}
    optumai_cfg = endpoints_cfg.get('OPTUMAI', {}) if isinstance(endpoints_cfg, dict) else {}
    uhcapi_cfg = endpoints_cfg.get('UHCAPI', {}) if isinstance(endpoints_cfg, dict) else {}

    optumai_path = (optumai_cfg.get('additional_endpoints', {}) or {}).get('claims_inquiry')
    uhc_path = (uhcapi_cfg.get('additional_endpoints', {}) or {}).get('claim_summary_by_provider')

    optumai_api_url = optumai_cfg.get('api_url')
    use_optumai = bool(optumai_api_url and optumai_path)
    # Capability guard: disable OPTUMAI if required helpers are unavailable
    if use_optumai:
        has_build = hasattr(MediLink_GraphQL, 'build_optumai_claims_inquiry_request')
        has_transform = hasattr(MediLink_GraphQL, 'transform_claims_inquiry_response_to_legacy')
        if not (has_build and has_transform):
            if DEBUG:
                MediLink_ConfigLoader.log(
                    "Disabling OPTUMAI claims inquiry: missing GraphQL helpers (build/transform)",
                    level="WARNING",
                    console_output=CONSOLE_LOGGING
                )
            use_optumai = False

    # Validate payer ID list based on endpoint we will attempt
    # BUG (minimally fixed): Previously a broad except masked invalid payer IDs and config issues.
    # Minimal fix: narrow exceptions and log a clear warning; proceed to maintain backward compatibility.
    # Recommended next steps:
    # - In non-production environments, fail fast on invalid payer IDs.
    # - Return a structured error object for invalid payers to avoid silent pass-through.
    # - Add unit tests covering valid/invalid payers and config load failures.
    try:
        target_endpoint = 'OPTUMAI' if use_optumai else 'UHCAPI'
        valid_payers = get_valid_payer_ids_for_endpoint(client, target_endpoint)
        if payer_id not in valid_payers:
            raise ValueError("Invalid payer_id: {} for endpoint {}. Must be one of: {}".format(
                payer_id, target_endpoint, ", ".join(valid_payers)))
    except (ValueError, KeyError) as e:
        MediLink_ConfigLoader.log(
            "Payer validation warning: {}".format(e),
            level="WARNING",
            console_output=CONSOLE_LOGGING
        )
    except Exception as e:
        MediLink_ConfigLoader.log(
            "Payer validation unexpected error: {}".format(e),
            level="ERROR",
            console_output=CONSOLE_LOGGING
        )

    # Build OPTUMAI GraphQL request if configured
    if use_optumai:
        try:
            # Compose headers (providerTaxId is required per Optum Real API)
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            # Map billing_provider_tin to providerTaxId
            provider_tin = medi.get('billing_provider_tin')
            if provider_tin:
                headers['providerTaxId'] = str(provider_tin)
                # correlation id for tracing
                try:
                    corr_id = 'mc-ci-{}'.format(int(time.time() * 1000))
                except Exception:
                    corr_id = 'mc-ci-{}'.format(int(time.time()))
                headers['x-optum-consumer-correlation-id'] = corr_id

            # Environment header for sandbox/stage if URL indicates
            try:
                api_url_lower = str(optumai_api_url).lower()
                if any(tag in api_url_lower for tag in ['sandbox', 'stg', 'stage', 'test']):
                    headers['environment'] = 'sandbox'
            except Exception:
                pass

            # Build searchClaimInput per partial swagger
            search_claim_input = {
                'payerId': str(payer_id)
            }
            # Map dates MM/DD/YYYY -> expected strings for GraphQL (examples show MM/DD/YYYY and also 01/01/2025)
            if first_service_date:
                search_claim_input['serviceStartDate'] = first_service_date
            if last_service_date:
                search_claim_input['serviceEndDate'] = last_service_date

            # Note: our pagination param is nextPageToken header in swagger; we surface as transaction_id in legacy code
            # For subsequent pages, pass it in headers; GraphQL spec shows header, but our call builder only handles body.
            # We'll set header when calling API; the transformer maps nextPageToken -> transactionId for downstream.
            if transaction_id:
                headers['nextPageToken'] = transaction_id

            # Build GraphQL body
            graphql_body = MediLink_GraphQL.build_optumai_claims_inquiry_request(search_claim_input)

            # Make the call
            response = client.make_api_call('OPTUMAI', 'POST', optumai_path, params=None, data=graphql_body, headers=headers)

            # Transform to legacy format
            transformed = MediLink_GraphQL.transform_claims_inquiry_response_to_legacy(response)
            status = transformed.get('statuscode') if isinstance(transformed, dict) else None
            if status == '200':
                # Add note so UI can message that Optum Real is active (non-breaking)
                try:
                    transformed['data_source'] = 'OPTUMAI'
                except Exception:
                    pass
                return transformed
            # If not 200, fall through to UHC fallback when permitted
        except Exception as e:
            # If capability guard failed upstream for any reason, handle missing attribute gracefully here too
            if isinstance(e, AttributeError):
                MediLink_ConfigLoader.log(
                    "OPTUMAI disabled due to missing GraphQL helpers; falling back to UHCAPI.",
                    level="WARNING",
                    console_output=CONSOLE_LOGGING
                )
            else:
                MediLink_ConfigLoader.log("OPTUMAI Claims Inquiry failed: {}".format(e), level="WARNING")

    # Fallback to existing UHC REST behavior to preserve current flows
    endpoint_name = 'UHCAPI'
    url_extension = uhc_path or ''

    if DEBUG:
        MediLink_ConfigLoader.log("Falling back to UHCAPI claim_summary_by_provider path: {}".format(url_extension), level="INFO")

    headers = {
        'tin': tin,
        'firstServiceDt': first_service_date,
        'lastServiceDt': last_service_date,
        'payerId': payer_id,
        'getStandardError': get_standard_error,
        'Accept': 'application/json'
    }
    if transaction_id:
        headers['transactionId'] = transaction_id

    return client.make_api_call(endpoint_name, 'GET', url_extension, params=None, data=None, headers=headers)

def get_eligibility(client, payer_id, provider_last_name, search_option, date_of_birth, member_id, npi):
    endpoint_name = 'UHCAPI'
    from MediCafe.core_utils import extract_medilink_config
    medi = extract_medilink_config(client.config)
    url_extension = medi.get('endpoints', {}).get(endpoint_name, {}).get('additional_endpoints', {}).get('eligibility', '')
    url_extension = url_extension + '?payerID={}&providerLastName={}&searchOption={}&dateOfBirth={}&memberId={}&npi={}'.format(
        payer_id, provider_last_name, search_option, date_of_birth, member_id, npi)
    return client.make_api_call(endpoint_name, 'GET', url_extension)

def get_eligibility_v3(client, payer_id, provider_last_name, search_option, date_of_birth, member_id, npi, 
                       first_name=None, last_name=None, payer_label=None, payer_name=None, service_start=None, service_end=None, 
                       middle_name=None, gender=None, ssn=None, city=None, state=None, zip=None, group_number=None, 
                       service_type_code=None, provider_first_name=None, tax_id_number=None, provider_name_id=None, 
                       corporate_tax_owner_id=None, corporate_tax_owner_name=None, organization_name=None, 
                       organization_id=None, identify_service_level_deductible=True):

    # Ensure all required parameters have values
    if not all([client, payer_id, provider_last_name, search_option, date_of_birth, member_id, npi]):
        raise ValueError("All required parameters must have values: client, payer_id, provider_last_name, search_option, date_of_birth, member_id, npi")

    # Endpoint is UHCAPI for this v3 REST call
    endpoint_name = 'UHCAPI'

    # Validate payer_id strictly against UHC list
    valid_payer_ids = get_valid_payer_ids_for_endpoint(client, endpoint_name)
    if payer_id not in valid_payer_ids:
        raise ValueError("Invalid payer_id: {} for endpoint {}. Must be one of: {}".format(
            payer_id, endpoint_name, ", ".join(valid_payer_ids)))
    from MediCafe.core_utils import extract_medilink_config
    medi = extract_medilink_config(client.config)
    url_extension = medi.get('endpoints', {}).get(endpoint_name, {}).get('additional_endpoints', {}).get('eligibility_v3', '')
    
    # Construct request body
    body = {
        "memberId": member_id,
        "lastName": last_name,
        "firstName": first_name,
        "dateOfBirth": date_of_birth,
        "payerID": payer_id,
        "payerLabel": payer_label,
        "payerName": payer_name,
        "serviceStart": service_start,
        "serviceEnd": service_end,
        "middleName": middle_name,
        "gender": gender,
        "ssn": ssn,
        "city": city,
        "state": state,
        "zip": zip,
        "groupNumber": group_number,
        "serviceTypeCode": service_type_code,
        "providerLastName": provider_last_name,
        "providerFirstName": provider_first_name,
        "taxIdNumber": tax_id_number,
        "providerNameID": provider_name_id,
        "npi": npi,
        "corporateTaxOwnerID": corporate_tax_owner_id,
        "corporateTaxOwnerName": corporate_tax_owner_name,
        "organizationName": organization_name,
        "organizationID": organization_id,
        "searchOption": search_option,
        "identifyServiceLevelDeductible": identify_service_level_deductible
    }
    
    # Remove None values from the body
    body = {k: v for k, v in body.items() if v is not None}

    # Log the request body
    MediLink_ConfigLoader.log("Request body: {}".format(json.dumps(body, indent=4)), level="DEBUG")

    return client.make_api_call(endpoint_name, 'POST', url_extension, params=None, data=body)

def get_eligibility_super_connector(client, payer_id, provider_last_name, search_option, date_of_birth, member_id, npi, 
                                   first_name=None, last_name=None, payer_label=None, payer_name=None, service_start=None, service_end=None, 
                                   middle_name=None, gender=None, ssn=None, city=None, state=None, zip=None, group_number=None, 
                                   service_type_code=None, provider_first_name=None, tax_id_number=None, provider_name_id=None, 
                                   corporate_tax_owner_id=None, corporate_tax_owner_name=None, organization_name=None, 
                                   organization_id=None, identify_service_level_deductible=True):
    """
    OPTUMAI eligibility (GraphQL) that maps to the same interface as get_eligibility_v3.
    This function does not perform legacy fallback; callers should invoke legacy v3 separately if desired.
    """
    # Ensure all required parameters have values
    if not all([client, payer_id, provider_last_name, search_option, date_of_birth, member_id, npi]):
        raise ValueError("All required parameters must have values: client, payer_id, provider_last_name, search_option, date_of_birth, member_id, npi")

    # Prefer OPTUMAI endpoint if configured, otherwise fall back to legacy UHCAPI v3 (REST)
    try:
        endpoints_cfg = client.config['MediLink_Config']['endpoints']
    except Exception:
        endpoints_cfg = {}

    endpoint_name = None
    url_extension = None

    try:
        optumai_cfg = endpoints_cfg.get('OPTUMAI', {})
        optumai_additional = optumai_cfg.get('additional_endpoints', {}) if isinstance(optumai_cfg, dict) else {}
        optumai_url = optumai_additional.get('eligibility_optumai')
        if optumai_cfg and optumai_cfg.get('api_url') and optumai_url:
            endpoint_name = 'OPTUMAI'
            url_extension = optumai_url
    except Exception:
        # Safe ignore; will fall back below
        pass

    if not endpoint_name:
        # No fallback from this function; surface configuration error
        raise ValueError("OPTUMAI eligibility endpoint not configured")

    # Validate payer_id against the selected endpoint's list
    # - If OPTUMAI is used, allow the augmented list (includes LIFE1, WELM2, etc.).
    # - If UHCAPI fallback is used, enforce strict UHC list only.
    valid_payer_ids = get_valid_payer_ids_for_endpoint(client, endpoint_name)
    if payer_id not in valid_payer_ids:
        raise ValueError("Invalid payer_id: {} for endpoint {}. Must be one of: {}".format(
            payer_id, endpoint_name, ", ".join(valid_payer_ids)))

    if not url_extension:
        raise ValueError("Eligibility endpoint not configured for {}".format(endpoint_name))

    # Debug/trace: indicate that OPTUMAI eligibility path is active (log only, no console print)
    # Wrap in try/except to handle OSError on Windows when logging stream flush fails
    try:
        MediLink_ConfigLoader.log(
            "Eligibility using OPTUMAI endpoint with path '{}'".format(url_extension),
            level="DEBUG",
            console_output=CONSOLE_LOGGING
        )
    except (OSError, IOError):
        # Windows logging stream flush can fail with OSError [Errno 22] - ignore silently
        pass
    except Exception:
        pass
    
    # Get provider TIN from config (using existing billing_provider_tin)
    from MediCafe.core_utils import extract_medilink_config
    medi = extract_medilink_config(client.config)
    provider_tin = medi.get('billing_provider_tin')
    if not provider_tin:
        raise ValueError("Provider TIN not found in configuration")
    # Normalize provider TIN to 9-digit numeric string
    try:
        provider_tin_str = ''.join([ch for ch in str(provider_tin) if ch.isdigit()])
        if len(provider_tin_str) == 9:
            provider_tin = provider_tin_str
        else:
            error_msg = "Provider TIN '{}' is not 9 digits after normalization (got {} digits)".format(
                provider_tin, len(provider_tin_str))
            MediLink_ConfigLoader.log(error_msg, level="WARNING", console_output=CONSOLE_LOGGING)
            raise ValueError(error_msg)
    except ValueError:
        # Re-raise ValueError (validation failure)
        raise
    except Exception as e:
        # Other exceptions - log and raise as ValueError
        MediLink_ConfigLoader.log(
            "Error normalizing provider TIN: {}".format(str(e)),
            level="WARNING",
            console_output=CONSOLE_LOGGING
        )
        raise ValueError("Provider TIN normalization failed: {}".format(str(e)))
    
    # Validate service dates format if provided (should be ISO 8601 YYYY-MM-DD)
    try:
        from datetime import datetime
    except ImportError:
        datetime = None
    
    if service_start and datetime:
        try:
            service_start_str = str(service_start).strip()
            # Validate ISO date format
            datetime.strptime(service_start_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            MediLink_ConfigLoader.log(
                "Warning: service_start '{}' is not in YYYY-MM-DD format, but continuing anyway".format(
                    str(service_start)[:20]  # Limit length
                ),
                level="WARNING",
                console_output=CONSOLE_LOGGING
            )
        except Exception as e:
            MediLink_ConfigLoader.log(
                "Warning: Error validating service_start format: {}".format(str(e)),
                level="WARNING",
                console_output=CONSOLE_LOGGING
            )
    
    if service_end and datetime:
        try:
            service_end_str = str(service_end).strip()
            # Validate ISO date format
            datetime.strptime(service_end_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            MediLink_ConfigLoader.log(
                "Warning: service_end '{}' is not in YYYY-MM-DD format, but continuing anyway".format(
                    str(service_end)[:20]  # Limit length
                ),
                level="WARNING",
                console_output=CONSOLE_LOGGING
            )
        except Exception as e:
            MediLink_ConfigLoader.log(
                "Warning: Error validating service_end format: {}".format(str(e)),
                level="WARNING",
                console_output=CONSOLE_LOGGING
            )
    
    # Construct GraphQL query variables using the consolidated module
    # Include service dates when provided (needed to determine active policy at time of service)
    # Only pass service dates if they have actual values (not None and not empty string)
    graphql_kwargs = {
        'member_id': member_id,
        'date_of_birth': date_of_birth,
        'payer_id': payer_id,
        'provider_last_name': provider_last_name,
        'provider_npi': npi
    }
    # Add service dates only if provided (safe to omit if None or empty)
    if service_start:
        graphql_kwargs['service_start_date'] = service_start
    if service_end:
        graphql_kwargs['service_end_date'] = service_end
    # Add group number only when available (optional disambiguator for multi-plan cases)
    if group_number:
        try:
            graphql_kwargs['group_number'] = str(group_number).strip()
        except Exception:
            # If normalization fails, skip group number rather than sending bad data
            pass
    
    graphql_variables = MediLink_GraphQL.build_eligibility_variables(**graphql_kwargs)
    
    # Validate NPI format (should be 10 digits)
    if 'providerNPI' in graphql_variables:
        npi_value = graphql_variables['providerNPI']
        if not npi_value.isdigit() or len(npi_value) != 10:
            MediLink_ConfigLoader.log("Warning: NPI '{}' is not 10 digits, but continuing anyway".format(npi_value), level="WARNING")
    
    # Build GraphQL request using the consolidated module
    # Hardcoded switch to use sample data for testing
    USE_SAMPLE_DATA = False  # Set to False to use constructed data
    
    if USE_SAMPLE_DATA:
        # Use the sample data from swagger documentation
        graphql_body = MediLink_GraphQL.get_sample_eligibility_request()
        MediLink_ConfigLoader.log("Using SAMPLE DATA from swagger documentation", level="INFO")
    else:
        # Build GraphQL request with actual data using consolidated module
        # OPTUMAI now uses an enriched query aligned to production schema
        try:
            if endpoint_name == 'OPTUMAI' and hasattr(MediLink_GraphQL, 'build_optumai_enriched_request'):
                graphql_body = MediLink_GraphQL.build_optumai_enriched_request(graphql_variables)
                try:
                    MediLink_ConfigLoader.log("Using OPTUMAI ENRICHED GraphQL request", level="DEBUG")
                except (OSError, IOError):
                    # Windows logging stream flush can fail - ignore silently
                    pass
            else:
                graphql_body = MediLink_GraphQL.build_eligibility_request(graphql_variables)
                try:
                    MediLink_ConfigLoader.log("Using CONSTRUCTED DATA with consolidated GraphQL module", level="INFO")
                except (OSError, IOError):
                    # Windows logging stream flush can fail - ignore silently
                    pass
        except Exception:
            graphql_body = MediLink_GraphQL.build_eligibility_request(graphql_variables)
            try:
                MediLink_ConfigLoader.log("Fallback to standard GraphQL request body", level="WARNING")
            except (OSError, IOError):
                # Windows logging stream flush can fail - ignore silently
                pass
        
        # Compare with sample data for debugging
        sample_data = MediLink_GraphQL.get_sample_eligibility_request()
        MediLink_ConfigLoader.log("Sample data structure: {}".format(json.dumps(sample_data, indent=2)), level="DEBUG")
        MediLink_ConfigLoader.log("Constructed data structure: {}".format(json.dumps(graphql_body, indent=2)), level="DEBUG")
        
        # Compare key differences
        sample_vars = sample_data['variables']['input']
        constructed_vars = graphql_body['variables']['input']
        
        # Log differences in variables
        for key in set(sample_vars.keys()) | set(constructed_vars.keys()):
            sample_val = sample_vars.get(key)
            constructed_val = constructed_vars.get(key)
            if sample_val != constructed_val:
                MediLink_ConfigLoader.log("Variable difference - {}: sample='{}', constructed='{}'".format(
                    key, sample_val, constructed_val), level="DEBUG")
    
    # Log the GraphQL request
    MediLink_ConfigLoader.log("GraphQL request body: {}".format(json.dumps(graphql_body, indent=2)), level="DEBUG")
    MediLink_ConfigLoader.log("GraphQL variables: {}".format(json.dumps(graphql_variables, indent=2)), level="DEBUG")
    
    # Add required headers for Super Connector
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'tin': str(provider_tin)  # Ensure TIN is a string (used for legacy UHC super connector)
    }

    # OPTUMAI requires 'providertaxid' header (mapped from billing_provider_tin)
    try:
        if endpoint_name == 'OPTUMAI' and provider_tin:
            # OPTUMAI expects providerTaxId; remove legacy 'tin' header to avoid confusion
            if 'tin' in headers:
                try:
                    del headers['tin']
                except Exception:
                    pass
            headers['providerTaxId'] = str(provider_tin)
            # Add trace header for observability (optional per spec)
            try:
                corr_id = 'mc-{}'.format(int(time.time() * 1000))
            except Exception:
                corr_id = 'mc-{}'.format(int(time.time()))
            headers['x-optum-consumer-correlation-id'] = corr_id
    except Exception:
        pass
    
    # Only add env header when using sample data
    if USE_SAMPLE_DATA:
        headers['env'] = 'sandbox'
    
    # Remove None values from headers
    headers = {k: v for k, v in headers.items() if v is not None}
    
    # Log the final headers being sent
    MediLink_ConfigLoader.log("Final headers being sent: {}".format(json.dumps(headers, indent=2)), level="DEBUG")
    
    # Make the GraphQL API call with enhanced error diagnostics for endpoint failures
    try:
        response = client.make_api_call(endpoint_name, 'POST', url_extension, params=None, data=graphql_body, headers=headers)
    except Exception as e:
        # Check if this is a GraphQL validation error (ED270BR, BACKEND_VALIDATION_FAILED)
        error_str = str(e)
        is_validation_error = False
        validation_terms = ["BACKEND_VALIDATION_FAILED", "ED270BR", "mandatory attributes", "Bad request"]
        for term in validation_terms:
            if term in error_str:
                is_validation_error = True
                break
        
        # Enhanced diagnostics for validation errors
        if is_validation_error:
            # Log sanitized request payload for diagnostics (no PHI)
            try:
                # Extract variables from GraphQL body for diagnostics
                # Defensive check: graphql_body should be defined, but handle edge case where exception occurred during construction
                try:
                    graphql_body_ref = graphql_body
                except NameError:
                    # graphql_body not defined - exception occurred before it was created
                    graphql_body_ref = {}
                graphql_vars = graphql_body_ref.get('variables', {}).get('input', {}) if isinstance(graphql_body_ref, dict) else {}
                
                # Required fields per OPTUMAI spec
                required_fields = ['payerId', 'providerLastName', 'memberId', 'dateOfBirth']
                optional_but_important = ['providerNPI']
                
                # Check which required fields are present
                present_fields = []
                missing_fields = []
                for field in required_fields:
                    if field in graphql_vars and graphql_vars[field]:
                        present_fields.append(field)
                    else:
                        missing_fields.append(field)
                
                # Check providerTaxId header
                provider_tax_id_present = 'providerTaxId' in headers and headers.get('providerTaxId')
                
                # Build diagnostic message
                diag_parts = [
                    "GraphQL validation error (ED270BR) - Missing mandatory attributes",
                    "Required fields present: {}".format(", ".join(present_fields) if present_fields else "none"),
                    "Required fields missing: {}".format(", ".join(missing_fields) if missing_fields else "none"),
                    "providerTaxId header: {}".format("present" if provider_tax_id_present else "missing"),
                ]
                
                # Add optional field status
                if 'providerNPI' in graphql_vars and graphql_vars.get('providerNPI'):
                    diag_parts.append("providerNPI: present")
                else:
                    diag_parts.append("providerNPI: missing")
                
                # Log field values (sanitized - no full values, just presence and lengths)
                field_summary = []
                for field in required_fields + optional_but_important:
                    if field in graphql_vars:
                        val = graphql_vars[field]
                        if isinstance(val, str):
                            field_summary.append("{}: len={}".format(field, len(val)))
                        elif val:
                            field_summary.append("{}: present".format(field))
                        else:
                            field_summary.append("{}: empty".format(field))
                    else:
                        field_summary.append("{}: missing".format(field))
                
                diag_parts.append("Field summary: {}".format("; ".join(field_summary)))
                
                diagnostic_msg = " | ".join(diag_parts)
                MediLink_ConfigLoader.log(diagnostic_msg, level="WARNING", console_output=CONSOLE_LOGGING)
                
                # Also print a concise version
                try:
                    print("[Eligibility] GraphQL validation error - Missing: {} | Check logs for details".format(
                        ", ".join(missing_fields) if missing_fields else "unknown"
                    ))
                except Exception:
                    pass
            except Exception as diag_exc:
                # If diagnostics fail, log basic error
                MediLink_ConfigLoader.log(
                    "GraphQL validation error diagnostics failed: {}".format(str(diag_exc)),
                    level="WARNING",
                    console_output=CONSOLE_LOGGING
                )
        
        # Best-effort diagnostics without exposing secrets or PHI
        try:
            status = getattr(getattr(e, 'response', None), 'status_code', None)
            diag = "Eligibility request to {}{} failed".format(
                endpoint_name and (endpoint_name + " ") or "", url_extension)
            if status is not None:
                diag += " with status {}".format(status)
            if not is_validation_error:  # Don't duplicate log for validation errors
                MediLink_ConfigLoader.log(diag, level="ERROR", console_output=CONSOLE_LOGGING)
                try:
                    print("[Eligibility] Request failed (status: {}). See logs for details.".format(status))
                except Exception:
                    pass
        except Exception:
            pass

        # No fallback from this function; re-raise so callers can handle or try legacy explicitly
        raise
    
    # Transform GraphQL response to match REST API format
    # This ensures the calling code doesn't know the difference
    transformed_response = MediLink_GraphQL.transform_eligibility_response(response)

    # Post-transform sanity: if non-200, emit brief diagnostics to aid validation sessions
    try:
        sc_status = transformed_response.get('statuscode') if isinstance(transformed_response, dict) else None
        if sc_status and sc_status != '200':
            msg = transformed_response.get('message')
            MediLink_ConfigLoader.log(
                "OPTUMAI eligibility transformed response status: {} msg: {}".format(sc_status, msg),
                level="INFO",
                console_output=CONSOLE_LOGGING
            )
            raw_errs = None
            try:
                raw = transformed_response.get('rawGraphQLResponse', {})
                raw_errs = raw.get('errors')
            except Exception:
                raw_errs = None
            if raw_errs:
                try:
                    first_err = raw_errs[0]
                    code = first_err.get('code') or first_err.get('extensions', {}).get('code')
                    desc = first_err.get('description') or first_err.get('message')
                    print("[Eligibility] GraphQL error code={} desc={}".format(code, desc))
                    
                    # Enhanced diagnostics for validation errors
                    if code and ("BACKEND_VALIDATION_FAILED" in str(code) or "ED270BR" in str(desc) or "mandatory attributes" in str(desc)):
                        # Log which fields were sent vs required
                        try:
                            # Get the variables that were sent (defensive check for scope)
                            try:
                                graphql_body_ref = graphql_body
                            except NameError:
                                graphql_body_ref = {}
                            try:
                                headers_ref = headers
                            except NameError:
                                headers_ref = {}
                            
                            graphql_vars = graphql_body_ref.get('variables', {}).get('input', {}) if isinstance(graphql_body_ref, dict) else {}
                            required_fields = ['payerId', 'providerLastName', 'memberId', 'dateOfBirth']
                            
                            present = [f for f in required_fields if f in graphql_vars and graphql_vars[f]]
                            missing = [f for f in required_fields if f not in graphql_vars or not graphql_vars[f]]
                            
                            diag_msg = "Validation error details - Present: {} | Missing: {} | providerTaxId header: {}".format(
                                ", ".join(present) if present else "none",
                                ", ".join(missing) if missing else "none",
                                "present" if headers_ref.get('providerTaxId') else "missing"
                            )
                            MediLink_ConfigLoader.log(diag_msg, level="WARNING", console_output=CONSOLE_LOGGING)
                        except Exception:
                            pass  # Don't fail if diagnostics can't be generated
                except Exception:
                    pass

            # Terminal self-help hints for auth/authorization cases
            # Non-throwing hint emitter (kept outside core logic path)
            def _emit_hint_for_status(status_str):
                try:
                    trace_id = transformed_response.get('traceId')
                    trace_info = " (Trace ID: {})".format(trace_id) if trace_id else ""
                    
                    if status_str == '401':
                        hint_parts = [
                            "[Eligibility] Hint: Authentication failed{}.".format(trace_info),
                            "Verify client credentials and subscription access in OPTUMAI portal.",
                            "Note: OPTUM auto-grants scopes via subscription - scope parameter is not required in token request.",
                            "See docs/OPTUMAI_TOKEN_SCOPE_INVESTIGATION.md for troubleshooting."
                        ]
                        print(" ".join(hint_parts))
                    elif status_str == '403':
                        hint_parts = [
                            "[Eligibility] Hint: Access denied{}.".format(trace_info),
                            "Verify providerTaxId/TIN and subscription permissions/roles for endpoint.",
                            "Check that client credentials have eligibility endpoint access enabled in OPTUMAI portal."
                        ]
                        print(" ".join(hint_parts))
                except Exception:
                    pass

            try:
                _emit_hint_for_status(str(sc_status))
            except Exception:
                pass
    except Exception:
        pass
    
    return transformed_response

def is_test_mode(client, body, endpoint_type):
    """
    Checks if Test Mode is enabled in the client's configuration and simulates the response if it is.

    :param client: An instance of APIClient
    :param body: The intended request body
    :param endpoint_type: The type of endpoint being accessed ('claim_submission' or 'claim_details')
    :return: A dummy response simulating the real API call if Test Mode is enabled, otherwise None
    """
    if client.config.get("MediLink_Config", {}).get("TestMode", True):
        print("Test Mode is enabled! API Call not executed.")
        print("\nIntended request body:", body)
        MediLink_ConfigLoader.log("Test Mode is enabled! Simulating 1 second delay for API response for {}.".format(endpoint_type), level="INFO")
        time.sleep(1)
        MediLink_ConfigLoader.log("Intended request body: {}".format(body), level="INFO")

        if endpoint_type == 'claim_submission':
            dummy_response = {
                "transactionId": "CS07180420240328013411240",  # This is the tID for the sandbox Claim Acknowledgement endpoint.
                "x12ResponseData": "ISA*00* *00* *ZZ*TEST1234567890 *33*TEST *210101*0101*^*00501*000000001*0*P*:~GS*HC*TEST1234567890*TEST*20210101*0101*1*X*005010X222A1~ST*837*000000001*005010X222A1~BHT*0019*00*00001*20210101*0101*CH~NM1*41*2*TEST SUBMITTER*****46*TEST~PER*IC*TEST CONTACT*TE*1234567890~NM1*40*2*TEST RECEIVER*****46*TEST~HL*1**20*1~NM1*85*2*TEST PROVIDER*****XX*1234567890~N3*TEST ADDRESS~N4*TEST CITY*TEST STATE*12345~REF*EI*123456789~PER*IC*TEST PROVIDER*TE*1234567890~NM1*87*2~N3*TEST ADDRESS~N4*TEST CITY*TEST STATE*12345~HL*2*1*22*0~SBR*P*18*TEST GROUP******CI~NM1*IL*1*TEST PATIENT****MI*123456789~N3*TEST ADDRESS~N4*TEST CITY*TEST STATE*12345~DMG*D8*19800101*M~NM1*PR*2*TEST INSURANCE*****PI*12345~CLM*TESTCLAIM*100***12:B:1*Y*A*Y*Y*P~REF*D9*TESTREFERENCE~HI*ABK:TEST~NM1*DN*1*TEST DOCTOR****XX*1234567890~LX*1~SV1*HC:TEST*100*UN*1***1~DTP*472*RD8*20210101-20210101~REF*6R*TESTREFERENCE~SE*30*000000001~GE*1*1~IEA*1*000000001~",
                "responseType": "dummy_response_837999",
                "message": "Test Mode: Claim validated and sent for further processing"
            }
        elif endpoint_type == 'claim_details':
            dummy_response = {
                "responseType": "dummy_response_277CA-CH",
                "x12ResponseData": "ISA*00* *00*  *ZZ*841162764 *ZZ*UB920086 *240318*0921*^*00501*000165687*0*T*:~GS*HN*841162764*UB920086*20240318*0921*0165687*X*005010X214~ST*277*000000006*005010X214~... SE*116*000000006~GE*1*0165687~IEA*1*000165687~",
                "statuscode": "000",
                "message:": ""
            }
        return dummy_response
    return None

def submit_uhc_claim(client, x12_request_data):
    """
    Submits a UHC claim and retrieves the claim acknowledgement details.
    
    This function first submits the claim using the provided x12 837p data. If the client is in Test Mode, 
    it returns a simulated response. If Test Mode is not enabled, it submits the claim and then retrieves 
    the claim acknowledgement details using the transaction ID from the initial response.
    
    NOTE: This function uses endpoints that may not be available in the new swagger version:
    - /Claims/api/claim-submission/v1 (claim submission)
    - /Claims/api/claim-details/v1 (claim acknowledgement)
    
    If these endpoints are deprecated in the new swagger, this function will need to be updated
    to use the new available endpoints.
    
    :param client: An instance of APIClient
    :param x12_request_data: The x12 837p data as a string
    :return: The final response containing the claim acknowledgement details or a dummy response if in Test Mode
    """
    # VERBOSE LOGGING FOR CLAIM SUBMISSION
    MediLink_ConfigLoader.log("=" * 80, level="INFO")
    MediLink_ConfigLoader.log("SUBMIT UHC CLAIM - VERBOSE DETAILS", level="INFO")
    MediLink_ConfigLoader.log("=" * 80, level="INFO")
    MediLink_ConfigLoader.log("X12 Request Data Length: {}".format(len(x12_request_data) if x12_request_data else 0), level="INFO")
    if x12_request_data:
        MediLink_ConfigLoader.log("X12 Request Data Preview (first 200 chars): {}".format(x12_request_data[:200]), level="INFO")
    MediLink_ConfigLoader.log("=" * 80, level="INFO")
    
    endpoint_name = 'UHCAPI'
    from MediCafe.core_utils import extract_medilink_config
    medi = extract_medilink_config(client.config)
    endpoints = medi.get('endpoints', {})
    claim_submission_url = endpoints.get(endpoint_name, {}).get('additional_endpoints', {}).get('claim_submission', '')
    claim_details_url = endpoints.get(endpoint_name, {}).get('additional_endpoints', {}).get('claim_details', '')
 
    MediLink_ConfigLoader.log("Claim Submission URL: {}".format(claim_submission_url), level="INFO")
    MediLink_ConfigLoader.log("Claim Details URL: {}".format(claim_details_url), level="INFO")
 
    # Headers for the request
    headers = {'Content-Type': 'application/json'} 
 
    # Request body for claim submission
    claim_body = {'x12RequestData': x12_request_data}
 
    MediLink_ConfigLoader.log("Claim Body Keys: {}".format(list(claim_body.keys())), level="INFO")
    MediLink_ConfigLoader.log("Headers: {}".format(json.dumps(headers, indent=2)), level="INFO")
 
    # Check if Test Mode is enabled and return simulated response if so
    test_mode_response = is_test_mode(client, claim_body, 'claim_submission')
    if test_mode_response:
        return test_mode_response
 
    # Make the API call to submit the claim
    try:
        MediLink_ConfigLoader.log("Making claim submission API call...", level="INFO")
        submission_response = client.make_api_call(endpoint_name, 'POST', claim_submission_url, data=claim_body, headers=headers)
        
        # Extract the transaction ID from the submission response
        transaction_id = submission_response.get('transactionId')
        if not transaction_id:
            raise ValueError("transactionId not found in the submission response")
        
        # Log the transaction ID for traceability
        MediLink_ConfigLoader.log("UHCAPI claim submission transactionId: {}".format(transaction_id), level="INFO")
        
        # Prepare the request body for the claim acknowledgement retrieval
        acknowledgement_body = {'transactionId': transaction_id}
 
        # Check if Test Mode is enabled and return simulated response if so
        test_mode_response = is_test_mode(client, acknowledgement_body, 'claim_details')
        if test_mode_response:
            return test_mode_response
 
        # Make the API call to retrieve the claim acknowledgement details
        acknowledgement_response = client.make_api_call(endpoint_name, 'POST', claim_details_url, data=acknowledgement_body, headers=headers)
        
        # Persist as unified ack event (best-effort)
        try:
            from MediCafe.submission_index import append_ack_event, ensure_submission_index
            cfg, _ = MediLink_ConfigLoader.load_configuration()
            receipts_root = extract_medilink_config(cfg).get('local_claims_path', None)
            if receipts_root:
                ensure_submission_index(receipts_root)
                status_text = ''
                try:
                    # Attempt to pull a readable status from the response
                    status_text = acknowledgement_response.get('status') or acknowledgement_response.get('message') or ''
                except Exception:
                    status_text = ''
                append_ack_event(
                    receipts_root,
                    '',  # claim_key unknown here
                    status_text,
                    'API-277',
                    'uhcapi',
                    {'transactionId': transaction_id},
                    'api_ack',
                    int(time.time())
                )
        except Exception:
            pass
        
        return acknowledgement_response
 
    except Exception as e:
        print("Error during claim processing: {}".format(e))
        raise

# -----------------------------------------------------------------------------
# Helper: Optional acknowledgment (277CA) test endpoint
# -----------------------------------------------------------------------------

def test_acknowledgment(client, transaction_id, config, endpoint_name='UHCAPI'):
    """
    Light-weight probe to test the claim acknowledgment endpoint (e.g., 277CA) if configured.
    - Reads endpoint URL from config['MediLink_Config']['endpoints'][endpoint_name]['ack_endpoint']
    - Posts/gets with {'transactionId': transaction_id} depending on endpoint requirement
    - Logs response; returns parsed JSON or text.

    Backward-compatible: If no ack endpoint configured, logs and returns None without failing.
    """
    try:
        ack_url = (
            config.get('MediLink_Config', {})
                  .get('endpoints', {})
                  .get(endpoint_name, {})
                  .get('ack_endpoint')
        )
        if not ack_url:
            MediLink_ConfigLoader.log("Ack endpoint not configured for {}. Skipping acknowledgment test.".format(endpoint_name), level="INFO")
            return None

        payload = {"transactionId": transaction_id}
        headers = {"Content-Type": "application/json"}
        headers = client.add_environment_headers(headers, endpoint_name) if hasattr(client, 'add_environment_headers') else headers
        MediLink_ConfigLoader.log("Testing acknowledgment endpoint: {} payload={}".format(ack_url, payload), level="DEBUG")

        # Use generic request helper if available; otherwise fall back to requests
        try:
            response = client._request('post', ack_url, data=json.dumps(payload), headers=headers)  # type: ignore[attr-defined]
        except Exception:
            import requests as _rq
            response = _rq.post(ack_url, data=json.dumps(payload), headers=headers)
        
        try:
            content = response.json()
        except Exception:
            content = getattr(response, 'text', str(response))
        MediLink_ConfigLoader.log("Ack response: {}".format(content), level="INFO")
        return content
    except Exception as e:
        MediLink_ConfigLoader.log("Ack test failed: {}".format(e), level="ERROR")
        return None

if __name__ == "__main__":
    # Use factory for consistency but fallback to direct instantiation for testing
    try:
        from MediCafe.core_utils import get_api_client
        client = get_api_client()
        if client is None:
            client = APIClient()
    except ImportError:
        client = APIClient()
    
    # Define a configuration to enable or disable tests
    test_config = {
        'test_fetch_payer_name': False,
        'test_claim_summary': False,
        'test_eligibility': False,
        'test_eligibility_v3': False,
        'test_eligibility_super_connector': False,
        'test_claim_submission': False,
    }
    
    try:
        api_test_cases = client.config['MediLink_Config']['API Test Case']
        
        # Test 1: Fetch Payer Name
        if test_config.get('test_fetch_payer_name', False):
            try:
                for case in api_test_cases:
                    payer_name = fetch_payer_name_from_api(client, case['payer_id'], client.config)
                    print("*** TEST API: Payer Name: {}".format(payer_name))
            except Exception as e:
                print("*** TEST API: Error in Fetch Payer Name Test: {}".format(e))
        
        # Test 2: Get Claim Summary
        if test_config.get('test_claim_summary', False):
            try:
                for case in api_test_cases:
                    claim_summary = get_claim_summary_by_provider(client, case['provider_tin'], '05/01/2024', '06/23/2024', case['payer_id'])
                    print("TEST API: Claim Summary: {}".format(claim_summary))
            except Exception as e:
                print("TEST API: Error in Claim Summary Test: {}".format(e))
        
        # Test 3: Get Eligibility
        if test_config.get('test_eligibility', False):
            try:
                for case in api_test_cases:
                    eligibility = get_eligibility(client, case['payer_id'], case['provider_last_name'], case['search_option'], 
                                                  case['date_of_birth'], case['member_id'], case['npi'])
                    print("TEST API: Eligibility: {}".format(eligibility))
            except Exception as e:
                print("TEST API: Error in Eligibility Test: {}".format(e))

        # Test 4: Get Eligibility v3
        if test_config.get('test_eligibility_v3', False):
            try:
                for case in api_test_cases:
                    eligibility_v3 = get_eligibility_v3(client, payer_id=case['payer_id'], provider_last_name=case['provider_last_name'], 
                                                        search_option=case['search_option'], date_of_birth=case['date_of_birth'], 
                                                        member_id=case['member_id'], npi=case['npi'])
                    print("TEST API: Eligibility v3: {}".format(eligibility_v3))
            except Exception as e:
                print("TEST API: Error in Eligibility v3 Test: {}".format(e))

        # Test 5: Get Eligibility Super Connector (GraphQL)
        if test_config.get('test_eligibility_super_connector', False):
            try:
                for case in api_test_cases:
                    eligibility_super_connector = get_eligibility_super_connector(client, payer_id=case['payer_id'], provider_last_name=case['provider_last_name'], 
                                                                                search_option=case['search_option'], date_of_birth=case['date_of_birth'], 
                                                                                member_id=case['member_id'], npi=case['npi'])
                    print("TEST API: Eligibility Super Connector: {}".format(eligibility_super_connector))
            except Exception as e:
                print("TEST API: Error in Eligibility Super Connector Test: {}".format(e))

        """
        # Example of iterating over multiple patients (if needed)
        patients = [
            {'payer_id': '87726', 'provider_last_name': 'VIDA', 'search_option': 'MemberIDDateOfBirth', 'date_of_birth': '1980-01-01', 'member_id': '123456789', 'npi': '9876543210'},
            {'payer_id': '87726', 'provider_last_name': 'SMITH', 'search_option': 'MemberIDDateOfBirth', 'date_of_birth': '1970-02-02', 'member_id': '987654321', 'npi': '1234567890'},
            # Add more patients as needed
        ]

        for patient in patients:
            try:
                eligibility = get_eligibility(client, patient['payer_id'], patient['provider_last_name'], patient['search_option'], patient['date_of_birth'], patient['member_id'], patient['npi'])
                print("Eligibility for {}: {}".format(patient['provider_last_name'], eligibility))
            except Exception as e:
                print("Error in getting eligibility for {}: {}".format(patient['provider_last_name'], e))
        """
        # Test 6: UHC Claim Submission
        if test_config.get('test_claim_submission', False):
            try:
                x12_request_data = (
                    "ISA*00* *00* *ZZ*BRT219991205 *33*87726 *170417*1344*^*00501*019160001*0*P*:~GS*HC*BRT219991205*B2BRTA*20170417*134455*19160001*X*005010X222A1~ST*837*000000001*005010X222A1~BHT*0019*00*00001*20170417*134455*CH~NM1*41*2*B00099999819*****46*BB2B~PER*IC*NO NAME*TE*1234567890~NM1*40*2*TIGER*****46*87726~HL*1**20*1~NM1*85*2*XYZ ADDRESS*****XX*1073511762~N3*123 CITY#680~N4*STATE*TG*98765~REF*EI*943319804~PER*IC*XYZ ADDRESS*TE*8008738385*TE*9142862043*FX*1234567890~NM1*87*2~N3*PO BOX 277500~N4*STATE*TS*303847000~HL*2*1*22*0~SBR*P*18*701648******CI~NM1*IL*1*FNAME*LNAME****MI*00123456789~N3*2020 CITY~N4*STATE*TG*80001~DMG*D8*19820220*M~NM1*PR*2*PROVIDER XYZ*****PI*87726~\nCLM*TOSRTA-SPL1*471***12:B:1*Y*A*Y*Y*P~REF*D9*H4HZMH0R4P0104~HI*ABK:Z12~NM1*DN*1*DN*SKO****XX*1255589300~LX*1~SV1*HC:73525*471*UN*1***1~DTP*472*RD8*0190701-20190701~REF*6R*2190476543Z1~SE*30*000000001~GE*1*19160001~IEA*1*019160001~"
                )
                response = submit_uhc_claim(client, x12_request_data)
                print("\nTEST API: Claim Submission Response:\n", response)
            except Exception as e:
                print("\nTEST API: Error in Claim Submission Test:\n", e)
    
    except Exception as e:
        print("TEST API: Unexpected Error: {}".format(e))
