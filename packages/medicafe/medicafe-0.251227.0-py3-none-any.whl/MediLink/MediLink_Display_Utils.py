# MediLink_Display_Utils.py
# Display utility functions extracted from MediLink_UI.py to eliminate circular dependencies
# Provides centralized display functions for insurance options and patient summaries

from datetime import datetime
import time

# Use core utilities for standardized imports
from MediCafe.core_utils import get_shared_config_loader, extract_medilink_config
MediLink_ConfigLoader = get_shared_config_loader()

def print_error(message, sleep_seconds=3):
    """
    Print a visible error message with consistent formatting.
    
    Args:
        message: Error message string to display
        sleep_seconds: Number of seconds to pause after displaying (default: 3)
    """
    if not message:
        return
    try:
        sleep_seconds = max(0, float(sleep_seconds))
    except (ValueError, TypeError):
        sleep_seconds = 3
    try:
        print("\n" + "="*60)
        print("ERROR: {}".format(str(message)))
        print("="*60)
        time.sleep(sleep_seconds)
    except Exception as e:
        # Log exception at DEBUG level for troubleshooting, but don't break flow
        try:
            MediLink_ConfigLoader.log("Error displaying error message: {}".format(str(e)), level="DEBUG")
        except Exception:
            pass

def print_warning(message, sleep_seconds=3):
    """
    Print a visible warning message with consistent formatting.
    
    Args:
        message: Warning message string to display
        sleep_seconds: Number of seconds to pause after displaying (default: 3)
    """
    if not message:
        return
    try:
        sleep_seconds = max(0, float(sleep_seconds))
    except (ValueError, TypeError):
        sleep_seconds = 3
    try:
        print("\n" + "="*60)
        print("WARNING: {}".format(str(message)))
        print("="*60)
        time.sleep(sleep_seconds)
    except Exception as e:
        # Log exception at DEBUG level for troubleshooting, but don't break flow
        try:
            MediLink_ConfigLoader.log("Error displaying warning message: {}".format(str(e)), level="DEBUG")
        except Exception:
            pass

# Import cache lookup functions for deductible remaining amount
try:
    from MediLink.insurance_type_cache import lookup as cache_lookup, get_csv_dir_from_config
except ImportError:
    cache_lookup = None
    get_csv_dir_from_config = None

def _format_remaining_amount(remaining_amount_str):
    """Format remaining amount for display"""
    if not remaining_amount_str or remaining_amount_str.strip() == '':
        return 'N/A'
    try:
        # Try to parse as float and format
        amount = float(remaining_amount_str)
        if amount == 0:
            return '0.00'
        return '{:.2f}'.format(amount)  # Format as decimal without $ prefix
    except (ValueError, TypeError):
        return str(remaining_amount_str) if remaining_amount_str else 'N/A'

def display_insurance_options(insurance_options=None):
    """Display insurance options, loading from config if not provided"""
    
    if insurance_options is None:
        config, _ = MediLink_ConfigLoader.load_configuration()
        medi = extract_medilink_config(config)
        insurance_options = medi.get('insurance_options', {})
    
    print("\nInsurance Type Options (SBR09 Codes):")
    print("-" * 50)
    for code, description in sorted(insurance_options.items()):
        print("{:>3}: {}".format(code, description))
    print("-" * 50)
    print("Note: '12' (PPO) is the default if no selection is made.")
    print()  # Add a blank line for better readability

def display_patient_summaries(detailed_patient_data, config=None):
    """
    Displays summaries of all patients and their suggested endpoints.
    
    Args:
        detailed_patient_data: List of patient data dictionaries
        config: Optional config dictionary for cache lookup (if None, cache lookups will be skipped)
    """
    print("\nSummary of patient details and suggested endpoint:")
    
    # Sort by insurance_type_source priority for clearer grouping
    priority = {'API': 0, 'MANUAL': 1, 'DEFAULT': 2, 'DEFAULT_FALLBACK': 2}
    def sort_key(item):
        src = item.get('insurance_type_source', '')
        return (priority.get(src, 2), item.get('surgery_date', ''), item.get('patient_name', ''))
    sorted_data = sorted(detailed_patient_data, key=sort_key)

    for index, summary in enumerate(sorted_data, start=1):
        try:
            display_file_summary(index, summary, config)
        except KeyError as e:
            print("Summary at index {} is missing key: {}".format(index, e))
    print() # add blank line for improved readability.
    print("Legend: Src=API (auto), MAN (manual), DEF (default) | [DUP] indicates a previously submitted matching claim")

