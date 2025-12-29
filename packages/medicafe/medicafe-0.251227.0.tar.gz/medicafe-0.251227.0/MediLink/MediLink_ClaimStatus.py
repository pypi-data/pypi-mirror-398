# MediLink_ClaimStatus.py
from datetime import datetime, timedelta
import os, sys

# Import centralized logging configuration
try:
    from MediCafe.logging_config import DEBUG, PERFORMANCE_LOGGING
except ImportError:
    # Fallback to local flags if centralized config is not available
    DEBUG = False
    PERFORMANCE_LOGGING = False

# Set up project paths first
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Use core utilities for standardized imports
try:
    from MediCafe.core_utils import get_shared_config_loader, get_api_client, create_config_cache
    MediLink_ConfigLoader = get_shared_config_loader()
except ImportError:
    print("Error: Unable to import MediCafe.core_utils. Please ensure MediCafe package is properly installed.")
    sys.exit(1)

# Import api_core for claim operations
try:
    from MediCafe import api_core
except ImportError:
    api_core = None

# Calculate start_date and end_date for the API: 
# Official API documentation parameter description requires "last date less than 31 days from the First Date"
# Note: There is a discrepancy in swagger - parameter says "< 31 days" but error code LCLM_PS_112 says "90 Days"
# We enforce 30 days (inclusive) to comply with the parameter requirement (< 31 days means max 30 days)
# Use a conservative 30-day range to stay within the 31-day limit
current_date = datetime.today()
end_date = current_date - timedelta(days=1)      # Yesterday (avoid future dates)
start_date = end_date - timedelta(days=29)       # 29 days before end date (30-day range total, inclusive)

# Validate date range according to official API documentation
def validate_date_range(start_date, end_date):
    """
    Validate date range according to official API documentation.
    
    Requirements:
    - Date range must not exceed 30 days (API parameter says "less than 31 days", meaning max 30 days inclusive)
    - Dates must be within last 24 months (per swagger LCLM_PS_107)
    - End date cannot be in the future
    - Start date must be before end date
    
    Note: Swagger discrepancy - parameter description says "< 31 days" but error code LCLM_PS_112 mentions "90 Days"
    We follow the parameter requirement which is more restrictive and clearly stated.
    """
    current_date = datetime.today()
    
    if end_date > current_date:
        raise ValueError("End date cannot be in the future")
    
    date_diff = (end_date - start_date).days
    # API parameter says "less than 31 days" which means maximum 30 days (inclusive)
    if date_diff > 30:
        raise ValueError("Date range must not exceed 30 days (API requires less than 31 days between first and last service date)")
    
    if date_diff < 0:
        raise ValueError("Start date must be before end date")
    
    # Check if dates are within reasonable range (last 24 months as per swagger LCLM_PS_107)
    max_start_date = current_date - timedelta(days=730)  # 24 months
    if start_date < max_start_date:
        raise ValueError("Start date must be within last 24 months")

# Validate the calculated date range
try:
    validate_date_range(start_date, end_date)
except ValueError as e:
    print("Date validation error: {}".format(e))
    # Fallback to a safe date range within 30 days
    end_date = current_date - timedelta(days=1)
    start_date = end_date - timedelta(days=15)  # 15-day range as fallback

end_date_str = end_date.strftime('%m/%d/%Y')
start_date_str = start_date.strftime('%m/%d/%Y')

# Inline commentary: The official API documentation parameter requires "last date less than 31 days 
# from the First Date", which means maximum 30 days inclusive. We use a 30-day range to comply.
# Note: Swagger has a discrepancy - parameter says "< 31 days" but error code LCLM_PS_112 mentions "90 Days".
# We follow the parameter requirement (30 days max) as it's the more restrictive and clearly stated limit.
if DEBUG:
    print("Using date range for API compliance (30-day range, up to yesterday)")
    print("  Start Date: {}".format(start_date_str))
    print("  End Date: {}".format(end_date_str))

# Use latest core_utils configuration cache for better performance
_get_config, (_config_cache, _crosswalk_cache) = create_config_cache()

# Load configuration using latest core_utils pattern
config, _ = _get_config()

