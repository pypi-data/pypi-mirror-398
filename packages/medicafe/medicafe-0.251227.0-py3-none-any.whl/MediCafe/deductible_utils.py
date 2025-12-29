# MediCafe/deductible_utils.py
"""
Deductible utility functions for MediCafe
This module contains shared functionality for eligibility and deductible processing
to avoid code duplication and leverage existing MediCafe infrastructure.

COMPATIBILITY: Python 3.4.4 and Windows XP compatible
ASCII-only encoding required

API RESPONSE PARSER DEBUGGING STATUS:
This module addresses the TODO items from the original MediLink_Deductible.py commentary:

ADDRESSED:
 Enhanced logging with log_api_response_structure() function
 Schema validation with validate_api_response_schema() function  
 Response compatibility analysis with analyze_response_compatibility()
 Robust null checking and fallback mechanisms
 Detailed debugging logs for parser functions
 Graceful handling of missing fields and schema mismatches
 Centralized parser functions to eliminate duplication

PENDING (API Developer Fix Required):
 Complete Super Connector API response schema (API developers working on fix)
 Full response structure validation (depends on API fix)
 Comprehensive test cases (requires stable API responses)

SEE ALSO: docs/API_RESPONSE_DEBUGGING_ROADMAP.md for detailed status and roadmap

IMPLEMENTATION NOTES:
- Primary path uses CSV/crosswalk as authoritative source (O(N) complexity)
- API probing retained behind DEBUG_MODE_PAYER_PROBE toggle for troubleshooting
- All parser functions include enhanced logging and error handling
- Schema validation helps identify API response format changes
- Compatibility analysis provides detailed debugging information
"""

import os, sys, json
from datetime import datetime

try:
    from MediCafe.network_route_helpers import ROUTE_404_HINT
except ImportError:
    ROUTE_404_HINT = "Hint: verify endpoint configuration and rerun after DNS flush (ipconfig /flushdns on Windows XP)."

# =============================================================================
# LIGHTWEIGHT DIAGNOSTICS HELPERS (3.4.4 compatible)
# =============================================================================

def classify_api_failure(exc, context):
    """
    Classify common API failure cases into a short (code, message) tuple.
    Codes: TIMEOUT, CONN_ERR, AUTH_FAIL, INVALID_PAYER, MISCONFIG, NON_200, NO_DATA, ROUTE_404, UNKNOWN
    """
    code = 'UNKNOWN'
    try:
        detail = str(exc)
    except Exception:
        detail = ''
    try:
        detail_lower = detail.lower()
    except Exception:
        detail_lower = ''
    try:
        ctx = str(context)
    except Exception:
        ctx = 'API'
    try:
        # Lazy import to avoid hard dependency if requests missing
        try:
            import requests  # noqa
        except Exception:
            requests = None  # type: ignore

        if requests and hasattr(requests, 'exceptions'):
            if isinstance(exc, requests.exceptions.Timeout):
                code = 'TIMEOUT'
            elif isinstance(exc, requests.exceptions.ConnectionError):
                code = 'CONN_ERR'
            elif isinstance(exc, requests.exceptions.HTTPError):
                # HTTPError: try to extract status
                try:
                    status = getattr(getattr(exc, 'response', None), 'status_code', None)
                except Exception:
                    status = None
                code = 'NON_200' if status and status != 200 else 'UNKNOWN'
        # String heuristics as fallbacks
        if 'no route matched' in detail_lower:
            code = 'ROUTE_404'
        elif 'invalid payer_id' in detail_lower:
            code = 'INVALID_PAYER'
        elif ('no access token' in detail_lower) or ('token' in detail_lower):
            code = 'AUTH_FAIL'
        elif ('eligibility endpoint not configured' in detail_lower) or ('endpoint' in detail_lower and 'configured' in detail_lower):
            code = 'MISCONFIG'
    except Exception:
        code = 'UNKNOWN'
    message = "{} failure [{}]: {}".format(ctx or 'API', code, detail)
    if code == 'ROUTE_404':
        message += " | {}".format(ROUTE_404_HINT)
    return code, message

def is_ok_200(value):
    """Return True if value represents HTTP 200 in either int or string form."""
    try:
        return str(value).strip() == '200'
    except Exception:
        return False

# Use core utilities for standardized imports
try:
    from MediCafe.core_utils import get_shared_config_loader
    MediLink_ConfigLoader = get_shared_config_loader()
except ImportError:
    # Fallback for standalone usage
    MediLink_ConfigLoader = None

# Import existing date utilities from MediBot
try:
    from MediBot.MediBot_Preprocessor_lib import OptimizedDate
    HAS_OPTIMIZED_DATE = True
except ImportError:
    HAS_OPTIMIZED_DATE = False

# Import existing date utilities from MediLink
try:
    from MediLink.MediLink_837p_utilities import convert_date_format
    HAS_DATE_UTILS = True
except ImportError:
    HAS_DATE_UTILS = False

# =============================================================================
# DATE VALIDATION UTILITIES
# =============================================================================

def validate_and_format_date(date_str):
    """
    Enhanced date parsing that handles ambiguous formats intelligently.
    For ambiguous formats like MM/DD vs DD/MM, uses heuristics to determine the most likely interpretation.
    
    COMPATIBILITY: Python 3.4.4 and Windows XP compatible
    ASCII-only encoding required
    """
    import re

    # First, try unambiguous formats (4-digit years, month names, etc.)
    unambiguous_formats = [
        '%Y-%m-%d',    # 1990-01-15
        '%d-%b-%Y',    # 15-Jan-1990
        '%d %b %Y',    # 15 Jan 1990
        '%b %d, %Y',   # Jan 15, 1990
        '%b %d %Y',    # Jan 15 1990
        '%B %d, %Y',   # January 15, 1990
        '%B %d %Y',    # January 15 1990
        '%Y/%m/%d',    # 1990/01/15
        '%Y%m%d',      # 19900115
        '%y%m%d',      # 900115 (unambiguous compact format)
    ]

    # Try unambiguous formats first
    for fmt in unambiguous_formats:
        try:
            if '%y' in fmt:
                parsed_date = datetime.strptime(date_str, fmt)
                if parsed_date.year < 50:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                elif parsed_date.year < 100:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
                return parsed_date.strftime('%Y-%m-%d')
            else:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue

    # Handle potentially ambiguous formats with smart heuristics
    # Check if it's a MM/DD/YYYY or DD/MM/YYYY pattern
    ambiguous_pattern = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', date_str)
    if ambiguous_pattern:
        first_num, second_num, year = map(int, ambiguous_pattern.groups())

        # If first number > 12, it must be DD/MM/YYYY format
        if first_num > 12:
            try:
                return datetime(int(year), int(second_num), int(first_num)).strftime('%Y-%m-%d')
            except ValueError:
                return None

        # If second number > 12, it must be MM/DD/YYYY format
        elif second_num > 12:
            try:
                return datetime(int(year), int(first_num), int(second_num)).strftime('%Y-%m-%d')
            except ValueError:
                return None

        # Both numbers could be valid months (1-12), need to make an educated guess
        else:
            # Preference heuristic: In US context, MM/DD/YYYY is more common
            # But also consider: if first number is 1-12 and second is 1-31, both are possible
            # Default to MM/DD/YYYY for US-centric systems, but this could be configurable
            try:
                # Try MM/DD/YYYY first (US preference)
                return datetime(int(year), int(first_num), int(second_num)).strftime('%Y-%m-%d')
            except ValueError:
                try:
                    # If that fails, try DD/MM/YYYY
                    return datetime(int(year), int(second_num), int(first_num)).strftime('%Y-%m-%d')
                except ValueError:
                    return None

    # Handle 2-digit year ambiguous formats
    ambiguous_2digit_pattern = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{2})$', date_str)
    if ambiguous_2digit_pattern:
        first_num, second_num, year = map(int, ambiguous_2digit_pattern.groups())

        # Apply same logic as above, but handle 2-digit year
        year = 2000 + year if year < 50 else 1900 + year

        if first_num > 12:
            try:
                return datetime(year, second_num, first_num).strftime('%Y-%m-%d')
            except ValueError:
                return None
        elif second_num > 12:
            try:
                return datetime(year, first_num, second_num).strftime('%Y-%m-%d')
            except ValueError:
                return None
        else:
            # Default to MM/DD/YY (US preference)
            try:
                return datetime(year, first_num, second_num).strftime('%Y-%m-%d')
            except ValueError:
                try:
                    return datetime(year, second_num, first_num).strftime('%Y-%m-%d')
                except ValueError:
                    return None

    # Try remaining formats that are less likely to be ambiguous
    remaining_formats = [
        '%m-%d-%Y',    # 01-15-1990
        '%d-%m-%Y',    # 15-01-1990
        '%d/%m/%Y',    # 15/01/1990
        '%m-%d-%y',    # 01-15-90
        '%d-%m-%y',    # 15-01-90
        '%b %d, %y',   # Jan 15, 90
        '%b %d %y',    # Jan 15 90
        '%y/%m/%d',    # 90/01/15
        '%y-%m-%d',    # 90-01-15
    ]

    for fmt in remaining_formats:
        try:
            if '%y' in fmt:
                parsed_date = datetime.strptime(date_str, fmt)
                if parsed_date.year < 50:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                elif parsed_date.year < 100:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
                return parsed_date.strftime('%Y-%m-%d')
            else:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue

    return None

# =============================================================================
# API RESPONSE DEBUGGING AND LOGGING UTILITIES
# =============================================================================