def display_file_summary(index, summary, config=None):
    # Ensure surgery_date is converted to a datetime object
    surgery_date = datetime.strptime(summary['surgery_date'], "%m-%d-%y")
    
    # Perform cache lookup for deductible remaining amount
    remaining_amount_display = 'N/A'
    if cache_lookup and get_csv_dir_from_config and config:
        try:
            csv_dir = get_csv_dir_from_config(config)
            patid = summary.get('patid', '')
            if csv_dir and patid:
                # Convert surgery_date to YYYY-MM-DD format for cache lookup
                service_date_iso = surgery_date.strftime('%Y-%m-%d')
                # Lookup cache with return_full=True to get remaining_amount
                cache_result = cache_lookup(patient_id=patid, csv_dir=csv_dir, return_full=True, service_date=service_date_iso)
                if cache_result:
                    remaining_amount = cache_result.get('remaining_amount', '')
                    remaining_amount_display = _format_remaining_amount(remaining_amount)
        except Exception as e:
            # Fail gracefully - log at DEBUG level only (avoid HIPAA data in logs)
            try:
                MediLink_ConfigLoader.log("Cache lookup error in display_file_summary: {}".format(str(e)), level="DEBUG")
            except Exception:
                pass  # Silently fail if logging unavailable
    
    # Add header row if it's the first index
    if index == 1:
        print("{:<3} {:5} {:<10} {:<20} {:<15} {:<3} {:<5} {:<12} {:<20}".format(
            "No.", "Date", "ID", "Name", "Primary Ins.", "IT", "Src", "Deductible", "Current Endpoint"
        ))
        # Separator width matches header format: 3+5+10+20+15+3+5+12+20 + padding = 104
        print("-"*104)

    # Check if insurance_type is available; if not, set a default placeholder (this should already be '12' at this point)
    insurance_type = summary.get('insurance_type', '--')
    insurance_source = summary.get('insurance_type_source', '')
    duplicate_flag = '[DUP]' if summary.get('duplicate_candidate') else ''
    
    # Get the effective endpoint (confirmed > user preference > suggestion > default)
    effective_endpoint = (summary.get('confirmed_endpoint') or 
                         summary.get('user_preferred_endpoint') or 
                         summary.get('suggested_endpoint', 'AVAILITY'))

    # Format insurance type for display - prioritize code (SBR09/insuranceTypeCode)
    if insurance_type and len(insurance_type) <= 3:
        insurance_display = insurance_type
    else:
        # If description was provided instead of code, truncate respectfully
        insurance_display = insurance_type[:3] if insurance_type else '--'

    # Shorten source for compact display
    if insurance_source in ['DEFAULT_FALLBACK', 'DEFAULT']:
        source_display = 'DEF'
    elif insurance_source == 'MANUAL':
        source_display = 'MAN'
    elif insurance_source == 'API':
        source_display = 'API'
    else:
        source_display = ''

    # When duplicate_flag is present, overlay [DUP] over IT, Src, Deductible, and Current Endpoint columns (40 chars total)
    if duplicate_flag:
        print("{:02d}. {:5} ({:<8}) {:<20} {:<15} {:<40}".format(
            index,
            surgery_date.strftime("%m-%d"),
            summary['patient_id'],
            summary['patient_name'][:20],
            summary['primary_insurance'][:15],
            duplicate_flag))
    else:
        # Normal display with IT, Src, Deductible, and Current Endpoint columns
        print("{:02d}. {:5} ({:<8}) {:<20} {:<15} {:<3} {:<5} {:<12} {:<20}".format(
            index,
            surgery_date.strftime("%m-%d"),
            summary['patient_id'],
            summary['patient_name'][:20],
            summary['primary_insurance'][:15],
            insurance_display,
            source_display,
            remaining_amount_display,
            effective_endpoint[:20]))

def _generate_deductible_column_name(deductible_type, amount_type, network_status, index=0):
    """
    TEMPORARY DIAGNOSTIC FUNCTION: Generate a concise column identifier for deductible amounts.
    
    This function creates abbreviated column identifiers for diagnostic display purposes.
    The identifiers help users identify which column contains the correct deductible value
    by providing clear, concise labels that indicate the data source characteristics.
    
    DEPRECATION PLAN:
    This is a temporary diagnostic function. Once users provide feedback on which column
    contains the correct value, and extract_super_connector_remaining_amount() is updated
    with correct selection logic, this function should be DEPRECATED and removed along with
    all diagnostic column display functionality.
    
    Args:
        deductible_type: 'individual' or 'family'
        amount_type: 'remaining' or 'plan'
        network_status: Network status string (e.g., 'InNetwork', 'OutOfNetwork', 'Tier1')
        index: Index if multiple entries exist (for uniqueness)
    
    Returns:
        str: Column identifier like "IndRem[InN]", "FamPlan[T1]", "IndRem[InN]#2", etc.
    """
    # Abbreviate deductible type
    type_abbrev = 'Ind' if deductible_type == 'individual' else 'Fam'
    
    # Abbreviate amount type
    amount_abbrev = 'Rem' if amount_type == 'remaining' else 'Plan'
    
    # Abbreviate network status
    if not network_status:
        status_abbrev = ''
    elif 'InNetwork' in network_status and 'OutOfNetwork' in network_status:
        status_abbrev = 'InN/OutN'
    elif 'InNetwork' in network_status:
        status_abbrev = 'InN'
    elif 'OutOfNetwork' in network_status:
        status_abbrev = 'OutN'
    elif 'Tier1' in network_status or 'Tier 1' in network_status:
        status_abbrev = 'T1'
    elif 'Tier2' in network_status or 'Tier 2' in network_status:
        status_abbrev = 'T2'
    else:
        # For other statuses, use first 3 characters if short, otherwise truncate
        status_abbrev = network_status[:3] if len(network_status) <= 3 else network_status[:5]
    
    # Build identifier
    identifier = "{}{}".format(type_abbrev, amount_abbrev)
    if status_abbrev:
        identifier += "[{}]".format(status_abbrev)
    
    # Add index suffix if needed for uniqueness
    if index > 0:
        identifier += "#{}".format(index + 1)
    
    return identifier