# Error reporting imports for automated crash reporting
try:
    from MediCafe.error_reporter import capture_unhandled_traceback, submit_support_bundle_email, collect_support_bundle
except ImportError:
    capture_unhandled_traceback = None
    submit_support_bundle_email = None
    collect_support_bundle = None

# Get billing provider TIN from configuration
billing_provider_tin = config['MediLink_Config'].get('billing_provider_tin')

# Define the list of payer_id's to iterate over
payer_ids = ['87726', '03432', '96385', '95467', '86050', '86047', '95378', '37602']
# Allowed payer id's for UHC 87726, 03432, 96385, 95467, 86050, 86047, 95378, 37602. This api does not support payerId 06111.

# Initialize the API client via factory
client = get_api_client()
if client is None:
    if DEBUG:
        print("Warning: API client not available via factory")
    # Fallback to direct instantiation
    try:
        from MediCafe import api_core
        client = api_core.APIClient()
    except ImportError:
        print("Error: Unable to create API client")
        client = None

class ClaimCache:
    """In-memory cache for API responses"""
    def __init__(self):
        self.cache = {}  # {cache_key: {'data': response, 'payer_id': payer_id}}
    
    def get_cache_key(self, tin, start_date, end_date, payer_id):
        """Generate unique cache key for API call parameters"""
        return "{}_{}_{}_{}".format(tin, start_date, end_date, payer_id)
    
    def is_cached(self, cache_key):
        """Check if response is cached"""
        return cache_key in self.cache
    
    def get_cached_response(self, cache_key):
        """Retrieve cached response"""
        return self.cache[cache_key]['data']
    
    def cache_response(self, cache_key, response, payer_id):
        """Cache API response"""
        self.cache[cache_key] = {
            'data': response,
            'payer_id': payer_id
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()

class ConsolidatedClaims:
    """Consolidated claims data structure"""
    def __init__(self):
        self.claims_by_number = {}  # {claim_number: {claim_data, payer_sources: [payer_ids]}}
        self.payer_ids_checked = set()
        self.duplicate_warnings = []
    
    def add_claim(self, claim_data, payer_id):
        """Add claim to consolidated data, tracking payer sources"""
        claim_number = claim_data.get('claim_number', '')
        
        if not claim_number:
            # Skip claims without claim number
            return
        
        if claim_number not in self.claims_by_number:
            self.claims_by_number[claim_number] = {
                'data': claim_data,
                'payer_sources': [payer_id]
            }
        else:
            # Check if this is a duplicate with different data BEFORE adding payer_id
            existing_data = self.claims_by_number[claim_number]['data']
            existing_payers_before = list(self.claims_by_number[claim_number]['payer_sources'])
            
            # Always add payer_id to payer_sources, even if data differs
            if payer_id not in self.claims_by_number[claim_number]['payer_sources']:
                self.claims_by_number[claim_number]['payer_sources'].append(payer_id)
            
            # Check if this is a duplicate with different data
            if not self._claims_equal(existing_data, claim_data):
                # Different data - create warning (use payer list before adding new payer)
                self.duplicate_warnings.append({
                    'claim_number': claim_number,
                    'existing_payers': existing_payers_before,
                    'new_payer': payer_id,
                    'existing_data': existing_data,
                    'new_data': claim_data
                })
        
        self.payer_ids_checked.add(payer_id)
    
    def _claims_equal(self, claim1, claim2):
        """Compare two claim data structures for equality"""
        # Compare key fields that should be identical for the same claim
        key_fields = ['claim_status', 'patient_name', 'processed_date', 'first_service_date', 
                     'total_charged_amount', 'total_allowed_amount', 'total_paid_amount', 
                     'total_patient_responsibility_amount']
        
        for field in key_fields:
            if claim1.get(field) != claim2.get(field):
                return False
        return True

def extract_claim_data(claim):
    """Extract standardized claim data from API response with defensive checks"""
    try:
        # Use .get() with defaults to handle missing fields gracefully
        claim_number = claim.get('claimNumber', '')
        claim_status = claim.get('claimStatus', '')
        
        # Safely extract member info
        member_info = claim.get('memberInfo', {})
        patient_first_name = member_info.get('ptntFn', '')
        patient_last_name = member_info.get('ptntLn', '')
        
        # Safely extract claim summary
        claim_summary = claim.get('claimSummary', {})
        processed_date = claim_summary.get('processedDt', '')
        first_service_date = claim_summary.get('firstSrvcDt', '')
        total_charged_amount = claim_summary.get('totalChargedAmt', '0.00')
        total_allowed_amount = claim_summary.get('totalAllowdAmt', '0.00')
        total_paid_amount = claim_summary.get('totalPaidAmt', '0.00')
        total_patient_responsibility_amount = claim_summary.get('totalPtntRespAmt', '0.00')
        claim_xwalk_data = claim_summary.get('clmXWalkData', [])
        
        # Build patient name safely
        if patient_first_name or patient_last_name:
            patient_name = "{} {}".format(patient_first_name, patient_last_name).strip()
        else:
            patient_name = ''
        
        # Log warning if critical fields are missing
        if not claim_number:
            MediLink_ConfigLoader.log(
                "Warning: Claim data missing claimNumber field",
                level="WARNING",
                console_output=False
            )
        
        return {
            'claim_number': claim_number,
            'claim_status': claim_status,
            'patient_name': patient_name,
            'processed_date': processed_date,
            'first_service_date': first_service_date,
            'total_charged_amount': total_charged_amount,
            'total_allowed_amount': total_allowed_amount,
            'total_paid_amount': total_paid_amount,
            'total_patient_responsibility_amount': total_patient_responsibility_amount,
            'claim_xwalk_data': claim_xwalk_data
        }
    except Exception as e:
        # Log error and return minimal safe structure
        MediLink_ConfigLoader.log(
            "Error extracting claim data: {}".format(e),
            level="ERROR",
            console_output=False
        )
        # Return minimal structure to prevent downstream crashes
        return {
            'claim_number': claim.get('claimNumber', 'UNKNOWN'),
            'claim_status': '',
            'patient_name': '',
            'processed_date': '',
            'first_service_date': '',
            'total_charged_amount': '0.00',
            'total_allowed_amount': '0.00',
            'total_paid_amount': '0.00',
            'total_patient_responsibility_amount': '0.00',
            'claim_xwalk_data': []
        }

def handle_api_error(error, payer_id):
    """Handle specific API errors according to official documentation"""
    error_message = str(error)
    
    # Handle specific error codes from official documentation
    if "LCLM_PS_102" in error_message:
        return "Mandatory element missing in request (tin, firstServiceDt, lastServiceDt, or payerId)"
    elif "LCLM_PS_105" in error_message or "LCLM_PS_202" in error_message:
        return "Authorization error: Payer ID {} not allowed".format(payer_id)
    elif "LCLM_PS_106" in error_message:
        return "Invalid parameter combination: must use (firstServiceDt,lastServiceDt) or (transactionId)"
    elif "LCLM_PS_107" in error_message:
        return "Date range must be within last 24 months"
    elif "LCLM_PS_108" in error_message or "LCLM_PS_111" in error_message:
        return "Incorrect date format: use MM/dd/yyyy"
    elif "LCLM_PS_112" in error_message:
        # Note: Swagger parameter description says "less than 31 days" but error code LCLM_PS_112 says "90 Days"
        # We enforce 30 days to comply with the parameter requirement (< 31 days)
        return "Date range exceeds 30 days limit (API requires less than 31 days between first and last service date)"
    elif "LCLM_PS_113" in error_message:
        return "Incorrect Last Service Date format or value"
    elif "LCLM_PS_201" in error_message:
        return "No data found with given request parameters"
    elif "LCLM_PS_203" in error_message:
        return "No data found with given TransactionId - pagination token may be expired"
    elif "LCLM_PS_307" in error_message:
        return "Claim found but date of service does not match search criteria"
    elif "LCLM_PS_301" in error_message:
        return "Timeout exception from service - retry may be needed"
    elif "LCLM_PS_302" in error_message:
        return "Super user exception from service"
    elif "LCLM_PS_303" in error_message:
        return "System failure while fetching response"
    elif "LCLM_PS_304" in error_message:
        return "Error received from backend service"
    elif "LCLM_PA_500" in error_message:
        return "System failure while fetching response (PA endpoint)"
    elif "LCLM_PS_306" in error_message:
        # Critical error: search exceeds API limit
        return "Search exceeds 500 claims limit - narrow date range"
    elif "LCLM_PS_305" in error_message:
        # Critical error: system could not retrieve all claims
        return "System could not retrieve all claims - try pagination or narrower search"
    elif "LCLM_PS_500" in error_message:
        return "Server error: Exception from Claims 360 - try again later"
    elif "401" in error_message:
        return "Authentication error: check credentials"
    elif "403" in error_message:
        return "Authorization error: insufficient permissions"
    elif "500" in error_message:
        return "Server error: internal system failure"
    else:
        return "Unknown error: {}".format(error_message)

def process_claims_with_pagination(client, billing_provider_tin, start_date_str, end_date_str, payer_id):
    """
    Process all claims for a single payer ID with proper pagination handling
    """
    all_claims = []
    transaction_id = None
    page_count = 0
    total_claims_retrieved = 0
    
    while True:
        page_count += 1
        if DEBUG:
            print("    Fetching page {} for Payer ID: {}".format(page_count, payer_id))
        
        try:
            # Import api_core locally to ensure it's available
            from MediCafe import api_core
            claim_summary = api_core.get_claim_summary_by_provider(
                client, billing_provider_tin, start_date_str, end_date_str, 
                payer_id=payer_id, transaction_id=transaction_id
            )
            # Validate response is a dictionary
            if not isinstance(claim_summary, dict):
                raise ValueError("Invalid API response: expected dict, got {}".format(type(claim_summary).__name__))
            
            # Informational notice if new OPTUM Real endpoint is being used
            try:
                if claim_summary.get('data_source') == 'OPTUMAI':
                    MediLink_ConfigLoader.log(
                        "Claims Inquiry via Optum Real endpoint (OPTUMAI) with legacy-compatible output.",
                        level="INFO"
                    )
                    if DEBUG:
                        print("[Info] Using Optum Real Claims Inquiry for payer {}".format(payer_id))
            except Exception:
                pass
            
            # Extract claims from this page
            claims = claim_summary.get('claims', [])
            page_claim_count = len(claims)
            all_claims.extend(claims)
            total_claims_retrieved += page_claim_count
            
            # Response monitoring: Check for pagination token
            new_transaction_id = claim_summary.get('transactionId')
            
            if new_transaction_id:
                MediLink_ConfigLoader.log(
                    "PAGINATION DETECTED: Payer {} page {} returned {} claims with transactionId: {}".format(
                        payer_id, page_count, page_claim_count, new_transaction_id
                    ),
                    level="INFO"
                )
                transaction_id = new_transaction_id
            else:
                MediLink_ConfigLoader.log(
                    "PAGINATION COMPLETE: Payer {} page {} returned {} claims (final page)".format(
                        payer_id, page_count, page_claim_count
                    ),
                    level="INFO"
                )
                break
            
            # Safety check to prevent infinite loops (API max is 500 claims)
            # Check claim count first (primary limit), then page count as secondary safety
            if total_claims_retrieved >= 500:
                MediLink_ConfigLoader.log(
                    "Reached maximum claim limit (500) for payer {}. Total claims retrieved: {} across {} pages".format(
                        payer_id, total_claims_retrieved, page_count
                    ),
                    level="WARNING"
                )
                break
            elif page_count >= 20:  # Secondary safety: max 20 pages (20 * 50 = 1000, well above API limit)
                MediLink_ConfigLoader.log(
                    "Reached maximum page limit (20) for payer {}. Total claims retrieved: {} across {} pages".format(
                        payer_id, total_claims_retrieved, page_count
                    ),
                    level="WARNING"
                )
                break
                
        except Exception as e:
            error_msg = handle_api_error(e, payer_id)
            error_str = str(e)
            
            # Standardized error handling pattern:
            # Critical errors (limits, retrieval failures): print + log with ERROR level
            # Other errors: log only with appropriate level
            if "LCLM_PS_306" in error_str or "exceeds 500 claims" in error_str:
                # Critical: search exceeds API limit
                print("  LIMIT ERROR for Payer ID {}: {}".format(payer_id, error_msg))
                MediLink_ConfigLoader.log(
                    "LIMIT ERROR for Payer ID {}: {}".format(payer_id, error_msg),
                    level="ERROR"
                )
            elif "LCLM_PS_305" in error_str or "could not retrieve all claims" in error_str:
                # Critical: system could not retrieve all claims
                print("  RETRIEVAL ERROR for Payer ID {}: {}".format(payer_id, error_msg))
                MediLink_ConfigLoader.log(
                    "RETRIEVAL ERROR for Payer ID {}: {}".format(payer_id, error_msg),
                    level="ERROR"
                )
            elif "LCLM_PS_201" in error_str or "LCLM_PS_203" in error_str:
                # Recoverable: no data found (may be expected)
                MediLink_ConfigLoader.log(
                    "No data found for Payer ID {}: {}".format(payer_id, error_msg),
                    level="WARNING",
                    console_output=False
                )
            else:
                # Other errors: print + log (inform user but not as critical as limit errors)
                print("  Error processing Payer ID {}: {}".format(payer_id, error_msg))
                MediLink_ConfigLoader.log(
                    "API Error for Payer ID {}: {}".format(payer_id, error_msg),
                    level="ERROR",
                    console_output=False
                )
            break
    
    if DEBUG:
        print("  Total claims retrieved for Payer ID {}: {} across {} pages".format(
            payer_id, total_claims_retrieved, page_count))
    
    return all_claims

def process_claims_with_payer_rotation(billing_provider_tin, start_date_str, end_date_str, 
                                     payer_ids, cache, consolidated_claims):
    """
    Process claims across multiple payer IDs with caching, consolidation, and pagination
    """
    from MediCafe.core_utils import get_api_client
    client = get_api_client()
    if client is None:
        if DEBUG:
            print("Warning: API client not available via factory")
        # Fallback to direct instantiation
        try:
            from MediCafe import api_core
            client = api_core.APIClient()
        except ImportError:
            print("Error: Unable to create API client")
            return
    
    for payer_id in payer_ids:
        if DEBUG:
            print("Processing Payer ID: {}".format(payer_id))
        
        # Generate cache key (using base parameters, pagination handled separately)
        cache_key = cache.get_cache_key(billing_provider_tin, start_date_str, end_date_str, payer_id)
        
        # Check cache first
        if cache.is_cached(cache_key):
            if DEBUG:
                print("  Using cached response for Payer ID: {}".format(payer_id))
            # For cached responses, we assume all pages were already retrieved
            cached_response = cache.get_cached_response(cache_key)
            claims = cached_response.get('claims', [])
        else:
            if DEBUG:
                print("  Making API call(s) with pagination for Payer ID: {}".format(payer_id))
            
            # Process all pages for this payer ID
            claims = process_claims_with_pagination(
                client, billing_provider_tin, start_date_str, end_date_str, payer_id
            )
            
            # Cache the consolidated result (all pages combined)
            consolidated_response = {'claims': claims}
            cache.cache_response(cache_key, consolidated_response, payer_id)
        
        # Process all claims from this payer (all pages)
        for claim in claims:
            claim_data = extract_claim_data(claim)
            consolidated_claims.add_claim(claim_data, payer_id)

def display_consolidated_claims(consolidated_claims, output_file):
    """
    Display consolidated claims with payer ID header and duplicate warnings
    """
    # Display header with all payer IDs checked
    payer_ids_str = ", ".join(sorted(consolidated_claims.payer_ids_checked))
    header = "Payer IDs Checked: {} | Start Date: {} | End Date: {}".format(
        payer_ids_str, start_date_str, end_date_str)
    print(header)
    output_file.write(header + "\n")
    print("=" * len(header))
    output_file.write("=" * len(header) + "\n")
    
    # Table header
    table_header = "{:<10} | {:<10} | {:<20} | {:<6} | {:<6} | {:<7} | {:<7} | {:<7} | {:<7} | {:<15}".format(
        "Claim #", "Status", "Patient", "Proc.", "Serv.", "Allowed", "Paid", "Pt Resp", "Charged", "Payer Sources")
    print(table_header)
    output_file.write(table_header + "\n")
    print("-" * len(table_header))
    output_file.write("-" * len(table_header) + "\n")
    
    # Sort claims by first service date (handle missing dates gracefully)
    # Use '9999/99/99' as sort key for missing dates to put them at the end
    sorted_claims = sorted(
        consolidated_claims.claims_by_number.items(),
        key=lambda x: x[1]['data'].get('first_service_date', '') or '9999/99/99'
    )
    
    # Display each claim
    for claim_number, claim_info in sorted_claims:
        claim_data = claim_info['data']
        payer_sources = claim_info['payer_sources']
        
        # Format payer sources with truncation for long lists
        sorted_payers = sorted(payer_sources)
        max_payer_display_length = 15  # Match table column width
        if len(sorted_payers) == 0:
            payer_sources_str = ''
        elif len(sorted_payers) == 1:
            payer_sources_str = sorted_payers[0]
        else:
            payer_sources_str = ", ".join(sorted_payers)
            # If too long, show count or truncate
            if len(payer_sources_str) > max_payer_display_length:
                if len(sorted_payers) > 3:
                    # Show count if many payers
                    payer_sources_str = "{} payers".format(len(sorted_payers))
                else:
                    # Truncate with ellipsis
                    payer_sources_str = payer_sources_str[:max_payer_display_length-3] + "..."
        
        table_row = "{:<10} | {:<10} | {:<20} | {:<6} | {:<6} | {:<7} | {:<7} | {:<7} | {:<7} | {:<15}".format(
            claim_number, claim_data.get('claim_status', '')[:10], claim_data.get('patient_name', '')[:20],
            claim_data.get('processed_date', '')[:5], claim_data.get('first_service_date', '')[:5],
            claim_data.get('total_allowed_amount', '0.00'), claim_data.get('total_paid_amount', '0.00'),
            claim_data.get('total_patient_responsibility_amount', '0.00'), claim_data.get('total_charged_amount', '0.00'),
            payer_sources_str[:max_payer_display_length]
        )
        print(table_row)
        output_file.write(table_row + "\n")
        
        # Display crosswalk data for $0.00 claims
        if claim_data.get('total_paid_amount') == '0.00':
            claim_xwalk_data = claim_data.get('claim_xwalk_data', [])
            # Check if claim_xwalk_data exists and is iterable
            if isinstance(claim_xwalk_data, list):
                for xwalk in claim_xwalk_data:
                    if isinstance(xwalk, dict):
                        clm507Cd = xwalk.get('clm507Cd', '')
                        clm507CdDesc = xwalk.get('clm507CdDesc', '')
                        clm508Cd = xwalk.get('clm508Cd', '')
                        clm508CdDesc = xwalk.get('clm508CdDesc', '')
                        clmIcnSufxCd = xwalk.get('clmIcnSufxCd', '')
                        if DEBUG:
                            print("  507: {} ({}) | 508: {} ({}) | ICN Suffix: {}".format(
                                clm507Cd, clm507CdDesc, clm508Cd, clm508CdDesc, clmIcnSufxCd))
    
    # Display duplicate warnings (terminal, log, and output file)
    if consolidated_claims.duplicate_warnings:
        warnings_section = "\n" + "="*80 + "\n"
        warnings_section += "DUPLICATE CLAIM WARNINGS:\n"
        warnings_section += "="*80 + "\n"
        
        for warning in consolidated_claims.duplicate_warnings:
            claim_number = warning['claim_number']
            all_payers = warning['existing_payers']
            new_payer = warning['new_payer']
            existing_data = warning['existing_data']
            new_data = warning['new_data']
            
            # Build comprehensive warning message showing all payer sources
            warning_msg = (
                "Claim {} found in multiple payers with different data:\n"
                "  All payer sources: {}\n"
                "  New payer with different data: {}\n"
                "  Status difference: {} (existing) vs {} (new)\n"
                "  Paid amount difference: ${} (existing) vs ${} (new)\n"
                "  Allowed amount difference: ${} (existing) vs ${} (new)\n"
                "  Patient: {} (existing) vs {} (new)".format(
                    claim_number,
                    ", ".join(sorted(all_payers)),
                    new_payer,
                    existing_data.get('claim_status', ''),
                    new_data.get('claim_status', ''),
                    existing_data.get('total_paid_amount', '0.00'),
                    new_data.get('total_paid_amount', '0.00'),
                    existing_data.get('total_allowed_amount', '0.00'),
                    new_data.get('total_allowed_amount', '0.00'),
                    existing_data.get('patient_name', ''),
                    new_data.get('patient_name', '')
                )
            )
            
            warnings_section += warning_msg + "\n" + "-"*80 + "\n"
            
            if DEBUG:
                print(warning_msg)
            
            # Log the warning (file only, not console)
            MediLink_ConfigLoader.log(
                "Duplicate claim warning: {}".format(warning_msg),
                level="WARNING",
                console_output=False
            )
        
        # Write warnings to output file
        output_file.write(warnings_section)
        if DEBUG:
            print(warnings_section)

# Main execution with error reporting
if __name__ == "__main__":
    # Install unhandled exception hook to capture tracebacks
    try:
        if capture_unhandled_traceback is not None:
            sys.excepthook = capture_unhandled_traceback
    except Exception:
        pass

    try:
        # Initialize cache and consolidated claims
        cache = ClaimCache()
        consolidated_claims = ConsolidatedClaims()

        # Process claims with payer rotation
        process_claims_with_payer_rotation(
            billing_provider_tin, start_date_str, end_date_str, payer_ids, cache, consolidated_claims
        )

        # Display consolidated results
        temp_dir = os.getenv('TEMP') or os.getenv('TMP') or '/tmp'  # Cross-platform temp directory
        output_file_path = os.path.join(temp_dir, 'claim_summary_report.txt')
        with open(output_file_path, 'w') as output_file:
            display_consolidated_claims(consolidated_claims, output_file)

        # Clear cache after consolidated table is generated
        cache.clear_cache()

        # Open the generated file (cross-platform approach)
        try:
            if os.name == 'nt':  # Windows
                os.startfile(output_file_path)
            elif os.name == 'posix':  # Unix/Linux/MacOS
                import subprocess
                subprocess.call(['xdg-open', output_file_path])
            else:
                if DEBUG:
                    print("File saved to: {}".format(output_file_path))
        except Exception as e:
            if DEBUG:
                print("File saved to: {}".format(output_file_path))
                print("Could not open file automatically: {}".format(e))

    except Exception as e:
        print("\n" + "="*60)
        print("CLAIM STATUS EXECUTION FAILURE")
        print("="*60)
        print("Error: {}".format(e))
        print("Error type: {}".format(type(e).__name__))
        print("="*60)

        # Collect and submit error report
        try:
            if submit_support_bundle_email is not None and collect_support_bundle is not None:
                zip_path = collect_support_bundle(include_traceback=True)
                if zip_path:
                    # Try to check internet connectivity
                    try:
                        from MediCafe.core_utils import check_internet_connection
                        online = check_internet_connection()
                    except ImportError:
                        # If we can't check connectivity during error reporting, assume offline
                        # to preserve the error bundle for later
                        online = False
                        print("Warning: Could not check internet connectivity - preserving error bundle.")

                    if online:
                        success = submit_support_bundle_email(zip_path)
                        if success:
                            # On success, remove the bundle
                            try:
                                os.remove(zip_path)
                            except Exception:
                                pass
                        else:
                            # Preserve bundle for manual retry
                            print("Error report send failed - bundle preserved at {} for retry.".format(zip_path))
                    else:
                        print("Offline - error bundle queued at {} for retry when online.".format(zip_path))
                else:
                    print("Failed to create error report bundle.")
            else:
                print("Error reporting not available - check MediCafe installation.")
        except Exception as report_e:
            print("Error report collection failed: {}".format(report_e))