def log_api_response_structure(response, context="", level="DEBUG"):
    """
    Enhanced logging function to analyze API response structure.
    This addresses the TODO item for API Response Parser Debugging.
    
    Args:
        response: API response data to analyze
        context: Context string for logging (e.g., "Super Connector", "Legacy")
        level: Logging level (DEBUG, INFO, WARNING)
    """
    if not MediLink_ConfigLoader:
        return
    
    try:
        MediLink_ConfigLoader.log("=" * 60, level=level)
        MediLink_ConfigLoader.log("API RESPONSE STRUCTURE ANALYSIS - {}".format(context), level=level)
        MediLink_ConfigLoader.log("=" * 60, level=level)
        
        if response is None:
            MediLink_ConfigLoader.log("Response is None", level=level)
            return
        
        # Log top-level structure
        MediLink_ConfigLoader.log("Response type: {}".format(type(response)), level=level)
        if isinstance(response, dict):
            MediLink_ConfigLoader.log("Top-level keys: {}".format(list(response.keys())), level=level)
            
            # Check for key response indicators
            if "rawGraphQLResponse" in response:
                MediLink_ConfigLoader.log("Detected Super Connector format (has rawGraphQLResponse)", level=level)
            if "memberPolicies" in response:
                MediLink_ConfigLoader.log("Detected Legacy format (has memberPolicies)", level=level)
            
            # Log response size
            response_str = json.dumps(response, indent=2)
            MediLink_ConfigLoader.log("Response size: {} characters".format(len(response_str)), level=level)
            
            # Log first 1000 characters for debugging
            if len(response_str) > 1000:
                MediLink_ConfigLoader.log("Response preview (first 1000 chars): {}".format(response_str[:1000]), level=level)
                MediLink_ConfigLoader.log("... (truncated)", level=level)
            else:
                MediLink_ConfigLoader.log("Full response: {}".format(response_str), level=level)
        
        MediLink_ConfigLoader.log("=" * 60, level=level)
        
    except Exception as e:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Error in log_api_response_structure: {}".format(str(e)), level="ERROR")

def validate_api_response_schema(response, expected_schema, context=""):
    """
    Validate API response against expected schema.
    This addresses the TODO item for schema validation.
    
    Args:
        response: API response data to validate
        expected_schema: Dictionary defining expected structure
        context: Context string for validation
        
    Returns:
        tuple: (is_valid, validation_errors)
    """
    if not response or not expected_schema:
        return True, []
    
    validation_errors = []
    
    try:
        for key, expected_type in expected_schema.items():
            if key not in response:
                validation_errors.append("Missing required key: {}".format(key))
            elif not isinstance(response[key], expected_type):
                validation_errors.append("Key '{}' has wrong type. Expected {}, got {}".format(
                    key, expected_type.__name__, type(response[key]).__name__))
        
        if validation_errors and MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Schema validation failed for {}: {}".format(context, validation_errors), level="WARNING")
        
        return len(validation_errors) == 0, validation_errors
        
    except Exception as e:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Error in validate_api_response_schema: {}".format(str(e)), level="ERROR")
        return False, ["Validation error: {}".format(str(e))]

# Define expected schemas for different API response formats
LEGACY_RESPONSE_SCHEMA = {
    "memberPolicies": list,
    "status": str
}

# TODO (API DEVELOPER FIX REQUIRED):
# This schema is incomplete and needs to be updated once API developers
# complete the Super Connector response format fixes.
# 
# CURRENT ISSUES:
# - Super Connector API responses are not consistently structured
# - Some required fields may be missing or have different names
# - Response format may vary between different payer IDs
#
# FUTURE ENHANCEMENTS NEEDED:
# - Complete schema definition once API is stable
# - Add field-level validation for all required data
# - Implement schema version detection for API updates
# - Add support for payer-specific response variations
SUPER_CONNECTOR_RESPONSE_SCHEMA = {
    "rawGraphQLResponse": dict,
    "statuscode": str
    # Additional fields will be added once API response format is finalized
}

def analyze_response_compatibility(response, context=""):
    """
    Analyze response compatibility with our parser functions.
    This helps identify schema mismatches mentioned in the TODO.
    
    Args:
        response: API response to analyze
        context: Context string for analysis
        
    Returns:
        dict: Analysis results with compatibility information
    """
    analysis = {
        "context": context,
        "is_legacy_format": False,
        "is_super_connector_format": False,
        "has_patient_info": False,
        "has_insurance_info": False,
        "has_deductible_info": False,
        "compatibility_issues": []
    }
    
    try:
        if not response:
            analysis["compatibility_issues"].append("Response is None or empty")
            return analysis
        
        # Check format detection
        analysis["is_legacy_format"] = is_legacy_response_format(response)
        analysis["is_super_connector_format"] = is_super_connector_response_format(response)
        
        if not analysis["is_legacy_format"] and not analysis["is_super_connector_format"]:
            analysis["compatibility_issues"].append("Unknown response format")
        
        # Check for required data structures
        if analysis["is_legacy_format"]:
            member_policies = response.get("memberPolicies", [])
            if member_policies:
                first_policy = member_policies[0]
                analysis["has_patient_info"] = "patientInfo" in first_policy
                analysis["has_insurance_info"] = "insuranceInfo" in first_policy
                analysis["has_deductible_info"] = "deductibleInfo" in first_policy
                
                if not analysis["has_patient_info"]:
                    analysis["compatibility_issues"].append("Legacy format missing patientInfo")
                if not analysis["has_insurance_info"]:
                    analysis["compatibility_issues"].append("Legacy format missing insuranceInfo")
                if not analysis["has_deductible_info"]:
                    analysis["compatibility_issues"].append("Legacy format missing deductibleInfo")
        
        elif analysis["is_super_connector_format"]:
            raw_response = response.get("rawGraphQLResponse", {})
            data = raw_response.get("data", {})
            check_eligibility = data.get("checkEligibility", {})
            eligibility_list = check_eligibility.get("eligibility", [])
            
            if eligibility_list:
                first_eligibility = eligibility_list[0]
                eligibility_info = first_eligibility.get("eligibilityInfo", {})
                analysis["has_patient_info"] = "member" in eligibility_info
                analysis["has_insurance_info"] = "insuranceInfo" in eligibility_info
                analysis["has_deductible_info"] = "planLevels" in eligibility_info
                
                if not analysis["has_patient_info"]:
                    analysis["compatibility_issues"].append("Super Connector format missing member info")
                if not analysis["has_insurance_info"]:
                    analysis["compatibility_issues"].append("Super Connector format missing insuranceInfo")
                if not analysis["has_deductible_info"]:
                    analysis["compatibility_issues"].append("Super Connector format missing planLevels")
        
        # Log analysis results
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Response compatibility analysis for {}: {}".format(context, analysis), level="DEBUG")
        
        return analysis
        
    except Exception as e:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Error in analyze_response_compatibility: {}".format(str(e)), level="ERROR")
        analysis["compatibility_issues"].append("Analysis error: {}".format(str(e)))
        return analysis

# =============================================================================
# API RESPONSE PARSING UTILITIES
# =============================================================================

def extract_legacy_patient_info(policy):
    """Extract patient information from legacy API response format"""
    patient_info = policy.get("patientInfo", [{}])[0]
    return {
        'lastName': patient_info.get("lastName", ""),
        'firstName': patient_info.get("firstName", ""),
        'middleName': patient_info.get("middleName", "")
    }

def extract_super_connector_patient_info(eligibility_data):
    """Extract patient information from Super Connector API response format"""
    if not eligibility_data:
        return {'lastName': '', 'firstName': '', 'middleName': ''}
    
    # ENHANCED DEBUGGING: Log response structure before parsing
    log_api_response_structure(eligibility_data, "Super Connector Patient Info", "DEBUG")
    
    # Analyze compatibility with our parser
    compatibility = analyze_response_compatibility(eligibility_data, "Super Connector Patient Info")
    if compatibility["compatibility_issues"]:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Compatibility issues detected: {}".format(compatibility["compatibility_issues"]), level="WARNING")
    
    # Handle multiple eligibility records - use the first one with valid data
    if "rawGraphQLResponse" in eligibility_data:
        raw_response = eligibility_data.get('rawGraphQLResponse', {})
        data = raw_response.get('data', {})
        check_eligibility = data.get('checkEligibility', {})
        eligibility_list = check_eligibility.get('eligibility', [])
        
        # Try to get from the first eligibility record
        if eligibility_list:
            first_eligibility = eligibility_list[0]
            member_info = first_eligibility.get('eligibilityInfo', {}).get('member', {})
            if member_info:
                result = {
                    'lastName': member_info.get("lastName", ""),
                    'firstName': member_info.get("firstName", ""),
                    'middleName': member_info.get("middleName", "")
                }
                if MediLink_ConfigLoader:
                    MediLink_ConfigLoader.log("Successfully extracted patient info from member: {}".format(result), level="DEBUG")
                return result
        
        # Check for data in error extensions (some APIs return data here despite errors)
        errors = raw_response.get('errors', [])
        for error in errors:
            extensions = error.get('extensions', {})
            if extensions and 'details' in extensions:
                details = extensions.get('details', [])
                if details:
                    # Use the first detail record that has patient info
                    for detail in details:
                        if detail.get('lastName') or detail.get('firstName'):
                            result = {
                                'lastName': detail.get("lastName", ""),
                                'firstName': detail.get("firstName", ""),
                                'middleName': detail.get("middleName", "")
                            }
                            if MediLink_ConfigLoader:
                                MediLink_ConfigLoader.log("Extracted patient info from error extensions: {}".format(result), level="DEBUG")
                            return result
    
    # Fallback to top-level fields
    result = {
        'lastName': eligibility_data.get("lastName", ""),
        'firstName': eligibility_data.get("firstName", ""),
        'middleName': eligibility_data.get("middleName", "")
    }
    if MediLink_ConfigLoader:
        MediLink_ConfigLoader.log("Using fallback top-level fields for patient info: {}".format(result), level="DEBUG")
    return result

def extract_legacy_remaining_amount(policy):
    """Extract remaining amount from legacy API response format"""
    deductible_info = policy.get("deductibleInfo", {})
    if 'individual' in deductible_info:
        remaining = deductible_info['individual']['inNetwork'].get("remainingAmount", "")
        return remaining if remaining else "Not Found"
    elif 'family' in deductible_info:
        remaining = deductible_info['family']['inNetwork'].get("remainingAmount", "")
        return remaining if remaining else "Not Found"
    else:
        return "Not Found"