def display_enhanced_deductible_table(data, context="pre_api", title=None):
    """
    Enhanced deductible table display with unified philosophy for both pre-API and post-API contexts.
    
    When context is "post_api", diagnostic columns are displayed showing ALL possible deductible
    amounts from the GraphQL response (individual/family, remaining/plan amounts, all networkStatus
    variations). This enables users to identify which column contains the correct value, providing
    feedback to guide future updates to the selection logic in extract_super_connector_remaining_amount().
    
    Args:
        data: List of patient records (CSV rows for pre_api, or eligibility results for post_api)
        context: "pre_api" (valid rows identification) or "post_api" (eligibility results)
        title: Custom title for the table
    """
    if not data:
        print("No data to display.")
        return
    
    # Set default titles based on context
    if title is None:
        if context == "pre_api":
            title = "Valid Patients for Deductible Lookup ({} patients found)".format(len(data))
        else:
            title = "Eligibility Lookup Results"
    
    print("\n{}".format(title))
    print()
    
    # Normalize data for consistent processing
    normalized_data = []
    for item in data:
        if context == "pre_api":
            # Pre-API: working with CSV row data
            normalized_item = _normalize_pre_api_data(item)
        else:
            # Post-API: working with eligibility results
            normalized_item = _normalize_post_api_data(item)
        
        if normalized_item:
            normalized_data.append(normalized_item)
    
    if not normalized_data:
        print("No valid data to display after normalization.")
        return
    
    # Sort data: by patient name, then by service date
    normalized_data.sort(key=lambda x: (
        x.get('patient_name', '').upper(),
        x.get('service_date_sort', datetime.min),
        x.get('patient_id', '')
    ))
    
    # Group by patient for enhanced display
    grouped_data = _group_by_patient(normalized_data)
    
    # Calculate column widths for proper alignment
    col_widths = _calculate_column_widths(normalized_data, context)
    
    # Display header
    _display_table_header(col_widths, context)
    
    # Display data with grouping
    line_number = 1
    for patient_id, patient_records in grouped_data.items():
        for idx, record in enumerate(patient_records):
            if idx == 0:
                # Primary line with line number
                _display_primary_line(record, line_number, col_widths, context)
                line_number += 1
            else:
                # Secondary lines with dashes
                _display_secondary_line(record, col_widths, context)
    
    print()  # Add blank line after table
    
    # Display legend for diagnostic columns if present
    if context == "post_api" and normalized_data:
        # Check if any record has diagnostic columns
        has_diagnostic_columns = any(
            record.get('all_deductible_amounts', {}) 
            for record in normalized_data
        )
        if has_diagnostic_columns:
            _display_deductible_legend(normalized_data)

def _display_deductible_legend(normalized_data):
    """
    TEMPORARY DIAGNOSTIC FUNCTION: Display a legend explaining the deductible amount column identifiers.
    
    Shows which column identifier corresponds to which data source (individual/family,
    remaining/plan, networkStatus) to help users provide feedback on which column
    contains the correct value.
    
    DEPRECATION PLAN:
    This is a temporary diagnostic function to help identify the correct selection logic.
    Once users provide feedback on which column contains the correct value, and
    extract_super_connector_remaining_amount() is updated with correct selection logic,
    this function should be DEPRECATED and removed. Diagnostic columns and legends should
    no longer be displayed. The system will use only the single correctly-selected
    remaining_amount value.
    """
    print()
    print("Deductible Amount Column Legend:")
    print("=" * 70)
    print("Column identifiers show: [Type][AmountType][NetworkStatus]")
    print("  Type: Ind=Individual, Fam=Family")
    print("  AmountType: Rem=Remaining Amount, Plan=Plan Amount")
    print("  NetworkStatus: InN=InNetwork, OutN=OutOfNetwork, T1=Tier1, T2=Tier2")
    print()
    print("The column marked '(CURRENT)' shows the value currently selected by")
    print("extract_super_connector_remaining_amount(). Please provide feedback on")
    print("which diagnostic column contains the correct value for your use case.")
    print("=" * 70)
    print()

