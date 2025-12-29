"""
MediLink_Deductible_Validator.py
Validation helper functions to compare legacy API responses with Super Connector API responses
Compatible with Python 3.4.4
"""
from datetime import datetime

# Python 3.4.4 compatibility imports
try:
    from io import open
except ImportError:
    pass

def deep_search_for_value(data, target_value, path="", max_depth=10, current_depth=0):
    """
    Recursively search for a value in nested dictionaries and lists.
    Returns all paths where the value is found.
    """
    if current_depth > max_depth:
        return []
    
    if data is None:
        return []
    
    found_paths = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = "{}.{}".format(path, key) if path else key
            
            # Check if this value matches our target
            if str(value) == str(target_value):
                found_paths.append(current_path)
            
            # Recursively search nested structures
            if isinstance(value, (dict, list)):
                found_paths.extend(deep_search_for_value(value, target_value, current_path, max_depth, current_depth + 1))
                
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = "{}[{}]".format(path, i)
            
            # Check if this item matches our target
            if str(item) == str(target_value):
                found_paths.append(current_path)
            
            # Recursively search nested structures
            if isinstance(item, (dict, list)):
                found_paths.extend(deep_search_for_value(item, target_value, current_path, max_depth, current_depth + 1))
    
    return found_paths

def extract_legacy_values_for_comparison(legacy_data):
    """
    Extract key values from legacy API response for comparison
    """
    comparison_values = {}
    
    if not legacy_data or "memberPolicies" not in legacy_data:
        return {}
    
    for policy in legacy_data.get("memberPolicies", []):
        # Skip non-medical policies
        if policy.get("policyInfo", {}).get("coverageType", "") != "Medical":
            continue
            
        # Extract patient info
        patient_info = policy.get("patientInfo", [{}])[0]
        comparison_values["patient_lastName"] = patient_info.get("lastName", "")
        comparison_values["patient_firstName"] = patient_info.get("firstName", "")
        comparison_values["patient_middleName"] = patient_info.get("middleName", "")
        
        # Extract insurance info
        insurance_info = policy.get("insuranceInfo", {})
        # Prefer standardized insuranceTypeCode for comparisons; keep description as secondary
        comparison_values["insurance_type"] = insurance_info.get("insuranceTypeCode", "") or insurance_info.get("insuranceType", "")
        comparison_values["insurance_typeCode"] = insurance_info.get("insuranceTypeCode", "")
        comparison_values["insurance_memberId"] = insurance_info.get("memberId", "")
        comparison_values["insurance_payerId"] = insurance_info.get("payerId", "")
        
        # Extract policy info
        policy_info = policy.get("policyInfo", {})
        comparison_values["policy_status"] = policy_info.get("policyStatus", "")
        
        # Extract deductible info
        deductible_info = policy.get("deductibleInfo", {})
        if 'individual' in deductible_info:
            comparison_values["deductible_remaining"] = deductible_info['individual']['inNetwork'].get("remainingAmount", "")
        elif 'family' in deductible_info:
            comparison_values["deductible_remaining"] = deductible_info['family']['inNetwork'].get("remainingAmount", "")
        else:
            comparison_values["deductible_remaining"] = "Not Found"
        
        # Only process the first medical policy
        break
    
    return comparison_values

def validate_super_connector_response(legacy_values, super_connector_data):
    """
    Compare legacy API values with Super Connector API response
    """
    validation_report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "legacy_values": legacy_values,
        "super_connector_analysis": {},
        "missing_values": [],
        "found_values": [],
        "data_quality_issues": []
    }
    
    if not super_connector_data:
        validation_report["super_connector_analysis"]["error"] = "No Super Connector data provided"
        return validation_report
    
    # Search for each legacy value in the Super Connector response
    for key, legacy_value in legacy_values.items():
        if legacy_value and legacy_value != "Not Found":
            found_paths = deep_search_for_value(super_connector_data, legacy_value)
            
            if found_paths:
                validation_report["found_values"].append({
                    "legacy_key": key,
                    "legacy_value": legacy_value,
                    "found_paths": found_paths
                })
            else:
                validation_report["missing_values"].append({
                    "legacy_key": key,
                    "legacy_value": legacy_value,
                    "status": "Not Found"
                })
    
    # Check for data quality issues
    data_quality_issues = check_data_quality_issues(super_connector_data)
    validation_report["data_quality_issues"] = data_quality_issues
    
    # Analyze the Super Connector response structure
    validation_report["super_connector_analysis"]["structure"] = analyze_response_structure(super_connector_data)
    
    return validation_report