def extract_super_connector_remaining_amount(eligibility_data):
    """Extract remaining amount from Super Connector API response format"""
    if not eligibility_data:
        return "Not Found"
    
    # First, check top-level metYearToDateAmount which might indicate deductible met
    met_amount = eligibility_data.get('metYearToDateAmount')
    if met_amount is not None:
        return str(met_amount)
    
    # Collect all deductible amounts to find the most relevant one
    all_deductible_amounts = []
    
    # Look for deductible information in planLevels (based on validation report)
    plan_levels = eligibility_data.get('planLevels', [])
    for plan_level in plan_levels:
        if plan_level.get('level') == 'deductibleInfo':
            # Collect individual deductible amounts
            individual_levels = plan_level.get('individual', [])
            if individual_levels:
                for individual in individual_levels:
                    remaining = individual.get('remainingAmount')
                    if remaining is not None:
                        try:
                            amount = float(remaining)
                            all_deductible_amounts.append(('individual', amount))
                        except (ValueError, TypeError):
                            pass
            
            # Collect family deductible amounts
            family_levels = plan_level.get('family', [])
            if family_levels:
                for family in family_levels:
                    remaining = family.get('remainingAmount')
                    if remaining is not None:
                        try:
                            amount = float(remaining)
                            all_deductible_amounts.append(('family', amount))
                        except (ValueError, TypeError):
                            pass
    
    # Navigate to the rawGraphQLResponse structure as fallback
    raw_response = eligibility_data.get('rawGraphQLResponse', {})
    if raw_response:
        data = raw_response.get('data', {})
        check_eligibility = data.get('checkEligibility', {})
        eligibility_list = check_eligibility.get('eligibility', [])
        
        # Try all eligibility records for deductible information
        for eligibility in eligibility_list:
            plan_levels = eligibility.get('eligibilityInfo', {}).get('planLevels', [])
            for plan_level in plan_levels:
                if plan_level.get('level') == 'deductibleInfo':
                    # Collect individual deductible amounts
                    individual_levels = plan_level.get('individual', [])
                    if individual_levels:
                        for individual in individual_levels:
                            remaining = individual.get('remainingAmount')
                            if remaining is not None:
                                try:
                                    amount = float(remaining)
                                    all_deductible_amounts.append(('individual', amount))
                                except (ValueError, TypeError):
                                    pass
                    
                    # Collect family deductible amounts
                    family_levels = plan_level.get('family', [])
                    if family_levels:
                        for family in family_levels:
                            remaining = family.get('remainingAmount')
                            if remaining is not None:
                                try:
                                    amount = float(remaining)
                                    all_deductible_amounts.append(('family', amount))
                                except (ValueError, TypeError):
                                    pass
    
    # Select the most relevant deductible amount
    # TODO: Augment this selection logic to be more intelligent when multiple remaining_amount options are available.
    # Current strategy (prefer individual over family, prefer non-zero, use max()) can yield erroneously large values
    # for certain patients with multiple policies/eligibility records. Future work needed to research and repair:
    # - Consider service_date matching to select the correct policy period
    # - Consider plan dates (planStartDate/planEndDate) to match active policies
    # - Consider relationship codes or member roles to select appropriate individual vs family amounts
    # - Investigate cases where max() returns unexpectedly large values and implement better filtering/validation
    # NOTE: Diagnostic columns showing all deductible amounts are now available in the table display.
    # User feedback on which column contains the correct value will guide future selection logic improvements.
    if all_deductible_amounts:
        # Strategy: Prefer individual over family, and prefer non-zero amounts
        # First, try to find non-zero individual amounts
        non_zero_individual = [amt for type_, amt in all_deductible_amounts if type_ == 'individual' and amt > 0]
        if non_zero_individual:
            return str(max(non_zero_individual))  # Return highest non-zero individual amount
        
        # If no non-zero individual, try non-zero family amounts
        non_zero_family = [amt for type_, amt in all_deductible_amounts if type_ == 'family' and amt > 0]
        if non_zero_family:
            return str(max(non_zero_family))  # Return highest non-zero family amount
        
        # If all amounts are zero, return the first individual amount (or family if no individual)
        individual_amounts = [amt for type_, amt in all_deductible_amounts if type_ == 'individual']
        if individual_amounts:
            return str(individual_amounts[0])
        
        # Fallback to first family amount
        family_amounts = [amt for type_, amt in all_deductible_amounts if type_ == 'family']
        if family_amounts:
            return str(family_amounts[0])
    
    return "Not Found"

def extract_all_deductible_amounts(eligibility_data):
    """
    TEMPORARY DIAGNOSTIC FUNCTION: Extract ALL deductible amounts from eligibility response for diagnostic display.
    
    This function extracts every deductible-related value from the GraphQL response,
    including all individual/family combinations, remaining/plan amounts, and all
    networkStatus variations. The extracted data enables users to identify which
    value should be used as the default selection.
    
    DEPRECATION PLAN:
    This is a temporary diagnostic function to help identify the correct selection logic.
    Once users provide feedback on which column contains the correct value, the
    selection logic in extract_super_connector_remaining_amount() should be updated
    accordingly. After the correct selection logic is implemented:
    1. This function should be DEPRECATED and removed
    2. The 'all_deductible_amounts' field should no longer be extracted or stored
    3. Diagnostic columns should no longer be displayed in the table
    4. The system will return to using only the single correctly-selected remaining_amount value
    
    Args:
        eligibility_data: Eligibility response data (Super Connector format)
    
    Returns:
        dict: Structured deductible information with keys:
            - 'individual_remaining': List of dicts with 'amount', 'networkStatus', 'frequency'
            - 'family_remaining': List of dicts with 'amount', 'networkStatus', 'frequency'
            - 'individual_plan': List of dicts with 'amount', 'networkStatus', 'frequency'
            - 'family_plan': List of dicts with 'amount', 'networkStatus', 'frequency'
            - 'current_selected': str - The value currently selected by extract_super_connector_remaining_amount()
    """
    if not eligibility_data:
        return {
            'individual_remaining': [],
            'family_remaining': [],
            'individual_plan': [],
            'family_plan': [],
            'current_selected': 'Not Found'
        }
    
    # Get the currently selected value for comparison
    current_selected = extract_super_connector_remaining_amount(eligibility_data)
    
    individual_remaining = []
    family_remaining = []
    individual_plan = []
    family_plan = []
    
    # Helper function to extract deductible info from a plan_level entry
    def extract_from_plan_level(plan_level):
        """Extract deductible info from a single planLevel entry"""
        if plan_level.get('level') == 'deductibleInfo' or (isinstance(plan_level.get('level'), str) and plan_level.get('level', '').startswith('deductibleInfo')):
            # Extract individual amounts
            individual_levels = plan_level.get('individual', [])
            if individual_levels:
                for individual in individual_levels:
                    # Extract remaining amount
                    remaining = individual.get('remainingAmount')
                    if remaining is not None:
                        individual_remaining.append({
                            'amount': str(remaining),
                            'networkStatus': str(individual.get('networkStatus', '')),
                            'frequency': str(individual.get('planAmountFrequency', ''))
                        })
                    
                    # Extract plan amount
                    plan_amt = individual.get('planAmount')
                    if plan_amt is not None:
                        individual_plan.append({
                            'amount': str(plan_amt),
                            'networkStatus': str(individual.get('networkStatus', '')),
                            'frequency': str(individual.get('planAmountFrequency', ''))
                        })
            
            # Extract family amounts
            family_levels = plan_level.get('family', [])
            if family_levels:
                for family in family_levels:
                    # Extract remaining amount
                    remaining = family.get('remainingAmount')
                    if remaining is not None:
                        family_remaining.append({
                            'amount': str(remaining),
                            'networkStatus': str(family.get('networkStatus', '')),
                            'frequency': str(family.get('planAmountFrequency', ''))
                        })
                    
                    # Extract plan amount
                    plan_amt = family.get('planAmount')
                    if plan_amt is not None:
                        family_plan.append({
                            'amount': str(plan_amt),
                            'networkStatus': str(family.get('networkStatus', '')),
                            'frequency': str(family.get('planAmountFrequency', ''))
                        })
    
    # Look for deductible information in top-level planLevels
    plan_levels = eligibility_data.get('planLevels', [])
    for plan_level in plan_levels:
        extract_from_plan_level(plan_level)
    
    # Navigate to the rawGraphQLResponse structure as fallback
    raw_response = eligibility_data.get('rawGraphQLResponse', {})
    if raw_response:
        data = raw_response.get('data', {})
        check_eligibility = data.get('checkEligibility', {})
        eligibility_list = check_eligibility.get('eligibility', [])
        
        # Try all eligibility records for deductible information
        for eligibility in eligibility_list:
            eligibility_info = eligibility.get('eligibilityInfo', {})
            plan_levels = eligibility_info.get('planLevels', [])
            for plan_level in plan_levels:
                extract_from_plan_level(plan_level)
    
    return {
        'individual_remaining': individual_remaining,
        'family_remaining': family_remaining,
        'individual_plan': individual_plan,
        'family_plan': family_plan,
        'current_selected': current_selected
    }

def extract_legacy_insurance_info(policy):
    """Extract insurance information from legacy API response format"""
    insurance_info = policy.get("insuranceInfo", {})
    return {
        'insuranceType': insurance_info.get("insuranceType", ""),
        'insuranceTypeCode': insurance_info.get("insuranceTypeCode", ""),
        'memberId': insurance_info.get("memberId", ""),
        'payerId': insurance_info.get("payerId", "")
    }