def _normalize_pre_api_data(row):
    """Normalize CSV row data for pre-API display"""
    try:
        # Extract patient name
        patient_name = _format_patient_name_from_csv(row)
        
        # Extract service date
        service_date_display, service_date_sort = _extract_service_date_from_csv(row)
        
        # Extract other fields
        dob = row.get('Patient DOB', row.get('DOB', ''))
        member_id = row.get('Primary Policy Number', row.get('Ins1 Member ID', '')).strip()
        payer_id = row.get('Ins1 Payer ID', '')
        patient_id = row.get('Patient ID #2', row.get('Patient ID', ''))

        # Surrogate key and warnings if patient_id missing/blank
        if not str(patient_id).strip():
            surrogate = "{}:{}".format(dob, member_id)
            patient_id = surrogate
            try:
                # Print visible warning and log as WARNING event
                print("Warning: Missing Patient ID in CSV row; using surrogate key {}".format(surrogate))
                MediLink_ConfigLoader.log(
                    "Missing Patient ID in CSV; using surrogate key {}".format(surrogate),
                    level="WARNING"
                )
            except Exception:
                pass
        
        return {
            'patient_id': str(patient_id),
            'patient_name': patient_name,
            'dob': dob,
            'member_id': member_id,
            'payer_id': str(payer_id),
            'service_date_display': service_date_display,
            'service_date_sort': service_date_sort,
            'status': 'Ready',
            'insurance_type': '',
            'policy_status': '',
            'remaining_amount': ''
        }
    except Exception as e:
        MediLink_ConfigLoader.log("Error normalizing pre-API data: {}".format(e), level="WARNING")
        return None

def _normalize_post_api_data(eligibility_result):
    """Normalize eligibility result data for post-API display"""
    try:
        # Handle the enhanced format that comes from convert_eligibility_to_enhanced_format
        if isinstance(eligibility_result, dict):
            normalized = {
                'patient_id': str(eligibility_result.get('patient_id', '')),
                'patient_name': str(eligibility_result.get('patient_name', '')),
                'dob': str(eligibility_result.get('dob', '')),
                'member_id': str(eligibility_result.get('member_id', '')),
                'payer_id': str(eligibility_result.get('payer_id', '')),
                'service_date_display': str(eligibility_result.get('service_date_display', '')),
                'service_date_sort': eligibility_result.get('service_date_sort', datetime.min),
                'status': str(eligibility_result.get('status', 'Processed')),
                'insurance_type': str(eligibility_result.get('insurance_type', '')),
                'policy_status': str(eligibility_result.get('policy_status', '')),
                'remaining_amount': str(eligibility_result.get('remaining_amount', '')),
                'data_source': str(eligibility_result.get('data_source', '')),
                'error_reason': str(eligibility_result.get('error_reason', '')),
                'is_successful': bool(eligibility_result.get('is_successful', False)),
                # TEMPORARY: Extract all_deductible_amounts for diagnostic display
                # TODO: DEPRECATE - Remove this field extraction once correct selection logic is implemented
                'all_deductible_amounts': eligibility_result.get('all_deductible_amounts', {})
            }

            # Default unknown patient name when blank
            try:
                if not normalized['patient_name'].strip():
                    normalized['patient_name'] = 'Unknown Patient'
            except Exception:
                normalized['patient_name'] = 'Unknown Patient'

            # Surrogate key and warnings if patient_id missing/blank
            try:
                if not normalized['patient_id'].strip():
                    surrogate = "{}:{}".format(normalized.get('dob', ''), normalized.get('member_id', ''))
                    normalized['patient_id'] = surrogate
                    print("Warning: Missing Patient ID in eligibility result; using surrogate key {}".format(surrogate))
                    MediLink_ConfigLoader.log(
                        "Missing Patient ID in eligibility result; using surrogate key {}".format(surrogate),
                        level="WARNING"
                    )
            except Exception:
                pass

            return normalized
        else:
            MediLink_ConfigLoader.log("Unexpected eligibility result format: {}".format(type(eligibility_result)), level="WARNING")
            return None
    except Exception as e:
        MediLink_ConfigLoader.log("Error normalizing post-API data: {}".format(e), level="WARNING")
        return None