def check_data_quality_issues(super_connector_data):
    """
    Check for data quality issues in Super Connector response
    """
    issues = []
    
    # Check for non-standard plan descriptions
    plan_type_desc = super_connector_data.get("planTypeDescription", "")
    if plan_type_desc and len(plan_type_desc) > 50:
        issues.append({
            "type": "Non-Standard Plan Description",
            "field": "planTypeDescription",
            "value": plan_type_desc,
            "issue": "Using vendor-specific description instead of CMS standard name",
            "recommendation": "Use standard CMS plan type names (e.g., 'Preferred Provider Organization (PPO)')"
        })
    
    # Check for generic type codes
    coverage_types = super_connector_data.get("coverageTypes", [])
    if coverage_types:
        type_code = coverage_types[0].get("typeCode", "")
        if type_code == "M":
            issues.append({
                "type": "Generic Type Code",
                "field": "coverageTypes[0].typeCode",
                "value": type_code,
                "issue": "Using generic 'Medical' code instead of specific plan type code",
                "recommendation": "Use CMS standard codes (e.g., '12' for PPO, 'HM' for HMO)"
            })
    
    # Check for missing standard fields
    if not super_connector_data.get("productType"):
        issues.append({
            "type": "Missing Standard Field",
            "field": "productType",
            "issue": "Missing standard product type field",
            "recommendation": "Include standard product type (PPO, HMO, etc.)"
        })
    
    # Check for multiple deductible amounts
    deductible_amounts = []
    if "rawGraphQLResponse" in super_connector_data:
        raw_response = super_connector_data.get('rawGraphQLResponse', {})
        data = raw_response.get('data', {})
        check_eligibility = data.get('checkEligibility', {})
        eligibility_list = check_eligibility.get('eligibility', [])
        
        for eligibility in eligibility_list:
            plan_levels = eligibility.get('eligibilityInfo', {}).get('planLevels', [])
            for plan_level in plan_levels:
                if plan_level.get('level') == 'deductibleInfo':
                    # Check individual deductibles
                    individual_levels = plan_level.get('individual', [])
                    for individual in individual_levels:
                        remaining = individual.get('remainingAmount')
                        if remaining is not None:
                            try:
                                amount = float(remaining)
                                deductible_amounts.append(('individual', amount))
                            except (ValueError, TypeError):
                                pass
                    
                    # Check family deductibles
                    family_levels = plan_level.get('family', [])
                    for family in family_levels:
                        remaining = family.get('remainingAmount')
                        if remaining is not None:
                            try:
                                amount = float(remaining)
                                deductible_amounts.append(('family', amount))
                            except (ValueError, TypeError):
                                pass
    
    # Also check top-level planLevels
    plan_levels = super_connector_data.get('planLevels', [])
    for plan_level in plan_levels:
        if plan_level.get('level') == 'deductibleInfo':
            # Check individual deductibles
            individual_levels = plan_level.get('individual', [])
            for individual in individual_levels:
                remaining = individual.get('remainingAmount')
                if remaining is not None:
                    try:
                        amount = float(remaining)
                        deductible_amounts.append(('individual', amount))
                    except (ValueError, TypeError):
                        pass
            
            # Check family deductibles
            family_levels = plan_level.get('family', [])
            for family in family_levels:
                remaining = family.get('remainingAmount')
                if remaining is not None:
                    try:
                        amount = float(remaining)
                        deductible_amounts.append(('family', amount))
                    except (ValueError, TypeError):
                        pass
    
    if len(deductible_amounts) > 1:
        # Group by type and find ranges
        individual_amounts = [amt for type_, amt in deductible_amounts if type_ == 'individual']
        family_amounts = [amt for type_, amt in deductible_amounts if type_ == 'family']
        
        issue_details = []
        if individual_amounts:
            issue_details.append("Individual: {} values (range: {}-{})".format(
                len(individual_amounts), min(individual_amounts), max(individual_amounts)))
        if family_amounts:
            issue_details.append("Family: {} values (range: {}-{})".format(
                len(family_amounts), min(family_amounts), max(family_amounts)))
        
        issues.append({
            "type": "Multiple Deductible Amounts",
            "field": "planLevels[].deductibleInfo",
            "value": "{} total amounts found".format(len(deductible_amounts)),
            "issue": "Multiple deductible amounts found: {}".format("; ".join(issue_details)),
            "recommendation": "System will select highest non-zero individual amount, then family amount"
        })
    
    # Check for API errors
    if "rawGraphQLResponse" in super_connector_data:
        raw_response = super_connector_data.get('rawGraphQLResponse', {})
        errors = raw_response.get('errors', [])
        if errors:
            for error in errors:
                error_code = error.get('code', 'UNKNOWN')
                error_desc = error.get('description', 'No description')
                
                # Check if this is an informational error with data
                if error_code == 'INFORMATIONAL':
                    extensions = error.get('extensions', {})
                    if extensions and 'details' in extensions:
                        details = extensions.get('details', [])
                        if details:
                            issues.append({
                                "type": "Informational Error with Data",
                                "field": "rawGraphQLResponse.errors",
                                "value": error_code,
                                "issue": "API returned informational error but provided data in extensions: {}".format(error_desc),
                                "recommendation": "Data available in error extensions - system will attempt to extract"
                            })
                        else:
                            issues.append({
                                "type": "API Error",
                                "field": "rawGraphQLResponse.errors",
                                "value": error_code,
                                "issue": "Super Connector API returned error: {}".format(error_desc),
                                "recommendation": "Review API implementation and error handling"
                            })
                    else:
                        issues.append({
                            "type": "API Error",
                            "field": "rawGraphQLResponse.errors",
                            "value": error_code,
                            "issue": "Super Connector API returned error: {}".format(error_desc),
                            "recommendation": "Review API implementation and error handling"
                        })
                else:
                    issues.append({
                        "type": "API Error",
                        "field": "rawGraphQLResponse.errors",
                        "value": error_code,
                        "issue": "Super Connector API returned error: {}".format(error_desc),
                        "recommendation": "Review API implementation and error handling"
                    })
        
        # Check status code
        status_code = super_connector_data.get('statuscode')
        if status_code and status_code != '200':
            issues.append({
                "type": "Non-200 Status Code",
                "field": "statuscode",
                "value": status_code,
                "issue": "API returned status code {} instead of 200".format(status_code),
                "recommendation": "Check API health and error handling"
            })
    
    # Check for multiple eligibility records (this is actually good, but worth noting)
    if "rawGraphQLResponse" in super_connector_data:
        raw_response = super_connector_data.get('rawGraphQLResponse', {})
        data = raw_response.get('data', {})
        check_eligibility = data.get('checkEligibility', {})
        eligibility_list = check_eligibility.get('eligibility', [])
        if len(eligibility_list) > 1:
            issues.append({
                "type": "Multiple Eligibility Records",
                "field": "rawGraphQLResponse.data.checkEligibility.eligibility",
                "value": "{} records found".format(len(eligibility_list)),
                "issue": "Multiple eligibility records returned - this is normal but may need special handling",
                "recommendation": "Ensure parsing logic handles multiple records correctly"
            })
    
    return issues