def extract_super_connector_insurance_info(eligibility_data):
    """Extract insurance information from Super Connector API response format"""
    if not eligibility_data:
        return {'insuranceType': '', 'insuranceTypeCode': '', 'memberId': '', 'payerId': ''}
    
    # Handle multiple eligibility records - use the first one with valid data
    if "rawGraphQLResponse" in eligibility_data:
        raw_response = eligibility_data.get('rawGraphQLResponse', {})
        data = raw_response.get('data', {})
        check_eligibility = data.get('checkEligibility', {})
        eligibility_list = check_eligibility.get('eligibility', [])
        
        # Try to get from the first eligibility record
        if eligibility_list:
            first_eligibility = eligibility_list[0]
            insurance_info = first_eligibility.get('eligibilityInfo', {}).get('insuranceInfo', {})
            if insurance_info:
                # Extract and validate insurance type code
                raw_code = insurance_info.get("insuranceTypeCode") or insurance_info.get("productServiceCode", "")
                validated_code = raw_code if (raw_code and is_valid_insurance_code(raw_code)) else ''
                
                # Log rejection if invalid
                if raw_code and not validated_code and MediLink_ConfigLoader:
                    MediLink_ConfigLoader.log(
                        "extract_super_connector_insurance_info: REJECTED invalid code '{}' from rawGraphQLResponse".format(
                            raw_code[:50]), level="WARNING")
                
                return {
                    'insuranceType': insurance_info.get("planTypeDescription", ""),
                    'insuranceTypeCode': validated_code,
                    'memberId': insurance_info.get("memberId", ""),
                    'payerId': insurance_info.get("payerId", "")
                }
        
        # Check for data in error extensions (some APIs return data here despite errors)
        errors = raw_response.get('errors', [])
        for error in errors:
            extensions = error.get('extensions', {})
            if extensions and 'details' in extensions:
                details = extensions.get('details', [])
                if details:
                    # Use the first detail record that has insurance info
                    for detail in details:
                        if detail.get('memberId') or detail.get('payerId'):
                            # Try to determine insurance type from available data
                            insurance_type = detail.get('planType', '')
                            if not insurance_type:
                                insurance_type = detail.get('productType', '')
                            
                            # Extract and validate insurance type code
                            raw_code = detail.get("insuranceTypeCode") or detail.get("productServiceCode", "")
                            validated_code = raw_code if (raw_code and is_valid_insurance_code(raw_code)) else ''
                            
                            # Log rejection if invalid
                            if raw_code and not validated_code and MediLink_ConfigLoader:
                                MediLink_ConfigLoader.log(
                                    "extract_super_connector_insurance_info: REJECTED invalid code '{}' from error extensions".format(
                                        raw_code[:50]), level="WARNING")
                            
                            return {
                                'insuranceType': insurance_type,
                                'insuranceTypeCode': validated_code,
                                'memberId': detail.get("memberId", ""),
                                'payerId': detail.get("payerId", "")
                            }
    
    # Fallback to top-level fields
    insurance_type = eligibility_data.get("planTypeDescription", "")
    if not insurance_type:
        insurance_type = eligibility_data.get("productType", "")
    
    # Clean up the insurance type if it's too long (like the LPPO description)
    if insurance_type and len(insurance_type) > 50:
        # Extract just the plan type part
        if "PPO" in insurance_type:
            insurance_type = "Preferred Provider Organization (PPO)"
        elif "HMO" in insurance_type:
            insurance_type = "Health Maintenance Organization (HMO)"
        elif "EPO" in insurance_type:
            insurance_type = "Exclusive Provider Organization (EPO)"
        elif "POS" in insurance_type:
            insurance_type = "Point of Service (POS)"
    
    # Get insurance type code from multiple possible locations (prefer insuranceTypeCode)
    insurance_type_code = eligibility_data.get("insuranceTypeCode", "")
    if not insurance_type_code:
        insurance_type_code = eligibility_data.get("productServiceCode", "")
    if not insurance_type_code:
        # Try to get from coverageTypes
        coverage_types = eligibility_data.get("coverageTypes", [])
        if coverage_types:
            insurance_type_code = coverage_types[0].get("typeCode", "")
    
    # Validate insurance type code before returning
    validated_code = insurance_type_code if (insurance_type_code and is_valid_insurance_code(insurance_type_code)) else ''
    
    # Log rejection if invalid
    if insurance_type_code and not validated_code and MediLink_ConfigLoader:
        MediLink_ConfigLoader.log(
            "extract_super_connector_insurance_info: REJECTED invalid code '{}' from top-level fields".format(
                insurance_type_code[:50]), level="WARNING")
    
    return {
        'insuranceType': insurance_type,
        'insuranceTypeCode': validated_code,
        'memberId': eligibility_data.get("subscriberId", ""),
        'payerId': eligibility_data.get("payerId", "")
    }


def collect_insurance_type_mapping_from_response(eligibility_data):
    """
    Extract insurance type code and all fallback fields from eligibility API response.
    Used for silent monitoring to build API_TO_SBR_MAPPING dictionary.
    
    Args:
        eligibility_data: Raw eligibility API response (from get_eligibility_super_connector or merge_responses)
        
    Returns:
        Dictionary with single entry: {api_code: [list of field values]} or empty dict if extraction fails.
        Field values include: planTypeDescription, productType, planVariation, lineOfBusiness, 
        lineOfBusinessCode, productServiceCode, insuranceTypeCode
    """
    if not eligibility_data:
        return {}
    
    try:
        api_code = None
        field_values = []
        
        # Try to extract from raw GraphQL response first
        if "rawGraphQLResponse" in eligibility_data:
            raw_response = eligibility_data.get('rawGraphQLResponse', {})
            data = raw_response.get('data', {})
            check_eligibility = data.get('checkEligibility', {})
            eligibility_list = check_eligibility.get('eligibility', [])
            
            # Try to get from the first eligibility record
            if eligibility_list:
                first_eligibility = eligibility_list[0]
                insurance_info = first_eligibility.get('eligibilityInfo', {}).get('insuranceInfo', {})
                if insurance_info:
                    # Get the primary code
                    api_code = (insurance_info.get("insuranceTypeCode") or 
                               insurance_info.get("productServiceCode", "")).strip()
                    
                    # Collect all relevant fields as a list
                    if insurance_info.get("planTypeDescription"):
                        field_values.append(insurance_info.get("planTypeDescription"))
                    if insurance_info.get("productType"):
                        field_values.append(insurance_info.get("productType"))
                    if insurance_info.get("planVariation"):
                        field_values.append(insurance_info.get("planVariation"))
                    if insurance_info.get("lineOfBusiness"):
                        field_values.append(insurance_info.get("lineOfBusiness"))
                    if insurance_info.get("lineOfBusinessCode"):
                        field_values.append(insurance_info.get("lineOfBusinessCode"))
                    if insurance_info.get("productServiceCode"):
                        field_values.append(insurance_info.get("productServiceCode"))
                    if insurance_info.get("insuranceTypeCode"):
                        field_values.append(insurance_info.get("insuranceTypeCode"))
            
            # Check for data in error extensions (some APIs return data here despite errors)
            if not api_code:
                errors = raw_response.get('errors', [])
                for error in errors:
                    extensions = error.get('extensions', {})
                    if extensions and 'details' in extensions:
                        details = extensions.get('details', [])
                        if details:
                            # Use the first detail record that has insurance info
                            for detail in details:
                                if detail.get('memberId') or detail.get('payerId'):
                                    # Get the code
                                    api_code = (detail.get("insuranceTypeCode") or 
                                               detail.get("productServiceCode", "")).strip()
                                    
                                    # Collect fields from detail
                                    if detail.get('planType'):
                                        field_values.append(detail.get('planType'))
                                    if detail.get('productType'):
                                        field_values.append(detail.get('productType'))
                                    if detail.get("insuranceTypeCode"):
                                        field_values.append(detail.get("insuranceTypeCode"))
                                    if detail.get("productServiceCode"):
                                        field_values.append(detail.get("productServiceCode"))
                                    break
                            if api_code:
                                break
        
        # Fallback to using extract_super_connector_insurance_info if raw response not available
        if not api_code:
            try:
                insurance_info = extract_super_connector_insurance_info(eligibility_data)
                api_code = insurance_info.get('insuranceTypeCode', '').strip()
                description = insurance_info.get('insuranceType', '').strip()
                if description:
                    field_values.append(description)
            except Exception:
                pass
        
        # Only return if we have a code and at least one field value
        if api_code and field_values:
            # Store as list of unique values (preserving order)
            seen = set()
            unique_values = []
            for val in field_values:
                val_str = str(val).strip() if val else ''
                if val_str and val_str not in seen:
                    seen.add(val_str)
                    unique_values.append(val_str)
            
            if unique_values:
                return {api_code: unique_values}
        
        return {}
    except Exception:
        # Return empty dict on any error - silent failure
        return {}

def extract_legacy_policy_status(policy):
    """Extract policy status from legacy API response format"""
    policy_info = policy.get("policyInfo", {})
    return policy_info.get("policyStatus", "")

def extract_super_connector_policy_status(eligibility_data):
    """Extract policy status from Super Connector API response format"""
    if not eligibility_data:
        return ""
    
    # Handle multiple eligibility records - use the first one with valid data
    if "rawGraphQLResponse" in eligibility_data:
        raw_response = eligibility_data.get('rawGraphQLResponse', {})
        data = raw_response.get('data', {})
        check_eligibility = data.get('checkEligibility', {})
        eligibility_list = check_eligibility.get('eligibility', [])
        
        # Try to get from the first eligibility record
        if eligibility_list:
            first_eligibility = eligibility_list[0]
            insurance_info = first_eligibility.get('eligibilityInfo', {}).get('insuranceInfo', {})
            if insurance_info:
                return insurance_info.get("policyStatus", "")
    
    # Fallback to top-level field
    return eligibility_data.get("policyStatus", "")

def is_legacy_response_format(data):
    """Determine if the response is in legacy format (has memberPolicies)"""
    return data is not None and "memberPolicies" in data

def is_super_connector_response_format(data):
    """Determine if the response is in Super Connector format (has rawGraphQLResponse)"""
    return data is not None and "rawGraphQLResponse" in data

# =============================================================================
# ELIGIBILITY DATA CONVERSION UTILITIES
# =============================================================================