def _format_patient_name_from_csv(row):
    """Format patient name as LAST, FIRST from CSV data"""
    try:
        # Check if Patient Name is already constructed
        if 'Patient Name' in row and row['Patient Name']:
            return str(row['Patient Name'])[:25]  # Limit length
        
        # Otherwise construct from parts
        first_name = row.get('Patient First', '').strip()
        last_name = row.get('Patient Last', '').strip()
        middle_name = row.get('Patient Middle', '').strip()
        
        if last_name or first_name:
            # Format as "LAST, FIRST MIDDLE"
            name_parts = []
            if last_name:
                name_parts.append(last_name)
            if first_name:
                if name_parts:
                    name_parts.append(", {}".format(first_name))
                else:
                    name_parts.append(first_name)
            if middle_name:
                name_parts.append(" {}".format(middle_name[:1]))  # Just first initial
            
            return ''.join(name_parts)[:25]  # Limit length
        
        return "Unknown Patient"
    except Exception:
        return "Unknown Patient"

def _extract_service_date_from_csv(row):
    """Extract and format service date from CSV data"""
    try:
        # Try Surgery Date first
        surgery_date = row.get('Surgery Date')
        if surgery_date:
            if isinstance(surgery_date, datetime):
                if surgery_date != datetime.min:
                    return surgery_date.strftime('%m-%d'), surgery_date
            elif isinstance(surgery_date, str) and surgery_date.strip() and surgery_date != 'MISSING':
                try:
                    # Try to parse common date formats
                    for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            parsed_date = datetime.strptime(surgery_date.strip(), fmt)
                            return parsed_date.strftime('%m-%d'), parsed_date
                        except ValueError:
                            continue
                except Exception:
                    pass
        
        # Try other possible date fields
        for date_field in ['Date of Service', 'Service Date', 'DOS']:
            date_value = row.get(date_field)
            if date_value and isinstance(date_value, str) and date_value.strip():
                try:
                    for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            parsed_date = datetime.strptime(date_value.strip(), fmt)
                            return parsed_date.strftime('%m-%d'), parsed_date
                        except ValueError:
                            continue
                except Exception:
                    pass
        
        # Default to unknown
        return "Unknown", datetime.min
    except Exception:
        return "Unknown", datetime.min

def _group_by_patient(normalized_data):
    """Group normalized data by patient ID"""
    grouped = {}
    for record in normalized_data:
        patient_id = record.get('patient_id', 'Unknown')
        if patient_id not in grouped:
            grouped[patient_id] = []
        grouped[patient_id].append(record)
    return grouped

def _calculate_column_widths(normalized_data, context):
    """
    Calculate optimal column widths based on data.
    
    When context is "post_api", this function also calculates widths for diagnostic
    deductible columns. These columns show all possible deductible amounts to help
    users identify which value should be selected by the default logic.
    """
    widths = {
        'patient_id': max(10, max(len(str(r.get('patient_id', ''))) for r in normalized_data) if normalized_data else 10),
        'patient_name': max(20, max(len(str(r.get('patient_name', ''))) for r in normalized_data) if normalized_data else 20),
        'dob': 10,
        'member_id': max(12, max(len(str(r.get('member_id', ''))) for r in normalized_data) if normalized_data else 12),
        'payer_id': 8,
        'service_date': 10,
        'status': 8
    }
    
    # Diagnostic deductible column widths (empty list if no diagnostic columns)
    diagnostic_columns = []
    diagnostic_widths = {}
    
    if context == "post_api":
        # Insurance type codes are 1-3 characters, so cap at 8 for display (code + padding)
        insurance_type_widths = [len(str(r.get('insurance_type', ''))) for r in normalized_data] if normalized_data else []
        max_insurance_type_width = max(insurance_type_widths) if insurance_type_widths else 0
        # Cap at 8 characters maximum (insurance codes are 1-3 chars, but allow some padding)
        widths.update({
            'insurance_type': min(8, max(4, max_insurance_type_width)),
            'policy_status': 12,
            'remaining_amount': 12,
            'data_source': 10
        })
        
        # Collect all deductible amounts and generate column identifiers
        all_deductible_columns = {}  # Key: column_identifier, Value: list of values
        
        for record in normalized_data:
            all_deductible_amounts = record.get('all_deductible_amounts', {})
            if not all_deductible_amounts:
                continue
            
            # Process individual remaining amounts
            for idx, item in enumerate(all_deductible_amounts.get('individual_remaining', [])):
                col_name = _generate_deductible_column_name('individual', 'remaining', item.get('networkStatus', ''), idx)
                if col_name not in all_deductible_columns:
                    all_deductible_columns[col_name] = []
                all_deductible_columns[col_name].append(item.get('amount', 'N/A'))
            
            # Process family remaining amounts
            for idx, item in enumerate(all_deductible_amounts.get('family_remaining', [])):
                col_name = _generate_deductible_column_name('family', 'remaining', item.get('networkStatus', ''), idx)
                if col_name not in all_deductible_columns:
                    all_deductible_columns[col_name] = []
                all_deductible_columns[col_name].append(item.get('amount', 'N/A'))
            
            # Process individual plan amounts
            for idx, item in enumerate(all_deductible_amounts.get('individual_plan', [])):
                col_name = _generate_deductible_column_name('individual', 'plan', item.get('networkStatus', ''), idx)
                if col_name not in all_deductible_columns:
                    all_deductible_columns[col_name] = []
                all_deductible_columns[col_name].append(item.get('amount', 'N/A'))
            
            # Process family plan amounts
            for idx, item in enumerate(all_deductible_amounts.get('family_plan', [])):
                col_name = _generate_deductible_column_name('family', 'plan', item.get('networkStatus', ''), idx)
                if col_name not in all_deductible_columns:
                    all_deductible_columns[col_name] = []
                all_deductible_columns[col_name].append(item.get('amount', 'N/A'))
        
        # Calculate widths for each diagnostic column
        # Width should accommodate both the column identifier (header) and the values
        for col_name, values in all_deductible_columns.items():
            # Calculate width based on column name and values
            header_width = len(col_name)
            value_widths = [len(str(v)) for v in values] if values else [0]
            max_value_width = max(value_widths) if value_widths else 0
            # Use the maximum of header width + 2, max value width, or minimum 8
            diagnostic_widths[col_name] = max(8, header_width + 2, max_value_width)
            diagnostic_columns.append(col_name)
        
        # Sort diagnostic columns for consistent display order
        diagnostic_columns.sort()
    
    widths['diagnostic_columns'] = diagnostic_columns
    widths['diagnostic_widths'] = diagnostic_widths
    
    return widths