def analyze_response_structure(data, max_depth=5):
    """
    Analyze the structure of the Super Connector response
    """
    structure = {}
    
    def analyze_recursive(obj, path="", depth=0):
        if depth > max_depth:
            return
        
        if obj is None:
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = "{}.{}".format(path, key) if path else key
                if isinstance(value, (dict, list)):
                    structure[current_path] = "Type: {}".format(type(value).__name__)
                    analyze_recursive(value, current_path, depth + 1)
                else:
                    # Safe string conversion for Python 3.4.4
                    try:
                        value_str = str(value)[:50]
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        value_str = repr(value)[:50]
                    structure[current_path] = "Type: {}, Value: {}".format(type(value).__name__, value_str)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = "{}[{}]".format(path, i)
                if isinstance(item, (dict, list)):
                    structure[current_path] = "Type: {}".format(type(item).__name__)
                    analyze_recursive(item, current_path, depth + 1)
                else:
                    # Safe string conversion for Python 3.4.4
                    try:
                        item_str = str(item)[:50]
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        item_str = repr(item)[:50]
                    structure[current_path] = "Type: {}, Value: {}".format(type(item).__name__, item_str)
    
    analyze_recursive(data)
    return structure

def generate_validation_report(validation_report, output_file_path):
    """
    Generate a detailed validation report
    """
    # Use explicit encoding for Python 3.4.4 compatibility
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("SUPER CONNECTOR API VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write("Generated: {}\n\n".format(validation_report['timestamp']))
            
            # Legacy values section
            f.write("LEGACY API VALUES:\n")
            f.write("-" * 40 + "\n")
            for key, value in validation_report["legacy_values"].items():
                f.write("{}: {}\n".format(key, value))
            f.write("\n")
            
            # Found values section
            if validation_report["found_values"]:
                f.write("FOUND VALUES IN SUPER CONNECTOR RESPONSE:\n")
                f.write("-" * 50 + "\n")
                for item in validation_report["found_values"]:
                    f.write("Legacy Key: {}\n".format(item['legacy_key']))
                    f.write("Legacy Value: {}\n".format(item['legacy_value']))
                    f.write("Found at paths:\n")
                    for path in item['found_paths']:
                        f.write("  - {}\n".format(path))
                    f.write("\n")
            
            # Missing values section
            if validation_report["missing_values"]:
                f.write("MISSING VALUES IN SUPER CONNECTOR RESPONSE:\n")
                f.write("-" * 50 + "\n")
                for item in validation_report["missing_values"]:
                    f.write("Legacy Key: {}\n".format(item['legacy_key']))
                    f.write("Legacy Value: {}\n".format(item['legacy_value']))
                    f.write("Status: {}\n\n".format(item['status']))
            
            # Data Quality Issues section
            if validation_report["data_quality_issues"]:
                f.write("\nDATA QUALITY ISSUES:\n")
                f.write("-" * 50 + "\n")
                for issue in validation_report["data_quality_issues"]:
                    f.write("Type: {}\n".format(issue['type']))
                    f.write("Field: {}\n".format(issue['field']))
                    if 'value' in issue:
                        f.write("Value: {}\n".format(issue['value']))
                    f.write("Issue: {}\n".format(issue['issue']))
                    f.write("Recommendation: {}\n".format(issue['recommendation']))
                    f.write("\n")
            
            # API Status Information
            if "legacy_api_status" in validation_report["super_connector_analysis"]:
                f.write("\nAPI STATUS:\n")
                f.write("-" * 50 + "\n")
                f.write("Legacy API: {}\n".format(validation_report["super_connector_analysis"]["legacy_api_status"]))
                f.write("Super Connector API: {}\n".format(validation_report["super_connector_analysis"]["super_connector_api_status"]))
            
            # Super Connector structure analysis
            if "structure" in validation_report["super_connector_analysis"]:
                f.write("\nSUPER CONNECTOR RESPONSE STRUCTURE:\n")
                f.write("-" * 50 + "\n")
                for path, description in validation_report["super_connector_analysis"]["structure"].items():
                    f.write("{}: {}\n".format(path, description))
            
            # Summary
            f.write("\n" + "=" * 80 + "\n")
            f.write("SUMMARY:\n")
            f.write("Total legacy values: {}\n".format(len(validation_report['legacy_values'])))
            f.write("Found in Super Connector: {}\n".format(len(validation_report['found_values'])))
            f.write("Missing from Super Connector: {}\n".format(len(validation_report['missing_values'])))
            f.write("Data quality issues: {}\n".format(len(validation_report['data_quality_issues'])))
            f.write("=" * 80 + "\n")
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        # Fallback for encoding issues
        with open(output_file_path, 'w', encoding='latin-1') as f:
            f.write("=" * 80 + "\n")
            f.write("SUPER CONNECTOR API VALIDATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write("Generated: {}\n\n".format(validation_report['timestamp']))
            f.write("Note: Some characters may not display correctly due to encoding limitations.\n\n")
            
            # Legacy values section
            f.write("LEGACY API VALUES:\n")
            f.write("-" * 40 + "\n")
            for key, value in validation_report["legacy_values"].items():
                f.write("{}: {}\n".format(key, value))
            f.write("\n")
            
            # Summary
            f.write("\n" + "=" * 80 + "\n")
            f.write("SUMMARY:\n")
            f.write("Total legacy values: {}\n".format(len(validation_report['legacy_values'])))
            f.write("Found in Super Connector: {}\n".format(len(validation_report['found_values'])))
            f.write("Missing from Super Connector: {}\n".format(len(validation_report['missing_values'])))
            f.write("Data quality issues: {}\n".format(len(validation_report['data_quality_issues'])))
            f.write("=" * 80 + "\n")

def run_validation_comparison(legacy_data, super_connector_data, output_file_path):
    """
    Main function to run the validation comparison
    """
    # Handle cases where one or both APIs failed
    if not legacy_data and not super_connector_data:
        # Both APIs failed - create a minimal report
        validation_report = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "legacy_values": {},
            "super_connector_analysis": {"error": "Both APIs failed to return data"},
            "missing_values": [],
            "found_values": [],
            "data_quality_issues": [{
                "type": "API Failure",
                "field": "Both APIs",
                "issue": "Both Legacy API and Super Connector API failed to return data",
                "recommendation": "Check API connectivity and credentials"
            }]
        }
        generate_validation_report(validation_report, output_file_path)
        return validation_report
    
    # Extract values from legacy response (handles None gracefully)
    legacy_values = extract_legacy_values_for_comparison(legacy_data or {})
    
    # Validate Super Connector response (handles None gracefully)
    validation_report = validate_super_connector_response(legacy_values, super_connector_data or {})
    
    # Add API status information
    if not legacy_data:
        validation_report["super_connector_analysis"]["legacy_api_status"] = "Failed"
    else:
        validation_report["super_connector_analysis"]["legacy_api_status"] = "Success"
    
    if not super_connector_data:
        validation_report["super_connector_analysis"]["super_connector_api_status"] = "Failed"
    else:
        validation_report["super_connector_analysis"]["super_connector_api_status"] = "Success"
    
    # Generate report
    generate_validation_report(validation_report, output_file_path)
    
    return validation_report 