def convert_eligibility_to_enhanced_format(data, dob, member_id, patient_id="", service_date=""):
    """Convert API eligibility response to enhanced display format"""
    if data is None:
        return None

    # Check if data is already processed (from merge_responses)
    if isinstance(data, dict) and 'patient_name' in data and 'data_source' in data:
        # Already processed data - just add missing fields if needed
        if 'patient_id' not in data:
            data['patient_id'] = patient_id
        if 'service_date_display' not in data:
            data['service_date_display'] = service_date
        if 'service_date_sort' not in data:
            data['service_date_sort'] = datetime.min
        if 'status' not in data:
            data['status'] = 'Processed'
        # TEMPORARY: Preserve all_deductible_amounts if already present (should be set by merge_responses)
        # If not present, we can't extract it here because the raw data structure is gone
        # In this case, all_deductible_amounts should already be set by merge_responses
        # TODO: DEPRECATE - Remove this field preservation once correct selection logic is implemented
        if 'all_deductible_amounts' not in data:
            data['all_deductible_amounts'] = {}
        return data

    # ENHANCED DEBUGGING: Log response structure and analyze compatibility
    log_api_response_structure(data, "Eligibility Conversion", "DEBUG")
    compatibility = analyze_response_compatibility(data, "Eligibility Conversion")
    
    if compatibility["compatibility_issues"]:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Compatibility issues in eligibility conversion: {}".format(compatibility["compatibility_issues"]), level="WARNING")

    # Determine which API response format we're dealing with
    if is_legacy_response_format(data):
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Processing Legacy API response format", level="DEBUG")
        
        # Handle legacy API response format
        for policy in data.get("memberPolicies", []):
            # Skip non-medical policies
            if policy.get("policyInfo", {}).get("coverageType", "") != "Medical":
                continue

            patient_info = extract_legacy_patient_info(policy)
            remaining_amount = extract_legacy_remaining_amount(policy)
            insurance_info = extract_legacy_insurance_info(policy)
            policy_status = extract_legacy_policy_status(policy)

            patient_name = "{} {} {}".format(
                patient_info['firstName'], 
                patient_info['middleName'], 
                patient_info['lastName']
            ).strip()

            result = {
                'patient_id': patient_id,
                'patient_name': patient_name,
                'dob': dob,
                'member_id': member_id,
                'payer_id': insurance_info['payerId'],
                'service_date_display': service_date,
                'service_date_sort': datetime.min,  # Will be enhanced later
                'status': 'Processed',
                # Prefer insurance type code over description for downstream validation/UI
                'insurance_type': insurance_info.get('insuranceTypeCode') or insurance_info.get('insuranceType', ''),
                'policy_status': policy_status,
                'remaining_amount': remaining_amount,
                'data_source': 'Legacy',
                'is_successful': bool(patient_name and remaining_amount != 'Not Found'),
                # TEMPORARY: Legacy format may have different structure, so set empty dict for diagnostic columns
                # (diagnostic columns are primarily for Super Connector/GraphQL format)
                # TODO: DEPRECATE - Remove this field once correct selection logic is implemented
                'all_deductible_amounts': {}
            }

            # Provide a diagnostic reason when the patient name couldn't be resolved
            if not patient_name:
                try:
                    if not compatibility.get("has_patient_info"):
                        result['error_reason'] = 'Legacy API response missing patientInfo'
                    else:
                        result['error_reason'] = 'Legacy patientInfo present but name fields blank'
                except Exception:
                    result['error_reason'] = 'Unable to resolve patient name from Legacy response'

            if MediLink_ConfigLoader:
                MediLink_ConfigLoader.log("Successfully converted Legacy API response: {}".format(result), level="DEBUG")
            return result

    elif is_super_connector_response_format(data):
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Processing Super Connector API response format", level="DEBUG")
        
        # Handle Super Connector API response format
        patient_info = extract_super_connector_patient_info(data)
        remaining_amount = extract_super_connector_remaining_amount(data)
        insurance_info = extract_super_connector_insurance_info(data)
        policy_status = extract_super_connector_policy_status(data)

        patient_name = "{} {} {}".format(
            patient_info['firstName'], 
            patient_info['middleName'], 
            patient_info['lastName']
        ).strip()

        # TEMPORARY: Extract all deductible amounts for diagnostic display
        # This enables users to see all possible values and identify which one should be selected
        # TODO: DEPRECATE - Once users provide feedback and correct selection logic is implemented,
        #       remove this extraction. The 'all_deductible_amounts' field should no longer be stored,
        #       and diagnostic columns should not be displayed. The system will use only the single
        #       correctly-selected remaining_amount value.
        all_deductible_amounts = extract_all_deductible_amounts(data)
        
        result = {
            'patient_id': patient_id,
            'patient_name': patient_name,
            'dob': dob,
            'member_id': member_id,
            'payer_id': insurance_info['payerId'],
            'service_date_display': service_date,
            'service_date_sort': datetime.min,  # Will be enhanced later
            'status': 'Processed',
            # Prefer insurance type CODE over description for downstream validation/UI
            # Never use description (insuranceType) - it's too long and not a code
            'insurance_type': insurance_info.get('insuranceTypeCode') or insurance_info.get('productServiceCode', ''),
            'policy_status': policy_status,
            'remaining_amount': remaining_amount,
            'data_source': 'OptumAI',
            'is_successful': bool(patient_name and remaining_amount != 'Not Found'),
            # TEMPORARY: Store all deductible amounts for diagnostic display purposes
            # This allows users to see all possible values and provide feedback on which one is correct
            # TODO: DEPRECATE - Remove this field once correct selection logic is implemented
            'all_deductible_amounts': all_deductible_amounts
        }

        # Provide a diagnostic reason when the patient name couldn't be resolved
        if not patient_name:
            try:
                if not compatibility.get("has_patient_info"):
                    result['error_reason'] = 'OptumAI response missing member info'
                else:
                    result['error_reason'] = 'OptumAI member info present but name fields blank'
            except Exception:
                result['error_reason'] = 'Unable to resolve patient name from OptumAI response'

        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Successfully converted Super Connector API response: {}".format(result), level="DEBUG")
        return result

    else:
        # Unknown response format - enhanced logging for debugging
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Unknown response format in convert_eligibility_to_enhanced_format", level="WARNING")
            MediLink_ConfigLoader.log("Response structure: {}".format(json.dumps(data, indent=2)), level="DEBUG")
            
            # Additional debugging information
            MediLink_ConfigLoader.log("Response type: {}".format(type(data)), level="DEBUG")
            if isinstance(data, dict):
                MediLink_ConfigLoader.log("Available keys: {}".format(list(data.keys())), level="DEBUG")
        return None

# =============================================================================
# PAYER ID RESOLUTION UTILITIES
# =============================================================================

def resolve_payer_ids_from_csv(csv_data, config, crosswalk, payer_ids):
    """
    Resolve payer IDs for each patient from CSV data using crosswalk mapping.
    This eliminates the need for multi-payer probing and reduces complexity from O(PxN) to O(N).
    
    Args:
        csv_data (list): CSV data containing patient information
        config (dict): Configuration object
        crosswalk (dict): Crosswalk data containing payer mappings
        payer_ids (list): List of supported payer IDs
        
    Returns:
        dict: Mapping of (dob, member_id) tuples to resolved payer_id
    """
    if MediLink_ConfigLoader:
        MediLink_ConfigLoader.log("Resolving payer IDs from CSV data using crosswalk...", level="INFO")
    
    # Initialize cache
    payer_id_cache = {}
    
    # Build payer ID to endpoint mapping from crosswalk
    payer_endpoint_map = {}
    crosswalk_payers = crosswalk.get('payer_id', {})
    for payer_id, details in crosswalk_payers.items():
        endpoint = details.get('endpoint', 'UHCAPI')  # Default to UHCAPI
        payer_endpoint_map[payer_id] = endpoint
    
    # Process each CSV row to resolve payer IDs
    for row in csv_data:
        ins1_payer_id = row.get('Ins1 Payer ID', '').strip()
        # Use same DOB field extraction as MediLink_Deductible.py for consistency
        dob = row.get('Patient DOB', row.get('DOB', ''))
        # Use same member_id field extraction as MediLink_Deductible.py for consistency  
        member_id = row.get('Primary Policy Number', row.get('Ins1 Member ID', '')).strip()
        
        # Skip rows without required data
        if not ins1_payer_id or not dob or not member_id:
            continue
            
        # Validate and format DOB - both validate_and_format_date and _fallback_validate_and_format_date
        # should produce the same YYYY-MM-DD format, but ensure we handle edge cases
        formatted_dob = validate_and_format_date(dob)
        if not formatted_dob:
            continue
            
        # Check if this payer ID is in our supported list (or accept all if payer_ids is None)
        if payer_ids is None:
            # No filter - accept all payer IDs from CSV
            payer_id_cache[(formatted_dob, member_id)] = ins1_payer_id
            if MediLink_ConfigLoader:
                MediLink_ConfigLoader.log("Resolved payer ID {} for patient {} (DOB: {}) - no filter applied".format(
                    ins1_payer_id, member_id, formatted_dob), level="DEBUG")
        elif ins1_payer_id in payer_ids:
            # Use the payer ID from CSV as authoritative source
            payer_id_cache[(formatted_dob, member_id)] = ins1_payer_id
            if MediLink_ConfigLoader:
                MediLink_ConfigLoader.log("Resolved payer ID {} for patient {} (DOB: {})".format(
                    ins1_payer_id, member_id, formatted_dob), level="DEBUG")
        else:
            # Payer ID not in supported list - log for review
            if MediLink_ConfigLoader:
                MediLink_ConfigLoader.log("Payer ID {} not in supported list for patient {} (DOB: {})".format(
                    ins1_payer_id, member_id, formatted_dob), level="INFO")
    
    if MediLink_ConfigLoader:
        MediLink_ConfigLoader.log("Payer ID resolution complete. Resolved {} patient-payer mappings.".format(
            len(payer_id_cache)), level="INFO")
    
    return payer_id_cache

def get_payer_id_for_patient(dob, member_id, payer_id_cache):
    """
    Get the appropriate payer ID for a specific patient.
    
    Args:
        dob (str): Patient date of birth in ANY format (will be normalized internally)
        member_id (str): Patient member ID
        payer_id_cache (dict): Cached payer ID mappings (keys are normalized DOB in YYYY-MM-DD format)
        
    Returns:
        str: Payer ID for the patient, or None if not found
    """
    if not payer_id_cache or not isinstance(payer_id_cache, dict):
        return None
    
    # FIX #9: Normalize DOB to match cache key format (YYYY-MM-DD)
    normalized_dob = validate_and_format_date(dob)
    if not normalized_dob:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log(
                "get_payer_id_for_patient: Could not normalize DOB '{}' for member_id '{}'".format(
                    dob[:20] if dob else None, member_id), level="WARNING")
        return None
    
    # Create lookup key with normalized DOB
    lookup_key = (normalized_dob, member_id)
    result = payer_id_cache.get(lookup_key)
    
    # Log cache hit/miss for monitoring
    if result:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log(
                "get_payer_id_for_patient: Cache HIT for member_id '{}' (normalized_dob='{}'): payer_id='{}'".format(
                    member_id, normalized_dob, result), level="DEBUG")
    else:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log(
                "get_payer_id_for_patient: Cache MISS for member_id '{}' (normalized_dob='{}')".format(
                    member_id, normalized_dob), level="DEBUG")
    
    return result


def is_valid_insurance_code(code):
    """
    Validate if insurance type code is a valid short code (1-3 alphanumeric characters).
    Returns False for descriptions, "Not Available", empty strings, or invalid formats.
    
    This is a shared utility function used across multiple modules to ensure consistent
    validation of insurance type codes before caching or using them.
    
    Args:
        code: Insurance type code to validate (string, int, or None)
        
    Returns:
        bool: True if code is valid (1-3 alphanumeric), False otherwise
    """
    if not code:
        return False
    try:
        code_str = str(code).strip()
        if not code_str:
            return False
        # Reject common invalid values
        lowered = code_str.lower()
        if lowered in ('not available', 'not found', 'na', 'n/a', 'unknown', ''):
            return False
        # Valid codes are 1-3 alphanumeric characters
        # Reject anything longer (likely a description)
        if len(code_str) > 3:
            return False
        # Must be alphanumeric
        if not code_str.isalnum():
            return False
        return True
    except Exception:
        return False