def _display_table_header(col_widths, context):
    """Display table header based on context"""
    if context == "pre_api":
        header_format = "No.  {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}}"
        header = header_format.format(
            "Patient ID", col_widths['patient_id'],
            "Patient Name", col_widths['patient_name'],
            "DOB", col_widths['dob'],
            "Member ID", col_widths['member_id'],
            "Payer ID", col_widths['payer_id'],
            "Service Date", col_widths['service_date'],
            "Status", col_widths['status']
        )
        print(header)
        print("-" * len(header))
    else:
        # Build base header format
        header_format_parts = ["No.  {:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}"]
        header_format = " | ".join(header_format_parts)
        
        # Build header values - mark current "Remaining Amt" column with "(CURRENT)"
        header_values = [
            ("Patient ID", col_widths['patient_id']),
            ("Patient Name", col_widths['patient_name']),
            ("DOB", col_widths['dob']),
            ("Member ID", col_widths['member_id']),
            ("Payer ID", col_widths['payer_id']),
            ("Service Date", col_widths['service_date']),
            ("IT Code", col_widths['insurance_type']),
            ("Policy Status", col_widths['policy_status']),
            ("Remaining Amt (CURRENT)", col_widths['remaining_amount']),
            ("Data Source", col_widths.get('data_source', 10))
        ]
        
        # Add diagnostic columns if present
        diagnostic_columns = col_widths.get('diagnostic_columns', [])
        diagnostic_widths = col_widths.get('diagnostic_widths', {})
        
        if diagnostic_columns:
            # Add format placeholders for each diagnostic column
            for col_name in diagnostic_columns:
                header_format += " | {:<{}}"
                header_values.append((col_name, diagnostic_widths.get(col_name, 10)))
        
        # Format header
        header = header_format.format(*[val for pair in header_values for val in pair])
        print(header)
        print("-" * len(header))

def _get_diagnostic_value(record, col_name):
    """
    Get the diagnostic deductible value for a specific column identifier.
    
    Args:
        record: Normalized record containing all_deductible_amounts
        col_name: Column identifier (e.g., "IndRem[InN]", "FamPlan[T1]")
    
    Returns:
        str: Formatted value, or "N/A" if not found
    """
    all_deductible_amounts = record.get('all_deductible_amounts', {})
    if not all_deductible_amounts:
        return "N/A"
    
    # Parse column name to determine which list to search
    # Format: IndRem[InN], FamPlan[T1], etc.
    if col_name.startswith('IndRem'):
        items = all_deductible_amounts.get('individual_remaining', [])
        amount_type = 'remaining'
        deductible_type = 'individual'
    elif col_name.startswith('FamRem'):
        items = all_deductible_amounts.get('family_remaining', [])
        amount_type = 'remaining'
        deductible_type = 'family'
    elif col_name.startswith('IndPlan'):
        items = all_deductible_amounts.get('individual_plan', [])
        amount_type = 'plan'
        deductible_type = 'individual'
    elif col_name.startswith('FamPlan'):
        items = all_deductible_amounts.get('family_plan', [])
        amount_type = 'plan'
        deductible_type = 'family'
    else:
        return "N/A"
    
    # Extract network status from column name (between brackets)
    bracket_start = col_name.find('[')
    bracket_end = col_name.find(']')
    if bracket_start >= 0 and bracket_end > bracket_start:
        network_status_abbrev = col_name[bracket_start+1:bracket_end]
        # Reverse the abbreviation to find matching network status
        # This is a simple reverse lookup - could be enhanced if needed
        network_status_map = {
            'InN': 'InNetwork',
            'OutN': 'OutOfNetwork',
            'InN/OutN': 'InNetwork/OutOfNetwork',
            'T1': 'Tier1',
            'T2': 'Tier2'
        }
        network_status = network_status_map.get(network_status_abbrev, network_status_abbrev)
    else:
        network_status = ''
    
    # Check for index suffix (#2, #3, etc.)
    hash_idx = col_name.find('#')
    index = 0
    if hash_idx >= 0:
        try:
            parsed_index = int(col_name[hash_idx+1:]) - 1  # Convert to 0-based
            # Ensure index is non-negative (safety check)
            if parsed_index >= 0:
                index = parsed_index
            # If parsed index is negative, keep index = 0 (default)
        except (ValueError, TypeError):
            index = 0
    
    # Find matching item by network status and index
    matching_items = []
    for item in items:
        item_network_status = item.get('networkStatus', '')
        if network_status and item_network_status:
            # Match if network status contains the target status or vice versa
            if network_status in item_network_status or item_network_status in network_status:
                matching_items.append(item)
        elif not network_status and not item_network_status:
            matching_items.append(item)
    
    # Get the item at the specified index (ensure index is within bounds)
    if matching_items and 0 <= index < len(matching_items):
        amount = matching_items[index].get('amount', '')
        if amount:
            try:
                # Format number to 2 decimal places
                float_val = float(amount)
                return "{:.2f}".format(float_val)
            except (ValueError, TypeError):
                return str(amount)
    
    return "N/A"

def _display_primary_line(record, line_number, col_widths, context):
    """Display primary line with line number"""
    if context == "pre_api":
        # Enhanced status display for pre-API context
        status = record.get('status', '')
        if status == 'Ready':
            status_display = '[READY]'
        else:
            status_display = '[{}]'.format(status.upper())
        
        line_format = "{:03d}: {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}}"
        print(line_format.format(
            line_number,
            str(record.get('patient_id', ''))[:col_widths['patient_id']], col_widths['patient_id'],
            str(record.get('patient_name', ''))[:col_widths['patient_name']], col_widths['patient_name'],
            str(record.get('dob', ''))[:col_widths['dob']], col_widths['dob'],
            str(record.get('member_id', ''))[:col_widths['member_id']], col_widths['member_id'],
            str(record.get('payer_id', ''))[:col_widths['payer_id']], col_widths['payer_id'],
            str(record.get('service_date_display', ''))[:col_widths['service_date']], col_widths['service_date'],
            status_display[:col_widths['status']], col_widths['status']
        ))
    else:
        # Enhanced status display for post-API context
        status = record.get('status', '')
        if status == 'Processed':
            status_display = '[DONE]'
        elif status == 'Error':
            status_display = '[ERROR]'
        else:
            status_display = '[{}]'.format(status.upper())
        
        # Build base line format and values
        line_format_parts = ["{:03d}: {:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}"]
        line_format = " | ".join(line_format_parts)
        
        line_values = [
            (str(record.get('patient_id', ''))[:col_widths['patient_id']], col_widths['patient_id']),
            (str(record.get('patient_name', ''))[:col_widths['patient_name']], col_widths['patient_name']),
            (str(record.get('dob', ''))[:col_widths['dob']], col_widths['dob']),
            (str(record.get('member_id', ''))[:col_widths['member_id']], col_widths['member_id']),
            (str(record.get('payer_id', ''))[:col_widths['payer_id']], col_widths['payer_id']),
            (str(record.get('service_date_display', ''))[:col_widths['service_date']], col_widths['service_date']),
            (str(record.get('insurance_type', ''))[:col_widths['insurance_type']], col_widths['insurance_type']),
            (str(record.get('policy_status', ''))[:col_widths['policy_status']], col_widths['policy_status']),
            (str(record.get('remaining_amount', ''))[:col_widths['remaining_amount']], col_widths['remaining_amount']),
            (str(record.get('data_source', ''))[:col_widths['data_source']], col_widths['data_source'])
        ]
        
        # Add diagnostic column values if present
        diagnostic_columns = col_widths.get('diagnostic_columns', [])
        diagnostic_widths = col_widths.get('diagnostic_widths', {})
        
        if diagnostic_columns:
            for col_name in diagnostic_columns:
                line_format += " | {:<{}}"
                diagnostic_value = _get_diagnostic_value(record, col_name)
                col_width = diagnostic_widths.get(col_name, 10)
                line_values.append((diagnostic_value[:col_width], col_width))
        
        # Format and print line - line_number must be first argument for {:03d} format
        format_args = [line_number] + [val for pair in line_values for val in pair]
        print(line_format.format(*format_args))

        # After primary line in post-API view, display an explanatory error row when appropriate
        _maybe_display_error_row(record, context)