# Import GraphQL utility for accessing response structure
try:
    from MediCafe.graphql_utils import get_eligibility_list_from_response
except ImportError:
    # Fallback if import fails
    def get_eligibility_list_from_response(optumai_response):
        if not optumai_response or "rawGraphQLResponse" not in optumai_response:
            return []
        try:
            raw_response = optumai_response.get('rawGraphQLResponse', {})
            if not raw_response:
                return []
            data = raw_response.get('data', {})
            if not data:
                return []
            check_eligibility = data.get('checkEligibility')
            if not check_eligibility:
                return []
            eligibility_list = check_eligibility.get('eligibility', [])
            # Filter out None values to prevent downstream errors
            return [e for e in eligibility_list if e is not None]
        except Exception:
            return []

def _matches_selected_plan(eligibility, selected_detail):
    """
    Check if an eligibility record matches the selected plan detail.
    Matches by memberId and dateOfBirth if available in selected_detail.
    Returns True if matches or if no match criteria available.
    """
    if not eligibility or not selected_detail:
        return False  # Can't match if either is None
    
    eligibility_info = eligibility.get('eligibilityInfo') if eligibility else None
    if not eligibility_info:
        return False
    
    member_info = eligibility_info.get('member', {})
    
    # If we have memberId in selected (and it's not empty), it must match
    selected_member_id = selected_detail.get('memberId')
    if selected_member_id and str(selected_member_id).strip():
        if member_info.get('memberId') != selected_member_id:
            return False
    
    # If we have dateOfBirth in selected (and it's not empty), it must match
    selected_dob = selected_detail.get('dateOfBirth')
    if selected_dob and str(selected_dob).strip():
        if member_info.get('dateOfBirth') != selected_dob:
            return False
    
    return True

def _build_patient_name(first_name, middle_name, last_name):
    """Build patient name from components, handling missing parts gracefully."""
    if not (first_name or last_name):
        return ''
    name_parts = []
    if first_name:
        name_parts.append(first_name)
    if middle_name:
        name_parts.append(middle_name)
    if last_name:
        name_parts.append(last_name)
    return " ".join(name_parts)

def merge_responses(optumai_data, legacy_data, dob, member_id, service_date=None):
    """
    Intelligently merge OptumAI and Legacy API responses.
    Prioritizes OptumAI data but backfills missing fields from Legacy API.
    Adds [*] flag to indicate when data comes from Legacy API.
    
    Args:
        optumai_data: OptumAI eligibility response
        legacy_data: Legacy API eligibility response
        dob: Date of birth
        member_id: Member ID
        service_date: Service date in YYYY-MM-DD format (optional, used to match correct plan when multiple plans found)
    """
    merged = {}
    
    # Handle None inputs gracefully
    if optumai_data is None and legacy_data is None:
        return {
            'patient_name': 'Unknown Patient',
            'dob': dob,
            'member_id': member_id,
            'insurance_type': 'Not Available',
            'policy_status': 'Not Available',
            'remaining_amount': 'Not Found',
            'data_source': 'None',
            'is_successful': False,
            'error_reason': 'No eligibility responses returned from OptumAI or Legacy APIs'
        }
    
    # Helper to check if data is valid (not None, has required fields)
    def is_valid_data(data):
        if not data:
            return False
        # Basic check for key structures
        if "rawGraphQLResponse" in data:
            raw = data.get('rawGraphQLResponse', {})
            errors = raw.get('errors', [])
            if errors and all(e.get('code') != 'SUCCESS' for e in errors):
                return False  # All errors, no data
            return bool(raw.get('data', {}).get('checkEligibility', {}).get('eligibility'))
        elif "memberPolicies" in data:
            return bool(data.get("memberPolicies"))
        return False
    
    # Handle PARTIAL_DATA_RECEIVED and INFORMATIONAL errors - these still contain usable data
    def has_partial_data(data):
        if not data or not isinstance(data, dict) or "rawGraphQLResponse" not in data:
            return False
        raw = data.get('rawGraphQLResponse', {})
        if not isinstance(raw, dict):
            return False
        errors = raw.get('errors', [])
        if not isinstance(errors, list):
            return False
        for error in errors:
            if not isinstance(error, dict):
                continue
            if error.get('code') in ['PARTIAL_DATA_RECEIVED', 'INFORMATIONAL']:
                extensions = error.get('extensions', {})
                if isinstance(extensions, dict) and 'details' in extensions:
                    return bool(extensions.get('details'))
        return False
    
    # Check for error responses (statuscode 500, 404, etc.) before processing
    if optumai_data and isinstance(optumai_data, dict):
        statuscode = optumai_data.get('statuscode', '')
        if statuscode and str(statuscode) not in ('200', '201'):
            # Error response - check if it has partial data in extensions
            if not has_partial_data(optumai_data):
                # No partial data, return error result
                return {
                    'patient_name': 'Unknown Patient',
                    'dob': dob,
                    'member_id': member_id,
                    'insurance_type': 'Not Available',
                    'policy_status': 'Not Available',
                    'remaining_amount': 'Not Found',
                    'payer_id': optumai_data.get('payer_id', ''),
                    'data_source': 'Error',
                    'is_successful': False,
                    'error_reason': optumai_data.get('message', 'API returned error response')
                }
    
    # ALWAYS prioritize OptumAI as primary source for real patient data
    # Legacy API is sandbox data and should only be used for backfilling missing fields
    primary = optumai_data
    secondary = legacy_data
    
    # If primary is OptumAI with errors but extensions, extract from there
    if primary == optumai_data and optumai_data and isinstance(optumai_data, dict) and has_partial_data(optumai_data):
        raw = optumai_data.get('rawGraphQLResponse', {})
        if not isinstance(raw, dict):
            raw = {}
        errors = raw.get('errors', [])
        if not isinstance(errors, list):
            errors = []
        for error in errors:
            if not isinstance(error, dict):
                continue
            if error.get('code') in ['INFORMATIONAL', 'PARTIAL_DATA_RECEIVED']:
                extensions = error.get('extensions', {})
                details = extensions.get('details', [])
                if details:
                    # Select plan based on service_date if provided, otherwise use most recent plan
                    try:
                        selected = None
                        if service_date:
                            # Parse service_date to datetime for comparison
                            # service_date should be a string in YYYY-MM-DD format
                            try:
                                if not isinstance(service_date, str):
                                    service_date = str(service_date)
                                service_date_dt = datetime.strptime(service_date, '%Y-%m-%d')
                                # Find plan where service_date falls within plan date range
                                for detail in details:
                                    plan_start = detail.get('planStartDate', '')
                                    plan_end = detail.get('planEndDate', '')
                                    service_start = detail.get('serviceStartDate', '')
                                    service_end = detail.get('serviceEndDate', '')
                                    
                                    # Check if service_date is within plan date range
                                    # Prefer planStartDate/planEndDate, fallback to serviceStartDate/serviceEndDate
                                    start_date = plan_start or service_start
                                    end_date = plan_end or service_end
                                    
                                    if start_date and end_date:
                                        try:
                                            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                                            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                                            if start_dt <= service_date_dt <= end_dt:
                                                selected = detail
                                                break
                                        except ValueError:
                                            continue
                                
                                # If no match found by date range, fall back to most recent plan
                                if not selected:
                                    sorted_details = sorted(details, key=lambda d: datetime.strptime(d.get('planStartDate', '1900-01-01'), '%Y-%m-%d'), reverse=True)
                                    selected = sorted_details[0] if sorted_details else None
                            except (ValueError, TypeError):
                                # If service_date parsing fails, fall back to most recent plan
                                sorted_details = sorted(details, key=lambda d: datetime.strptime(d.get('planStartDate', '1900-01-01'), '%Y-%m-%d'), reverse=True)
                                selected = sorted_details[0] if sorted_details else None
                        else:
                            # No service_date provided, select most recent plan
                            sorted_details = sorted(details, key=lambda d: datetime.strptime(d.get('planStartDate', '1900-01-01'), '%Y-%m-%d'), reverse=True)
                            selected = sorted_details[0] if sorted_details else None
                        
                        if not selected:
                            continue
                        
                        # Extract patient name with middleName, validate names exist
                        first_name = selected.get('firstName', '').strip()
                        middle_name = selected.get('middleName', '').strip()
                        last_name = selected.get('lastName', '').strip()
                        merged['patient_name'] = _build_patient_name(first_name, middle_name, last_name)
                        
                        # Cache eligibility list to avoid multiple extractions
                        eligibility_list = get_eligibility_list_from_response(optumai_data) if optumai_data else []
                        
                        # If name not in extensions, try to extract from main response structure
                        if not merged['patient_name']:
                            for eligibility in eligibility_list:
                                if eligibility and _matches_selected_plan(eligibility, selected):
                                    eligibility_info = eligibility.get('eligibilityInfo') if eligibility else None
                                    if eligibility_info:
                                        member_info = eligibility_info.get('member', {})
                                        resp_first = member_info.get('firstName', '').strip() if member_info else ''
                                        resp_middle = member_info.get('middleName', '').strip() if member_info else ''
                                        resp_last = member_info.get('lastName', '').strip() if member_info else ''
                                        merged['patient_name'] = _build_patient_name(resp_first, resp_middle, resp_last)
                                        if merged['patient_name']:
                                            break
                        
                        merged['dob'] = selected.get('dateOfBirth', dob)
                        merged['member_id'] = selected.get('memberId', member_id)
                        
                        # Extract plan dates from selected detail for cache storage
                        # Prefer planStartDate/planEndDate, fallback to serviceStartDate/serviceEndDate
                        # Normalize empty strings to None for consistency
                        plan_start = selected.get('planStartDate', '') or selected.get('serviceStartDate', '')
                        plan_end = selected.get('planEndDate', '') or selected.get('serviceEndDate', '')
                        
                        # If not in extension details, try to extract from main response structure
                        # (similar to how insurance_type_code is extracted)
                        if not plan_start or not plan_end:
                            for eligibility in eligibility_list:
                                if eligibility and _matches_selected_plan(eligibility, selected):
                                    eligibility_info = eligibility.get('eligibilityInfo') if eligibility else None
                                    if eligibility_info:
                                        insurance_info = eligibility_info.get('insuranceInfo', {})
                                        # Extract plan dates from main response if not in extension details
                                        if not plan_start:
                                            plan_start = insurance_info.get('planStartDate', '') or insurance_info.get('serviceStartDate', '')
                                        if not plan_end:
                                            plan_end = insurance_info.get('planEndDate', '') or insurance_info.get('serviceEndDate', '')
                                        if plan_start and plan_end:
                                            break
                        
                        merged['plan_start_date'] = plan_start.strip() if plan_start else None
                        merged['plan_end_date'] = plan_end.strip() if plan_end else None
                        
                        # Prefer insurance type CODE (not description) from extensions or main response
                        # Extension details may not have insuranceTypeCode - try to get from main response
                        insurance_type_code = (
                            selected.get('insuranceTypeCode') or
                            selected.get('productServiceCode') or
                            ''
                        )
                        
                        # If not in extension details, try to extract from main response structure
                        if not insurance_type_code:
                            for eligibility in eligibility_list:
                                if eligibility and _matches_selected_plan(eligibility, selected):
                                    eligibility_info = eligibility.get('eligibilityInfo') if eligibility else None
                                    if eligibility_info:
                                        insurance_info = eligibility_info.get('insuranceInfo', {})
                                        insurance_type_code = (
                                            insurance_info.get('insuranceTypeCode') or
                                            insurance_info.get('productServiceCode') or
                                            ''
                                        )
                                        if insurance_type_code:
                                            break
                        
                        # Never use description (insuranceType) - it's too long and not a code
                        # Leave empty if no code found - CSV backfill or other sources will handle it
                        merged['insurance_type'] = insurance_type_code
                        
                        merged['policy_status'] = selected.get('policyStatus', 'Active')
                        merged['payer_id'] = selected.get('payerId', '')
                        
                        # Extract deductible from main response structure, not extension details
                        # Extension details don't contain planLevels - need to extract from rawGraphQLResponse
                        deductible_found = False
                        for eligibility in eligibility_list:
                            if eligibility and _matches_selected_plan(eligibility, selected):
                                eligibility_info = eligibility.get('eligibilityInfo') if eligibility else None
                                if eligibility_info:
                                    plan_levels = eligibility_info.get('planLevels', [])
                                    for plan_level in plan_levels:
                                        if plan_level and plan_level.get('level') == 'deductibleInfo':
                                            # Try individual deductible first
                                            individual = plan_level.get('individual', [])
                                            if individual and len(individual) > 0 and individual[0]:
                                                remaining = individual[0].get('remainingAmount')
                                                if remaining is not None:
                                                    merged['remaining_amount'] = str(remaining)
                                                    deductible_found = True
                                                    break  # Break from plan_level loop
                                            # Try family deductible as fallback (only if individual not found)
                                            if not deductible_found:
                                                family = plan_level.get('family', [])
                                                if family and len(family) > 0 and family[0]:
                                                    remaining = family[0].get('remainingAmount')
                                                    if remaining is not None:
                                                        merged['remaining_amount'] = str(remaining)
                                                        deductible_found = True
                                                        break  # Break from plan_level loop
                                if deductible_found:
                                    break  # Break from eligibility loop
                        
                        if not deductible_found:
                            merged['remaining_amount'] = 'Not Found'
                        
                        # Extract all deductible amounts for diagnostic display
                        # This enables users to see all possible values and identify which one should be selected
                        merged['all_deductible_amounts'] = extract_all_deductible_amounts(optumai_data)
                        
                        merged['data_source'] = 'OptumAI-Extensions'
                        break  # Use first error with valid extensions
                    except Exception as e:
                        # If extraction fails, continue to normal processing
                        pass
    
    # Extract from OptumAI (primary) first - this contains real patient data
    if is_super_connector_response_format(primary) and primary:
        # Extract real patient data from OptumAI
        merged['patient_name'] = "{} {} {}".format(
            primary.get('firstName', ""),
            primary.get('middleName', ""), 
            primary.get('lastName', "")
        ).strip()
        merged['payer_id'] = primary.get('payerId', '')
        merged['remaining_amount'] = extract_super_connector_remaining_amount(primary)
        merged['policy_status'] = primary.get('policyStatus', '')
        
        # Prefer insurance type code directly from OptumAI response
        merged['insurance_type'] = primary.get('insuranceTypeCode') or primary.get('productServiceCode', '')
        
        # Extract plan dates from OptumAI response
        # Prefer planStartDate/planEndDate, fallback to serviceStartDate/serviceEndDate or eligibilityStartDate/eligibilityEndDate
        plan_start = primary.get('planStartDate', '') or primary.get('serviceStartDate', '') or primary.get('eligibilityStartDate', '')
        plan_end = primary.get('planEndDate', '') or primary.get('serviceEndDate', '') or primary.get('eligibilityEndDate', '')
        merged['plan_start_date'] = plan_start.strip() if plan_start else None
        merged['plan_end_date'] = plan_end.strip() if plan_end else None
        
        # TEMPORARY: Extract all deductible amounts for diagnostic display
        # This enables users to see all possible values and identify which one should be selected
        # TODO: DEPRECATE - Once users provide feedback and correct selection logic is implemented,
        #       remove this extraction. The 'all_deductible_amounts' field should no longer be stored,
        #       and diagnostic columns should not be displayed. The system will use only the single
        #       correctly-selected remaining_amount value.
        merged['all_deductible_amounts'] = extract_all_deductible_amounts(primary)
        
        merged['data_source'] = 'OptumAI'
        
    elif is_legacy_response_format(primary) and primary:
        # Only use Legacy as primary if OptumAI is completely unavailable
        policy = primary.get("memberPolicies", [{}])[0]
        patient_info = policy.get("patientInfo", [{}])[0]
        merged['patient_name'] = "{} {} {}".format(
            patient_info.get("firstName", ""),
            patient_info.get("middleName", ""),
            patient_info.get("lastName", "")
        ).strip()
        merged['insurance_type'] = policy.get("insuranceInfo", {}).get("insuranceType", "")
        merged['policy_status'] = policy.get("policyInfo", {}).get("policyStatus", "")
        merged['remaining_amount'] = extract_legacy_remaining_amount(policy)
        merged['payer_id'] = policy.get("insuranceInfo", {}).get("payerId", "")
        # Legacy format may have different structure, so set empty dict for diagnostic columns
        # (diagnostic columns are primarily for Super Connector/GraphQL format)
        merged['all_deductible_amounts'] = {}
        merged['data_source'] = 'Legacy'
    
    # Set fallback data if still empty
    if not merged:
        merged = {
            'patient_name': 'Unknown Patient',
            'insurance_type': 'Not Available',
            'policy_status': 'Not Available', 
            'remaining_amount': 'Not Found',
            'payer_id': '',
            'data_source': 'None',
            'error_reason': 'Unable to extract patient name from available eligibility responses'
        }
    
    # Intelligently backfill missing fields from Legacy API (secondary)
    # This is where we enrich OptumAI data with missing fields from Legacy
    if secondary and is_valid_data(secondary) and is_legacy_response_format(secondary):
        legacy_policy = secondary.get("memberPolicies", [{}])[0]
        legacy_insurance_info = legacy_policy.get("insuranceInfo", {})
        
        # Track which fields are backfilled from Legacy API
        backfilled_fields = []
        
        # Backfill insurance_type from Legacy API (OptumAI doesn't have this yet)
        if not merged.get('insurance_type') or merged['insurance_type'].strip() == '':
            legacy_insurance_type = legacy_insurance_info.get("insuranceType", "")
            if legacy_insurance_type:
                merged['insurance_type'] = legacy_insurance_type + " [*]"
                backfilled_fields.append('insurance_type')
        
        # Backfill policy_status if missing
        if not merged.get('policy_status') or merged['policy_status'].strip() == '':
            legacy_policy_status = legacy_policy.get("policyInfo", {}).get("policyStatus", "")
            if legacy_policy_status:
                merged['policy_status'] = legacy_policy_status + " [*]"
                backfilled_fields.append('policy_status')
        
        # Backfill remaining_amount if missing or "Not Found"
        if not merged.get('remaining_amount') or merged['remaining_amount'] == 'Not Found':
            legacy_remaining = extract_legacy_remaining_amount(legacy_policy)
            if legacy_remaining and legacy_remaining != 'Not Found':
                merged['remaining_amount'] = legacy_remaining + " [*]"
                backfilled_fields.append('remaining_amount')
        
        # Backfill payer_id if missing (should be preserved from CSV anyway)
        if not merged.get('payer_id') or merged['payer_id'].strip() == '':
            legacy_payer_id = legacy_insurance_info.get("payerId", "")
            if legacy_payer_id:
                merged['payer_id'] = legacy_payer_id + " [*]"
                backfilled_fields.append('payer_id')
        
        # Update data source to indicate backfilling occurred
        if backfilled_fields:
            if merged.get('data_source') == 'OptumAI':
                merged['data_source'] = 'OptumAI+Legacy'
            else:
                merged['data_source'] = 'Legacy'
            
            if MediLink_ConfigLoader:
                MediLink_ConfigLoader.log("Backfilled fields from Legacy API: {}".format(backfilled_fields), level="DEBUG")
    
    # For multi-plan, select most recent
    if 'multiple_plans' in merged:  # Flag if multi
        plans = merged['multiple_plans']
        if plans:
            # Sort by planStartDate descending
            sorted_plans = sorted(plans, key=lambda p: datetime.strptime(p.get('planStartDate', '1900-01-01'), '%Y-%m-%d'), reverse=True)
            selected = sorted_plans[0]
            # Update merged with selected plan data
    
    # Search for deductible in primary/secondary (only if not already set by backfill)
    if 'remaining_amount' not in merged or merged['remaining_amount'] == 'Not Found':
        if primary == optumai_data:
            merged['remaining_amount'] = extract_super_connector_remaining_amount(primary)
        else:
            merged['remaining_amount'] = extract_legacy_remaining_amount(primary)
    
    # Add required fields if missing
    if 'dob' not in merged:
        merged['dob'] = dob
    if 'member_id' not in merged:
        merged['member_id'] = member_id
    if 'patient_id' not in merged:
        merged['patient_id'] = ''
    if 'service_date_display' not in merged:
        merged['service_date_display'] = ''
    if 'status' not in merged:
        merged['status'] = 'Processed'
    
    # Update data source if not already set
    if 'data_source' not in merged or not merged['data_source']:
        merged['data_source'] = 'OptumAI' if primary == optumai_data else 'Legacy' if primary else 'None'
    
    # If patient name still missing or unknown, infer a failure reason when possible
    # But only set error_reason if name is truly missing after all extraction attempts
    # (CSV backfill happens after merge_responses, so don't set error here if name might be backfilled)
    try:
        patient_name = merged.get('patient_name', '').strip()
        if not patient_name or patient_name == 'Unknown Patient':
            # Check if we have data but just missing name (indicating extraction issue)
            has_optumai_data = is_super_connector_response_format(optumai_data or {})
            has_legacy_data = is_legacy_response_format(legacy_data or {})
            
            if not merged.get('error_reason'):
                if has_optumai_data:
                    raw = (optumai_data or {}).get('rawGraphQLResponse', {})
                    elig = raw.get('data', {}).get('checkEligibility', {}).get('eligibility', [])
                    errors = raw.get('errors', [])
                    # Check if we have errors with extensions (multiple plans scenario)
                    has_extensions = any(
                        error.get('extensions', {}).get('details', [])
                        for error in errors
                        if error.get('code') in ['INFORMATIONAL', 'PARTIAL_DATA_RECEIVED']
                    )
                    if has_extensions and elig:
                        merged['error_reason'] = 'OptumAI eligibility present but member name missing'
                    elif not elig:
                        merged['error_reason'] = 'OptumAI response contained no eligibility records'
                    else:
                        merged['error_reason'] = 'OptumAI eligibility present but member name missing'
                elif has_legacy_data:
                    policies = (legacy_data or {}).get('memberPolicies', [])
                    merged['error_reason'] = 'Legacy API returned no memberPolicies records' if not policies else 'Legacy policy present but patient name missing'
                else:
                    merged['error_reason'] = 'Patient name not found in responses or CSV backfill'
    except Exception:
        pass

    # FIX #3: Validate insurance_type code before returning
    insurance_type = merged.get('insurance_type', '')
    if insurance_type:
        # Clean [*] markers before validation (added by backfill logic)
        clean_code = insurance_type.replace(' [*]', '').strip()
        
        # Validate using shared utility
        if clean_code and not is_valid_insurance_code(clean_code):
            if MediLink_ConfigLoader:
                MediLink_ConfigLoader.log(
                    "merge_responses: REJECTED invalid insurance_type '{}' (description or invalid format). Clearing to allow CSV/manual backfill.".format(
                        clean_code[:50]), level="WARNING")
            # Clear invalid code - downstream backfill will handle it
            merged['insurance_type'] = ''
            
            # Add diagnostic note for troubleshooting
            if 'error_reason' not in merged or not merged.get('error_reason'):
                merged['error_reason'] = 'API returned invalid insurance code format (description instead of code)'

    # Set final success status
    merged['is_successful'] = bool(merged.get('patient_name') and 
                                 merged.get('patient_name') != 'Unknown Patient' and
                                 merged.get('remaining_amount') != 'Not Found')
    return merged