def _display_secondary_line(record, col_widths, context):
    """Display secondary line with dashes for grouped data"""
    patient_id_dashes = '-' * min(len(str(record.get('patient_id', ''))), col_widths['patient_id'])
    patient_name_dashes = '-' * min(len(str(record.get('patient_name', ''))), col_widths['patient_name'])
    dob_dashes = '-' * min(len(str(record.get('dob', ''))), col_widths['dob'])
    member_id_dashes = '-' * min(len(str(record.get('member_id', ''))), col_widths['member_id'])
    payer_id_dashes = '-' * min(len(str(record.get('payer_id', ''))), col_widths['payer_id'])
    
    if context == "pre_api":
        # Enhanced status display for pre-API context
        status = record.get('status', '')
        if status == 'Ready':
            status_display = '[READY]'
        else:
            status_display = '[{}]'.format(status.upper())
        
        line_format = "     {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}}"
        print(line_format.format(
            patient_id_dashes, col_widths['patient_id'],
            patient_name_dashes, col_widths['patient_name'],
            dob_dashes, col_widths['dob'],
            member_id_dashes, col_widths['member_id'],
            payer_id_dashes, col_widths['payer_id'],
            str(record.get('service_date_display', ''))[:col_widths['service_date']], col_widths['service_date'],
            status_display[:col_widths['status']], col_widths['status']
        ))
    else:
        insurance_type_dashes = '-' * min(len(str(record.get('insurance_type', ''))), col_widths['insurance_type'])
        policy_status_dashes = '-' * min(len(str(record.get('policy_status', ''))), col_widths['policy_status'])
        
        # Enhanced status display for post-API context
        status = record.get('status', '')
        if status == 'Processed':
            status_display = '[DONE]'
        elif status == 'Error':
            status_display = '[ERROR]'
        else:
            status_display = '[{}]'.format(status.upper())
        
        # Build base line format and values
        line_format_parts = ["     {:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}", "{:<{}}"]
        line_format = " | ".join(line_format_parts)
        
        line_values = [
            (patient_id_dashes, col_widths['patient_id']),
            (patient_name_dashes, col_widths['patient_name']),
            (dob_dashes, col_widths['dob']),
            (member_id_dashes, col_widths['member_id']),
            (payer_id_dashes, col_widths['payer_id']),
            (str(record.get('service_date_display', ''))[:col_widths['service_date']], col_widths['service_date']),
            (insurance_type_dashes, col_widths['insurance_type']),
            (policy_status_dashes, col_widths['policy_status']),
            (str(record.get('remaining_amount', ''))[:col_widths['remaining_amount']], col_widths['remaining_amount']),
            (str(record.get('data_source', ''))[:col_widths['data_source']], col_widths['data_source'])
        ]
        
        # Add diagnostic column dashes if present
        diagnostic_columns = col_widths.get('diagnostic_columns', [])
        diagnostic_widths = col_widths.get('diagnostic_widths', {})
        
        if diagnostic_columns:
            for col_name in diagnostic_columns:
                line_format += " | {:<{}}"
                col_width = diagnostic_widths.get(col_name, 10)
                # Use dashes for secondary line
                diagnostic_dashes = '-' * min(3, col_width)  # Short dashes for diagnostic columns
                line_values.append((diagnostic_dashes, col_width))
        
        # Format and print line
        print(line_format.format(*[val for pair in line_values for val in pair])) 

        # For grouped secondary lines, we do not repeat error rows

def _maybe_display_error_row(record, context):
    """Print an explanatory error row beneath the primary line when name or other lookups failed."""
    try:
        if context != 'post_api':
            return
        name_unknown = (not record.get('patient_name')) or (record.get('patient_name') == 'Unknown Patient')
        has_error = (record.get('status') == 'Error') or (record.get('data_source') in ['None', 'Error'])
        amount_missing = (str(record.get('remaining_amount', '')) == 'Not Found')
        reason = record.get('error_reason', '')

        if not reason:
            if name_unknown:
                reason = 'Patient name could not be determined from API responses or CSV backfill'
            elif amount_missing:
                reason = 'Deductible remaining amount not found in eligibility response'
            elif has_error:
                reason = 'Eligibility lookup encountered an error; see logs for details'

        # Prefer diagnostics lines when present; otherwise fall back to reason
        diagnostics = record.get('diagnostics', []) or []
        if diagnostics:
            # Only show first 1-2 lines to avoid noise in XP console
            to_show = diagnostics[:2]
            for line in to_show:
                print("     >> {}".format(line))
        elif reason:
            print("     >> Error: {}".format(reason))
    except Exception:
        # Never let diagnostics break table rendering
        pass