def _format_patient_name_from_csv_row(row):
    """Local CSV name formatter to avoid cross-package imports"""
    try:
        if row is None:
            return ""
        if 'Patient Name' in row and row['Patient Name']:
            return str(row['Patient Name'])[:25]
        first_name = str(row.get('Patient First', '')).strip()
        last_name = str(row.get('Patient Last', '')).strip()
        middle_name = str(row.get('Patient Middle', '')).strip()
        if last_name or first_name:
            name_parts = []
            if last_name:
                name_parts.append(last_name)
            if first_name:
                if name_parts:
                    name_parts.append(", {}".format(first_name))
                else:
                    name_parts.append(first_name)
            if middle_name:
                name_parts.append(" {}".format(middle_name[:1]))
            return ''.join(name_parts)[:25]
        # Try alternative fields
        alt_first = str(row.get('First Name', row.get('First', row.get('FirstName', '')))).strip()
        alt_last = str(row.get('Last Name', row.get('Last', row.get('LastName', '')))).strip()
        if alt_first or alt_last:
            combined = (alt_first + ' ' + alt_last).strip()
            return combined[:25]
        return ""
    except Exception:
        return ""


def _extract_service_date_from_csv_row(row):
    """
    Extract service_date_display and service_date_sort (datetime) from CSV row.
    
    FIX #4: Now uses centralized validate_and_format_date() for consistent parsing.
    """
    try:
        if row is None:
            return '', datetime.min
        # Preferred fields (keep in sync with MediLink_Deductible.py header handling)
        # Surgery Date is treated as the primary source of date of service.
        candidates = [
            row.get('Surgery Date'),
            row.get('Service Date'),
            row.get('Date of Service'),
            row.get('DOS'),
            row.get('Date')
        ]
        for val in candidates:
            if not val:
                continue
            if isinstance(val, datetime):
                if val != datetime.min:
                    return val.strftime('%m-%d'), val
            elif isinstance(val, str) and val.strip() and val != 'MISSING':
                # FIX #4: Use centralized date parsing for consistency
                normalized = validate_and_format_date(val.strip())
                if normalized:
                    parsed = datetime.strptime(normalized, '%Y-%m-%d')
                    return parsed.strftime('%m-%d'), parsed
        return '', datetime.min
    except Exception:
        return '', datetime.min


def extract_group_number_from_csv_row(row):
    """
    Extract a best-effort group number from a CSV row for use with OPTUM eligibility.
    
    NOTES:
    - Primary source is the primary plan's group policy field (e.g., 'Group Policy 1').
    - We intentionally avoid using descriptive fields like 'Group Name' as these are
      often long, human-readable strings that are less reliable as true group numbers.
    - The function is conservative: if the value is empty or obviously a placeholder
      (e.g., NA / N/A / UNKNOWN), it returns an empty string so the caller can choose
      to omit groupNumber from the API request altogether.
    """
    if row is None:
        return ''
    try:
        # Candidate field names to try in order of preference.
        # This is intentionally narrow to avoid accidentally sending free-text labels.
        candidate_keys = [
            'Group Policy 1',
            'Group Policy1',
            'GroupPolicy1',
            'Group Policy',   # Fallback for older exports
            'Group #',
            'Group Number'
        ]
        for key in candidate_keys:
            if key in row:
                raw_value = row.get(key)
                if raw_value is None:
                    continue
                text = str(raw_value).strip()
                if not text:
                    continue
                lowered = text.lower()
                if lowered in ('na', 'n/a', 'unknown', 'none', 'not available', 'not_applicable'):
                    continue
                # Return the first non-empty, non-placeholder candidate as-is.
                return text
        return ''
    except Exception:
        # On any parsing error, fall back to empty string so callers can safely skip.
        return ''


def backfill_enhanced_result(enhanced_result, csv_row=None):
    """
    Ensure enhanced eligibility result has required fields populated using CSV fallbacks.
    - Fills patient_name if missing using CSV fields
    - Fills patient_id from CSV if missing
    - Fills service_date_display and service_date_sort from CSV if missing
    - Fills payer_id from CSV if missing
    - Keeps existing values intact; only fills blanks
    """
    if enhanced_result is None:
        return None
    try:
        # Shallow copy to avoid mutating caller dict
        result = dict(enhanced_result)

        # Backfill patient_name
        name_missing = (not result.get('patient_name')) or (result.get('patient_name', '').strip() == '') or (result.get('patient_name') == 'Unknown Patient')
        if name_missing:
            csv_name = _format_patient_name_from_csv_row(csv_row)
            if csv_name:
                result['patient_name'] = csv_name
                # Update error_reason if it was specifically about missing member name and we successfully backfilled from CSV
                # The name issue is resolved, but other API issues may remain (e.g., missing insurance type, policy status)
                try:
                    error_reason = result.get('error_reason', '')
                    if error_reason and 'member name missing' in error_reason.lower():
                        # Check if there are other missing fields that indicate API issues
                        insurance_missing = not result.get('insurance_type') or result.get('insurance_type') in ['Not Available', '']
                        status_missing = not result.get('policy_status') or result.get('policy_status') in ['Not Available', '']
                        if insurance_missing or status_missing:
                            # Update error to reflect that name was backfilled but other fields are missing
                            result['error_reason'] = 'OptumAI response incomplete - patient name backfilled from CSV, but insurance type or policy status missing'
                        else:
                            # Name was the only issue and it's now resolved - clear the error
                            result['error_reason'] = None
                except Exception:
                    pass
            else:
                # Attach CSV-specific diagnostic if still missing
                try:
                    if not result.get('error_reason'):
                        result['error_reason'] = 'CSV patient name fields missing or blank'
                except Exception:
                    pass

        # Backfill patient_id
        if not result.get('patient_id') and csv_row is not None:
            result['patient_id'] = str(csv_row.get('Patient ID #2', csv_row.get('Patient ID', '')))

        # Backfill payer_id
        current_payer_id = result.get('payer_id', '')
        if (not current_payer_id or not current_payer_id.strip()) and csv_row is not None:
            payer = csv_row.get('Ins1 Payer ID', '')
            if payer:
                result['payer_id'] = str(payer)

        # Backfill service dates
        if (not result.get('service_date_display')) or (result.get('service_date_sort') is None):
            display, sort_val = _extract_service_date_from_csv_row(csv_row)
            if display:
                result['service_date_display'] = display
            if 'service_date_sort' not in result or result['service_date_sort'] is None or result['service_date_sort'] == datetime.min:
                result['service_date_sort'] = sort_val

        # Normalize status
        if not result.get('status'):
            result['status'] = 'Processed'

        return result
    except Exception as e:
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Error in backfill_enhanced_result: {}".format(str(e)), level="WARNING")
        return enhanced_result


# =============================================================================
# ROW ERROR REASON COMPUTATION (centralized)
# =============================================================================

def compute_error_reason(record):
    """Compute a user-friendly error reason for an eligibility result row."""
    try:
        if not isinstance(record, dict):
            return ""
        reason = str(record.get('error_reason', '')).strip()
        name_unknown = (not str(record.get('patient_name', '')).strip()) or (record.get('patient_name') == 'Unknown Patient')
        has_error = (str(record.get('status', '')) == 'Error') or (str(record.get('data_source', '')) in ['None', 'Error'])
        amount_missing = (str(record.get('remaining_amount', '')) == 'Not Found')

        if not reason:
            if name_unknown:
                reason = 'Patient name could not be determined from API responses or CSV backfill'
            elif amount_missing:
                reason = 'Deductible remaining amount not found in eligibility response'
            elif has_error:
                reason = 'Eligibility lookup encountered an error; see logs for details'
        return reason
    except Exception:
        return ""