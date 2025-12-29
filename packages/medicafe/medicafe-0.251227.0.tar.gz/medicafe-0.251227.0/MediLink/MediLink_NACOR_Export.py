# MediLink_NACOR_Export.py
# NACOR XML Export Utility
# Exports patient data from CSV and DOCX files to NACOR XML format, grouped by year (date of service)
#
# XP / Python 3.4.4 compatible
# ASCII-only UI with progress bars
#
# Configuration (add to json/config.json):
# {
#   "CSV_FILE_PATH": "path/to/csv/file.csv",  # Existing key
#   "outputFilePath": "path/to/output",        # Existing key
#   "MediLink_Config": {
#     "local_storage_path": "path/to/docx/files",  # Existing key
#     "error_reporting": {
#       "email": {
#         "to": ["recipient@example.com"]  # Existing key
#       }
#     },
#     "nacor_export": {  # New section - only metadata
#       "vendor_id": "999ZZ99",
#       "vendor_name": "Your Vendor Name",
#       "process_name": "AQITestProcess",
#       "submitter_name": "John Doe",
#       "submitter_email": "j.doe@sample.org",
#       "contact_name": "Amanda Doe",
#       "contact_email": "a.doe@sample.org",
#       "schema_version": "2025V1.0",
#       "submission_type": "1"
#     }
#   }
# }
#
# Usage: Access via MediLink main menu -> Tools -> Export NACOR XML

from __future__ import print_function

import os
import sys
import time
from datetime import datetime
from collections import defaultdict
from xml.etree import ElementTree as ET
from xml.dom import minidom

# Ensure MediCafe module path is available
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from MediCafe.core_utils import get_shared_config_loader, extract_medilink_config
    MediLink_ConfigLoader = get_shared_config_loader()
except Exception:
    MediLink_ConfigLoader = None
    extract_medilink_config = None

try:
    from MediCafe.error_reporter import _normalize_recipients, _attempt_gmail_reauth_interactive
except Exception:
    _normalize_recipients = None
    _attempt_gmail_reauth_interactive = None

try:
    from MediBot import MediBot_Preprocessor_lib
except Exception:
    MediBot_Preprocessor_lib = None

try:
    from MediBot.MediBot_docx_decoder import parse_docx, extract_date_of_service
except Exception:
    parse_docx = None
    extract_date_of_service = None

try:
    from MediCafe.gmail_token_service import get_gmail_access_token
except Exception:
    get_gmail_access_token = None

try:
    import requests
except Exception:
    requests = None

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64


def _log(message, level="INFO"):
    """Log message using MediLink_ConfigLoader if available."""
    if MediLink_ConfigLoader and hasattr(MediLink_ConfigLoader, 'log'):
        MediLink_ConfigLoader.log(message, level=level)
    else:
        print("[{}] {}".format(level, message))


def _render_progress_bar(current, total, width=40):
    """ASCII-only progress bar text (XP / Py3.4.4 compatible)."""
    try:
        if total <= 0:
            filled = 0
        else:
            ratio = float(max(0, min(current, total))) / float(total)
            filled = int(round(width * ratio))
    except Exception:
        filled = 0
        total = max(total, 1)
    filled = max(0, min(width, filled))
    empty = width - filled
    return "[{}{}] {}/{}".format("#" * filled, "-" * empty, current, total if total > 0 else 0)


def _print_progress(current, total, message=""):
    """Render progress bar on a single console line."""
    try:
        bar = _render_progress_bar(current, total)
        if message:
            sys.stdout.write("\r{} {}".format(bar, message))
        else:
            sys.stdout.write("\r{}".format(bar))
        sys.stdout.flush()
    except Exception:
        pass


def _parse_date_string(date_str):
    """Parse date string in various formats and return datetime object."""
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_str = date_str.strip()
    if not date_str or date_str == 'MISSING':
        return None
    
    # Try common date formats
    formats = ['%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d', '%m-%d-%y', '%m/%d/%y', '%Y/%m/%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def _extract_year_from_date(date_value):
    """Extract year from date (datetime object or string)."""
    if isinstance(date_value, datetime):
        return date_value.year
    elif isinstance(date_value, str):
        parsed = _parse_date_string(date_value)
        if parsed:
            return parsed.year
    return None


def discover_available_years(config):
    """
    Discover available years and preload data structures for reuse.
    Loads CSV and scans DOCX once, returns data structures to avoid reloading.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        dict: {
            'year_counts': {year: record_count},
            'csv_data': [row, ...],  # Full CSV data
            'csv_dates_by_year': {year: [datetime, ...]},  # Surgery dates per year
            'patient_counts_per_date': {date_str: count},  # Patients per date
            'docx_dates': set of datetime,  # All DOCX dates of service
            'docx_files_scanned': int
        }
    """
    try:
        _log("Discovering available years...", level="INFO")
        print("Scanning files to discover available years...")
        
        year_counts = defaultdict(int)
        csv_data = []
        csv_dates_by_year = defaultdict(list)
        patient_counts_per_date = defaultdict(int)
        docx_dates = set()
        docx_files_scanned = 0
        
        # Extract paths from config
        csv_path = config.get('CSV_FILE_PATH', '')
        if not csv_path:
            return {
                'year_counts': {},
                'csv_data': [],
                'csv_dates_by_year': {},
                'patient_counts_per_date': {},
                'docx_dates': set(),
                'docx_files_scanned': 0
            }
        
        if extract_medilink_config:
            medi = extract_medilink_config(config)
        else:
            medi = config.get('MediLink_Config', {})
        
        docx_dir = medi.get('local_storage_path', '')
        
        # Load CSV and extract dates
        if csv_path and os.path.exists(csv_path):
            try:
                if not MediBot_Preprocessor_lib:
                    _log("MediBot_Preprocessor_lib not available", level="WARNING")
                    return {
                        'year_counts': {},
                        'csv_data': [],
                        'csv_dates_by_year': {},
                        'patient_counts_per_date': {},
                        'docx_dates': set(),
                        'docx_files_scanned': 0
                    }
                
                csv_data = MediBot_Preprocessor_lib.load_csv_data(csv_path)
                total_rows = len(csv_data)
                
                # Collect all surgery dates from CSV for DOCX filtering
                all_csv_surgery_dates = set()
                
                for idx, row in enumerate(csv_data):
                    if (idx + 1) % 500 == 0:
                        _print_progress(idx + 1, total_rows, "Scanning CSV")
                    
                    # Extract surgery date
                    surgery_date = row.get('Surgery Date', '') or row.get('Service Date', '') or row.get('Date of Service', '') or row.get('DOS', '')
                    if not surgery_date:
                        continue
                    
                    # Parse date
                    date_obj = _parse_date_string(surgery_date)
                    if date_obj:
                        year_counts[date_obj.year] += 1
                        csv_dates_by_year[date_obj.year].append(date_obj)
                        all_csv_surgery_dates.add(date_obj)
                        
                        # Count patients per date
                        date_str = date_obj.strftime('%m-%d-%Y')
                        patient_counts_per_date[date_str] += 1
                
                if total_rows > 0:
                    _print_progress(total_rows, total_rows, "CSV scan complete")
                    print()  # New line after progress bar
            except Exception as e:
                _log("Error scanning CSV for years: {}".format(e), level="WARNING")
                csv_data = []
        
        # Scan DOCX files and extract dates of service
        if docx_dir and os.path.exists(docx_dir):
            try:
                if parse_docx and extract_date_of_service:
                    docx_files = [f for f in os.listdir(docx_dir) if f.lower().endswith('.docx')]
                    total_files = len(docx_files)
                    docx_files_scanned = total_files
                    
                    for idx, docx_file in enumerate(docx_files):
                        if (idx + 1) % 10 == 0:
                            _print_progress(idx + 1, total_files, "Scanning DOCX")
                        
                        docx_path = os.path.join(docx_dir, docx_file)
                        try:
                            # Extract date of service from DOCX file
                            dos_str = extract_date_of_service(docx_path)
                            if dos_str:
                                try:
                                    dos_date = datetime.strptime(dos_str, '%m-%d-%Y')
                                    docx_dates.add(dos_date)
                                    # Only count DOCX records in year_counts if they have matching CSV surgery dates
                                    # This ensures discovery count matches what will actually be exported
                                    if dos_date in all_csv_surgery_dates:
                                        year_counts[dos_date.year] += 1
                                except ValueError:
                                    _log("Error parsing DOCX date '{}' from file {}".format(dos_str, docx_file), level="WARNING")
                                    continue
                        except Exception as e:
                            _log("Error extracting date from DOCX file {}: {}".format(docx_file, e), level="WARNING")
                            continue
                    
                    if total_files > 0:
                        _print_progress(total_files, total_files, "DOCX scan complete")
                        print()  # New line after progress bar
                else:
                    _log("DOCX parser or date extractor not available", level="WARNING")
            except Exception as e:
                _log("Error scanning DOCX for years: {}".format(e), level="WARNING")
        else:
            _log("DOCX directory not configured or not found", level="INFO")
        
        _log("Discovered {} year(s) with data".format(len(year_counts)), level="INFO")
        _log("Year breakdown: {}".format({y: c for y, c in sorted(year_counts.items())}), level="DEBUG")
        
        # Convert defaultdicts to regular dicts and sort dates
        csv_dates_by_year_clean = {}
        for year, dates in csv_dates_by_year.items():
            csv_dates_by_year_clean[year] = sorted(set(dates))
        
        return {
            'year_counts': dict(year_counts),
            'csv_data': csv_data,
            'csv_dates_by_year': csv_dates_by_year_clean,
            'patient_counts_per_date': dict(patient_counts_per_date),
            'docx_dates': docx_dates,
            'docx_files_scanned': docx_files_scanned
        }
    except Exception as e:
        _log("Error discovering years: {}".format(e), level="ERROR")
        return {
            'year_counts': {},
            'csv_data': [],
            'csv_dates_by_year': {},
            'patient_counts_per_date': {},
            'docx_dates': set(),
            'docx_files_scanned': 0
        }


def check_missing_docx_files(preloaded_data, selected_years=None):
    """
    Check for surgery dates in CSV that don't have matching DOCX files.
    Uses preloaded data - no file I/O, pure computation.
    
    Args:
        preloaded_data: Dict from discover_available_years()
        selected_years: Optional list of years to check (None = all years)
    
    Returns:
        dict: {
            'missing_dates': [datetime, ...],  # Sorted list
            'missing_by_year': {year: [datetime, ...]},  # Grouped by year
            'missing_patient_counts': {date_str: count},  # Patients per missing date
            'missing_count': int,
            'total_csv_dates': int,
            'total_docx_dates': int
        }
    """
    try:
        if not preloaded_data:
            return {
                'missing_dates': [],
                'missing_by_year': {},
                'missing_patient_counts': {},
                'missing_count': 0,
                'total_csv_dates': 0,
                'total_docx_dates': 0
            }
        
        csv_dates_by_year = preloaded_data.get('csv_dates_by_year', {})
        patient_counts_per_date = preloaded_data.get('patient_counts_per_date', {})
        docx_dates = preloaded_data.get('docx_dates', set())
        
        # Filter by selected_years if specified
        if selected_years is not None:
            csv_dates_by_year = {year: dates for year, dates in csv_dates_by_year.items() if year in selected_years}
        
        # Collect all CSV surgery dates
        all_csv_dates = set()
        for year, dates in csv_dates_by_year.items():
            all_csv_dates.update(dates)
        
        # Find missing dates (in CSV but not in DOCX)
        missing_dates = sorted(all_csv_dates - docx_dates)
        
        # Group missing dates by year
        missing_by_year = defaultdict(list)
        missing_patient_counts = {}
        
        for missing_date in missing_dates:
            year = missing_date.year
            missing_by_year[year].append(missing_date)
            
            # Get patient count for this date
            date_str = missing_date.strftime('%m-%d-%Y')
            missing_patient_counts[date_str] = patient_counts_per_date.get(date_str, 0)
        
        # Sort dates within each year
        for year in missing_by_year:
            missing_by_year[year].sort()
        
        return {
            'missing_dates': missing_dates,
            'missing_by_year': dict(missing_by_year),
            'missing_patient_counts': missing_patient_counts,
            'missing_count': len(missing_dates),
            'total_csv_dates': len(all_csv_dates),
            'total_docx_dates': len(docx_dates)
        }
    except Exception as e:
        _log("Error checking missing DOCX files: {}".format(e), level="ERROR")
        return {
            'missing_dates': [],
            'missing_by_year': {},
            'missing_patient_counts': {},
            'missing_count': 0,
            'total_csv_dates': 0,
            'total_docx_dates': 0
        }


def format_missing_docx_report(missing_data):
    """
    Format missing DOCX files report for display.
    
    Args:
        missing_data: Dict from check_missing_docx_files()
    
    Returns:
        str: Formatted report string
    """
    if not missing_data or missing_data.get('missing_count', 0) == 0:
        return "\nQA Check: Missing DOCX Files\n" + "-" * 60 + "\nAll surgery dates have matching DOCX files.\n"
    
    missing_count = missing_data.get('missing_count', 0)
    missing_by_year = missing_data.get('missing_by_year', {})
    missing_patient_counts = missing_data.get('missing_patient_counts', {})
    
    lines = []
    lines.append("\nQA Check: Missing DOCX Files")
    lines.append("-" * 60)
    lines.append("Found {} surgery date(s) in CSV without matching DOCX files:".format(missing_count))
    lines.append("")
    
    for year in sorted(missing_by_year.keys()):
        dates = missing_by_year[year]
        lines.append("Year {}:".format(year))
        for date in dates:
            date_str = date.strftime('%m-%d-%Y')
            patient_count = missing_patient_counts.get(date_str, 0)
            lines.append("  - {} ({:,} patient{})".format(date_str, patient_count, 's' if patient_count != 1 else ''))
        lines.append("")
    
    lines.append("Note: Export will proceed with CSV data only for these dates.")
    lines.append("-" * 60)
    
    return "\n".join(lines)


def format_year_selection_menu(available_years):
    """
    Format the year selection menu display.
    
    Args:
        available_years: dict {year: record_count}
    
    Returns:
        str: Formatted menu string
    """
    if not available_years:
        return "No years found with data."
    
    sorted_years = sorted(available_years.keys())
    total_records = sum(available_years.values())
    
    lines = []
    lines.append("\nAvailable Years:")
    for year in sorted_years:
        count = available_years[year]
        lines.append("  {}: {:,} records".format(year, count))
    lines.append("  Total: {:,} records".format(total_records))
    lines.append("")
    lines.append("Export Options:")
    lines.append("1. Export all years ({:,} total records)".format(total_records))
    lines.append("2. Export specific year(s)")
    lines.append("3. Cancel")
    
    return "\n".join(lines)


def get_year_selection(available_years):
    """
    Get year selection from user.
    
    Args:
        available_years: dict {year: record_count}
    
    Returns:
        list: Selected years, or None for all years, or empty list for cancel
    """
    if not available_years:
        return []
    
    sorted_years = sorted(available_years.keys())
    
    # Get initial choice
    choice = input("Enter your choice: ").strip()
    
    if choice == '1':
        return None  # All years
    elif choice == '3':
        return []  # Cancel
    elif choice == '2':
        # Show numbered list of years
        print("\nSelect years to export (comma-separated, e.g., 1,3):")
        for idx, year in enumerate(sorted_years, 1):
            count = available_years[year]
            print("{}. {} ({:,} records)".format(idx, year, count))
        
        selection_input = input("\n> ").strip()
        if not selection_input:
            return []
        
        # Parse comma-separated selections
        selected_indices = []
        for part in selection_input.split(','):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1  # Convert to 0-based
                if 0 <= idx < len(sorted_years):
                    selected_indices.append(idx)
        
        if not selected_indices:
            print("No valid selections. Cancelling.")
            return []
        
        # Convert indices to years
        selected_years = [sorted_years[idx] for idx in selected_indices]
        return selected_years
    else:
        print("Invalid choice. Cancelling.")
        return []


def format_export_summary(selected_years, year_counts, config):
    """
    Format pre-export confirmation summary.
    
    Args:
        selected_years: List of selected years, or None for all
        year_counts: dict {year: record_count}
        config: Configuration dictionary
    
    Returns:
        str: Formatted summary string
    """
    lines = []
    lines.append("\nExport Summary:")
    lines.append("-" * 60)
    
    if selected_years is None:
        # All years
        sorted_years = sorted(year_counts.keys())
        total = sum(year_counts.values())
        for year in sorted_years:
            count = year_counts[year]
            lines.append("- Year {}: {:,} records".format(year, count))
        lines.append("Total: {:,} records".format(total))
    else:
        # Specific years
        total = 0
        for year in sorted(selected_years):
            count = year_counts.get(year, 0)
            lines.append("- Year {}: {:,} records".format(year, count))
            total += count
        lines.append("Total: {:,} records".format(total))
    
    lines.append("")
    
    # Output directory
    output_path = config.get('outputFilePath', '')
    if output_path:
        lines.append("Output directory: {}".format(output_path))
    else:
        lines.append("Output directory: Not configured (files will not be saved)")
    
    # Email recipients
    email_config = config.get('MediLink_Config', {}).get('error_reporting', {}).get('email', {})
    recipients_raw = email_config.get('to', [])
    
    if _normalize_recipients:
        recipients = _normalize_recipients(recipients_raw)
    else:
        if isinstance(recipients_raw, str):
            recipients = [r.strip() for r in recipients_raw.replace(';', ',').split(',') if r.strip()]
        elif isinstance(recipients_raw, list):
            recipients = [str(r).strip() for r in recipients_raw if r]
        else:
            recipients = []
    
    if recipients:
        lines.append("Email recipients: {}".format(', '.join(recipients)))
    else:
        lines.append("Email recipients: Not configured")
    
    lines.append("-" * 60)
    
    return "\n".join(lines)


def collect_patient_data_by_year(config, target_year=None, preloaded_data=None):
    """
    Collect patient data from CSV and DOCX files, grouped by year.
    Processes ALL files first, then filters by year.
    Reuses preloaded_data if provided to avoid reloading files.
    
    Args:
        config: Configuration dictionary
        target_year: Optional year to filter (None = all years)
        preloaded_data: Optional dict from discover_available_years() to avoid reloading
    
    Returns:
        dict: {year: [patient_records]} where each record contains CSV and DOCX data
    """
    try:
        _log("Starting data collection from CSV and DOCX files", level="INFO")
        print("Collecting patient data...")
        
        # Use preloaded CSV data if available, otherwise load fresh
        if preloaded_data and preloaded_data.get('csv_data'):
            csv_data = preloaded_data['csv_data']
            _log("Reusing preloaded CSV data ({} records)".format(len(csv_data)), level="INFO")
            print("Using preloaded CSV data ({} records)...".format(len(csv_data)))
        else:
            # Extract paths from config
            csv_path = config.get('CSV_FILE_PATH', '')
            if not csv_path:
                _log("CSV_FILE_PATH not configured", level="ERROR")
                print("Error: CSV_FILE_PATH not configured in config.json")
                return {}
            
            # Load ALL CSV data (no filtering yet)
            csv_data = []
            if csv_path and os.path.exists(csv_path):
                try:
                    if not MediBot_Preprocessor_lib:
                        _log("MediBot_Preprocessor_lib not available", level="ERROR")
                        print("Error: CSV loading module not available.")
                        return {}
                    
                    print("Loading CSV data from: {}".format(csv_path))
                    csv_data = MediBot_Preprocessor_lib.load_csv_data(csv_path)
                    _log("Loaded {} CSV records".format(len(csv_data)), level="INFO")
                except Exception as e:
                    _log("Error loading CSV: {}".format(e), level="ERROR")
                    print("Error loading CSV file: {}".format(e))
                    return {}
            else:
                _log("CSV file not found: {}".format(csv_path), level="WARNING")
                print("Warning: CSV file not found. Continuing with DOCX data only.")
        
        # Get DOCX directory from config
        if extract_medilink_config:
            medi = extract_medilink_config(config)
        else:
            medi = config.get('MediLink_Config', {})
        
        docx_dir = medi.get('local_storage_path', '')
        if not docx_dir:
            _log("local_storage_path not configured", level="WARNING")
            print("Warning: local_storage_path not configured. Continuing with CSV data only.")
        
        # Process ALL CSV rows (no year filtering yet)
        print("Processing CSV records...")
        all_csv_records = []
        
        for idx, row in enumerate(csv_data):
            if (idx + 1) % 100 == 0:
                _print_progress(idx + 1, len(csv_data), "Processing CSV records")
            
            # Extract surgery date
            surgery_date = row.get('Surgery Date', '') or row.get('Service Date', '') or row.get('Date of Service', '') or row.get('DOS', '')
            if not surgery_date:
                continue
            
            # Parse date
            date_obj = _parse_date_string(surgery_date)
            if not date_obj:
                continue
            
            # Store CSV row with parsed date (no year filtering yet)
            all_csv_records.append({
                'csv_row': row,
                'surgery_date': date_obj,
                'patient_id': row.get('Patient ID #2', '') or row.get('Patient ID', ''),
                'dob': row.get('Patient DOB', '') or row.get('DOB', '')
            })
        
        if csv_data:
            _print_progress(len(csv_data), len(csv_data), "CSV processing complete")
            print()  # New line after progress bar
        
        # Load DOCX data
        docx_data_by_patient = {}
        if docx_dir and os.path.exists(docx_dir):
            try:
                if not parse_docx:
                    _log("DOCX parser not available", level="WARNING")
                    print("Warning: DOCX parser not available. Skipping DOCX files.")
                else:
                    print("Scanning DOCX files in: {}".format(docx_dir))
                    docx_files = [f for f in os.listdir(docx_dir) if f.lower().endswith('.docx')]
                    _log("Found {} DOCX files".format(len(docx_files)), level="INFO")
                    _log("Processing DOCX files from directory: {}".format(docx_dir), level="DEBUG")
                    
                    # Collect all surgery dates from CSV for DOCX filtering (as datetime objects)
                    all_surgery_dates = set()
                    for record in all_csv_records:
                        if record.get('surgery_date'):
                            all_surgery_dates.add(record['surgery_date'])
                    
                    # Process ALL DOCX files (no year filtering yet)
                    for idx, docx_file in enumerate(docx_files):
                        if (idx + 1) % 10 == 0:
                            _print_progress(idx + 1, len(docx_files), "Processing DOCX files")
                        
                        docx_path = os.path.join(docx_dir, docx_file)
                        try:
                            # Parse DOCX file (parse_docx expects set of datetime objects)
                            patient_data = parse_docx(docx_path, all_surgery_dates, capture_schedule_positions=False)
                        
                            # Merge DOCX data into structure (no year filtering yet)
                            # patient_data is OrderedDict: {patient_id: {date_str: [diagnosis, eye, femto]}}
                            for patient_id, dates_dict in patient_data.items():
                                if not patient_id:
                                    continue
                                
                                if patient_id not in docx_data_by_patient:
                                    docx_data_by_patient[patient_id] = {}
                                
                                for date_key, docx_info in dates_dict.items():
                                    # date_key is in MM-DD-YYYY format (string)
                                    try:
                                        docx_date = datetime.strptime(date_key, '%m-%d-%Y')
                                        docx_year = docx_date.year
                                        
                                        if docx_year not in docx_data_by_patient[patient_id]:
                                            docx_data_by_patient[patient_id][docx_year] = []
                                        
                                        # docx_info is a list: [diagnosis_code, left_or_right_eye, femto_yes_or_no]
                                        docx_data_by_patient[patient_id][docx_year].append({
                                            'date': docx_date,
                                            'diagnosis_code': docx_info[0] if len(docx_info) > 0 else '',
                                            'left_or_right_eye': docx_info[1] if len(docx_info) > 1 else '',
                                            'femto_yes_or_no': docx_info[2] if len(docx_info) > 2 else ''
                                        })
                                    except ValueError as e:
                                        _log("Error parsing DOCX date '{}' for patient {}: {}".format(date_key, patient_id, e), level="WARNING")
                                        continue
                                    except Exception as e:
                                        _log("Unexpected error processing DOCX data for patient {}: {}".format(patient_id, e), level="WARNING")
                                        continue
                        except Exception as e:
                            _log("Error processing DOCX file {}: {}".format(docx_file, e), level="WARNING")
                            continue
                    
                    if docx_files:
                        _print_progress(len(docx_files), len(docx_files), "DOCX processing complete")
                        print()  # New line after progress bar
            except Exception as e:
                _log("Error processing DOCX directory: {}".format(e), level="ERROR")
                print("Error processing DOCX directory: {}".format(e))
        
        # Group CSV records by year (after processing all)
        print("Grouping data by year...")
        csv_records_by_year = defaultdict(list)
        
        for record in all_csv_records:
            year = record['surgery_date'].year
            csv_records_by_year[year].append(record)
        
        # Merge CSV and DOCX data by year, then filter by target_year if specified
        all_years = set(csv_records_by_year.keys())
        for patient_id, year_data in docx_data_by_patient.items():
            all_years.update(year_data.keys())
        
        data_by_year = defaultdict(list)
        for year in all_years:
            # Filter by target_year if specified
            if target_year is not None and year != target_year:
                continue
            
            year_records = []
            
            # Add CSV records for this year
            for csv_record in csv_records_by_year.get(year, []):
                patient_id = csv_record['patient_id']
                
                # Find matching DOCX data
                docx_data = None
                if patient_id in docx_data_by_patient and year in docx_data_by_patient[patient_id]:
                    docx_data = docx_data_by_patient[patient_id][year]
                
                year_records.append({
                    'year': year,
                    'csv_row': csv_record['csv_row'],
                    'surgery_date': csv_record['surgery_date'],
                    'patient_id': patient_id,
                    'dob': csv_record['dob'],
                    'docx_data': docx_data
                })
            
            if year_records:
                data_by_year[year] = year_records
        
        _log("Data collection complete. Found records for years: {}".format(sorted(data_by_year.keys())), level="INFO")
        total_records_collected = sum(len(records) for records in data_by_year.values())
        _log("Total records collected: {} across {} year(s)".format(total_records_collected, len(data_by_year)), level="DEBUG")
        print("Data collection complete. Found {} year(s) of data.".format(len(data_by_year)))
        
        return dict(data_by_year)
    except Exception as e:
        _log("Critical error in collect_patient_data_by_year: {}".format(e), level="ERROR")
        print("Critical error during data collection: {}".format(e))
        import traceback
        _log("Traceback: {}".format(traceback.format_exc()), level="ERROR")
        return {}


def map_to_nacor_structure(patient_record, vendor_id="999ZZ99", vendor_name="AQI Sample Vendor"):
    """
    Map patient record (CSV + DOCX) to NACOR XML structure.
    
    Args:
        patient_record: dict with 'csv_row', 'surgery_date', 'patient_id', 'dob', 'docx_data'
        vendor_id: Vendor ID for NACOR submission
        vendor_name: Vendor name for NACOR submission
    
    Returns:
        dict: Structured data matching NACOR XML schema
    """
    try:
        if not patient_record:
            _log("Empty patient record provided to map_to_nacor_structure", level="WARNING")
            return None
        
        csv_row = patient_record.get('csv_row', {})
        surgery_date = patient_record.get('surgery_date')
        patient_id = patient_record.get('patient_id', '')
        dob = patient_record.get('dob', '')
        docx_data = patient_record.get('docx_data')
        
        # Extract patient name
        patient_name = csv_row.get('Patient Name', '') or csv_row.get('Name', '')
        if not patient_name:
            # Try to construct from first/last name fields
            first_name = csv_row.get('First Name', '') or csv_row.get('Patient First Name', '')
            last_name = csv_row.get('Last Name', '') or csv_row.get('Patient Last Name', '')
            if first_name or last_name:
                patient_name = "{} {}".format(first_name, last_name).strip()
        
        # Parse DOB
        dob_date = None
        if dob:
            dob_date = _parse_date_string(dob)
        
        # Extract gender
        gender = csv_row.get('Gender', '') or csv_row.get('Sex', '')
        gender_code = ''
        if gender:
            gender_upper = gender.upper()
            if 'MALE' in gender_upper or gender_upper == 'M':
                gender_code = 'Male'
            elif 'FEMALE' in gender_upper or gender_upper == 'F':
                gender_code = 'Female'
        
        # Extract race/ethnicity
        race = csv_row.get('Race', '') or csv_row.get('Ethnicity', '')
        
        # Extract procedure information
        cpt_code = csv_row.get('CPT Code', '') or csv_row.get('Procedure Code', '')
        procedure_description = csv_row.get('Procedure Description', '') or csv_row.get('Description', '')
        
        # Extract facility/location
        facility_id = csv_row.get('Facility ID', '') or csv_row.get('Facility', '')
        location_type = csv_row.get('Location Type', '') or csv_row.get('Place of Service', '')
        
        # Extract insurance information
        payer_id = csv_row.get('Ins1 Payer ID', '') or csv_row.get('Payer ID', '')
        member_id = csv_row.get('Ins1 Member ID', '') or csv_row.get('Primary Policy Number', '') or csv_row.get('Member ID', '')
        
        # Format dates for XML (ISO 8601 format: YYYY-MM-DDTHH:MM:SS)
        surgery_date_str = ''
        if surgery_date:
            surgery_date_str = surgery_date.strftime('%Y-%m-%dT%H:%M:%S')
        
        dob_str = ''
        if dob_date:
            dob_str = dob_date.strftime('%Y-%m-%d')
        
        # Build NACOR structure
        nacor_data = {
            'Patient': {
                'PatientID': patient_id or '',
                'BirthDate': dob_str,
                'Name': patient_name or '',
                'Gender': gender_code,
                'Race': race or ''
            },
            'Procedure': {
                'ProcedureID': csv_row.get('Procedure ID', '') or patient_id,
                'FacilityID': facility_id or '',
                'DateOfService': surgery_date_str,
                'CPTCode': cpt_code or '',
                'CPTDescription': procedure_description or '',
                'LocationType': location_type or ''
            },
            'Insurance': {
                'PayerID': payer_id or '',
                'MemberID': member_id or ''
            }
        }
        
        # Add DOCX data if available (anesthesia details)
        if docx_data and isinstance(docx_data, list) and len(docx_data) > 0:
            # Use first DOCX entry for this date
            docx_entry = docx_data[0] if isinstance(docx_data[0], dict) else {}
            nacor_data['Anesthesia'] = {
                'DiagnosisCode': docx_entry.get('diagnosis_code', ''),
                'Eye': docx_entry.get('left_or_right_eye', ''),
                'Femto': docx_entry.get('femto_yes_or_no', '')
            }
        
        # Add vendor information
        nacor_data['Vendor'] = {
            'VendorID': vendor_id or '999ZZ99',
            'VendorName': vendor_name or 'AQI Sample Vendor'
        }
        
        return nacor_data
    except Exception as e:
        _log("Error mapping patient record to NACOR structure: {}".format(e), level="ERROR")
        return None


def generate_nacor_xml(patient_records, year, submission_info=None):
    """
    Generate NACOR XML from patient records.
    
    Args:
        patient_records: List of mapped patient records (from map_to_nacor_structure)
        year: Year for this export
        submission_info: Optional dict with submission metadata (process_name, submitter_name, etc.)
    
    Returns:
        str: XML string
    """
    _log("generate_nacor_xml called for year {} with {} records".format(year, len(patient_records) if patient_records else 0), level="DEBUG")
    try:
        if not patient_records:
            _log("No patient records provided to generate_nacor_xml", level="WARNING")
            return None
        
        if submission_info is None:
            submission_info = {
                'process_name': 'AQITestProcess',
                'submitter_name': 'John Doe',
                'submitter_email': 'j.doe@sample.org',
                'contact_name': 'Amanda Doe',
                'contact_email': 'a.doe@sample.org',
                'schema_version': '2025V1.0',
                'vendor_id': '999ZZ99',
                'submission_type': '1'  # 1=Billing, 2=Quality/Outcomes, 3=AIMS only, 4=EMR/EHR
            }
        
        # Create root element
        root = ET.Element('NACORSubmission')
        
        # Add submission header
        header = ET.SubElement(root, 'SubmissionHeader')
        ET.SubElement(header, 'ProcessName').text = submission_info.get('process_name', 'AQITestProcess')
        ET.SubElement(header, 'SubmitterName').text = submission_info.get('submitter_name', '')
        ET.SubElement(header, 'SubmitterEmail').text = submission_info.get('submitter_email', '')
        ET.SubElement(header, 'ContactName').text = submission_info.get('contact_name', '')
        ET.SubElement(header, 'ContactEmail').text = submission_info.get('contact_email', '')
        ET.SubElement(header, 'SchemaVersion').text = submission_info.get('schema_version', '2025V1.0')
        ET.SubElement(header, 'VendorID').text = submission_info.get('vendor_id', '999ZZ99')
        ET.SubElement(header, 'SubmissionType').text = submission_info.get('submission_type', '1')
        ET.SubElement(header, 'SubmissionDate').text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        # Add patient records
        patients_elem = ET.SubElement(root, 'Patients')
        _log("Building XML structure for {} patient records".format(len(patient_records)), level="DEBUG")
        
        for record in patient_records:
            patient_elem = ET.SubElement(patients_elem, 'Patient')
            
            # Patient demographics
            patient_data = record.get('Patient', {})
            if patient_data:
                ET.SubElement(patient_elem, 'PatientID').text = str(patient_data.get('PatientID', ''))
                if patient_data.get('BirthDate'):
                    ET.SubElement(patient_elem, 'BirthDate').text = patient_data.get('BirthDate', '')
                if patient_data.get('Name'):
                    ET.SubElement(patient_elem, 'Name').text = patient_data.get('Name', '')
                if patient_data.get('Gender'):
                    ET.SubElement(patient_elem, 'Gender').text = patient_data.get('Gender', '')
                if patient_data.get('Race'):
                    ET.SubElement(patient_elem, 'Race').text = patient_data.get('Race', '')
            
            # Procedure information
            procedure_data = record.get('Procedure', {})
            if procedure_data:
                procedure_elem = ET.SubElement(patient_elem, 'Procedure')
                if procedure_data.get('ProcedureID'):
                    ET.SubElement(procedure_elem, 'ProcedureID').text = str(procedure_data.get('ProcedureID', ''))
                if procedure_data.get('FacilityID'):
                    ET.SubElement(procedure_elem, 'FacilityID').text = str(procedure_data.get('FacilityID', ''))
                if procedure_data.get('DateOfService'):
                    ET.SubElement(procedure_elem, 'DateOfService').text = procedure_data.get('DateOfService', '')
                if procedure_data.get('CPTCode'):
                    ET.SubElement(procedure_elem, 'CPTCode').text = procedure_data.get('CPTCode', '')
                if procedure_data.get('CPTDescription'):
                    ET.SubElement(procedure_elem, 'CPTDescription').text = procedure_data.get('CPTDescription', '')
                if procedure_data.get('LocationType'):
                    ET.SubElement(procedure_elem, 'LocationType').text = str(procedure_data.get('LocationType', ''))
            
            # Insurance information
            insurance_data = record.get('Insurance', {})
            if insurance_data:
                insurance_elem = ET.SubElement(patient_elem, 'Insurance')
                if insurance_data.get('PayerID'):
                    ET.SubElement(insurance_elem, 'PayerID').text = str(insurance_data.get('PayerID', ''))
                if insurance_data.get('MemberID'):
                    ET.SubElement(insurance_elem, 'MemberID').text = str(insurance_data.get('MemberID', ''))
            
            # Anesthesia information (from DOCX)
            anesthesia_data = record.get('Anesthesia', {})
            if anesthesia_data:
                anesthesia_elem = ET.SubElement(patient_elem, 'Anesthesia')
                if anesthesia_data.get('DiagnosisCode'):
                    ET.SubElement(anesthesia_elem, 'DiagnosisCode').text = anesthesia_data.get('DiagnosisCode', '')
                if anesthesia_data.get('Eye'):
                    ET.SubElement(anesthesia_elem, 'Eye').text = anesthesia_data.get('Eye', '')
                if anesthesia_data.get('Femto'):
                    ET.SubElement(anesthesia_elem, 'Femto').text = anesthesia_data.get('Femto', '')
        
        # Convert to string with pretty printing
        try:
            # Python 3.4.4 compatible XML formatting
            rough_string = ET.tostring(root, encoding='unicode')
            # Use minidom for pretty printing
            reparsed = minidom.parseString(rough_string.encode('utf-8'))
            return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
        except Exception as e:
            _log("Error formatting XML: {}".format(e), level="WARNING")
            # Fallback to basic string representation
            return ET.tostring(root, encoding='unicode')
    except Exception as e:
        _log("Error generating NACOR XML: {}".format(e), level="ERROR")
        import traceback
        _log("Traceback: {}".format(traceback.format_exc()), level="ERROR")
        return None


def export_nacor_xml(year, xml_content, config, output_path=None):
    """
    Export NACOR XML to file and email.
    Always attempts to email using error_reporting.email.to recipients.
    
    Args:
        year: Year for this export
        xml_content: XML string content
        config: Configuration dictionary
        output_path: Optional directory path to save XML file (defaults to outputFilePath from config)
    
    Returns:
        tuple: (success: bool, file_path: str or None, email_sent: bool)
    """
    _log("export_nacor_xml called for year {}, XML size: {} bytes".format(year, len(xml_content) if xml_content else 0), level="DEBUG")
    file_path = None
    email_sent = False
    
    # Get output path from config if not provided
    if not output_path:
        output_path = config.get('outputFilePath', '')
        _log("Using outputFilePath from config: {}".format(output_path if output_path else "Not configured"), level="DEBUG")
    
    # Save to file if output_path provided
    if output_path:
        try:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
                _log("Created output directory: {}".format(output_path), level="INFO")
            
            filename = "NACOR_Export_{}.xml".format(year)
            file_path = os.path.join(output_path, filename)
            
            # Write XML file with UTF-8 encoding
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            _log("XML file saved: {}".format(file_path), level="INFO")
            print("XML file saved: {}".format(file_path))
        except Exception as e:
            _log("Error saving XML file: {}".format(e), level="ERROR")
            print("Error saving XML file: {}".format(e))
            return False, None, False
    
    # Always attempt to send email
    email_config = config.get('MediLink_Config', {}).get('error_reporting', {}).get('email', {})
    recipients_raw = email_config.get('to', [])
    
    # Normalize recipients
    if _normalize_recipients:
        recipients = _normalize_recipients(recipients_raw)
    else:
        # Fallback normalization
        if isinstance(recipients_raw, str):
            recipients = [r.strip() for r in recipients_raw.replace(';', ',').split(',') if r.strip()]
        elif isinstance(recipients_raw, list):
            recipients = [str(r).strip() for r in recipients_raw if r]
        else:
            recipients = []
    
    if not recipients:
        _log("No valid email recipients configured in error_reporting.email.to", level="WARNING")
        print("Warning: No valid email recipients configured. Set 'MediLink_Config.error_reporting.email.to' in config.json")
    else:
        # Check if TestMode is enabled
        medi_config = config.get('MediLink_Config', {})
        test_mode = medi_config.get('TestMode', False)
        
        if test_mode:
            _log("TestMode is enabled - email sending skipped for NACOR export", level="INFO")
            print("Note: TestMode is enabled. Email sending is skipped in test mode.")
            print("      XML export completed successfully (file saved if outputFilePath configured).")
        else:
            try:
                # Get Gmail access token
                access_token = None
                if get_gmail_access_token:
                    try:
                        access_token = get_gmail_access_token()
                    except Exception as e:
                        _log("Error getting Gmail access token: {}".format(e), level="WARNING")
                        access_token = None
                
                # If no token, attempt interactive re-authentication
                if not access_token:
                    _log("No access token - attempting Gmail re-authorization.", level="INFO")
                    print("No Gmail token found. Starting re-authorization...")
                    
                    if _attempt_gmail_reauth_interactive:
                        _log("Initiating interactive Gmail re-authorization", level="DEBUG")
                        try:
                            reauth_result = _attempt_gmail_reauth_interactive()
                            _log("Gmail re-authorization result: {}".format(reauth_result), level="DEBUG")
                            
                            if reauth_result:
                                # Retry getting token after successful auth
                                try:
                                    access_token = get_gmail_access_token()
                                    _log("Access token obtained after re-authorization", level="INFO" if access_token else "WARNING")
                                except Exception as e:
                                    _log("Error getting Gmail access token after re-auth: {}".format(e), level="WARNING")
                                    access_token = None
                        except Exception as e:
                            _log("Error during Gmail re-authorization: {}".format(e), level="ERROR")
                    else:
                        _log("Gmail re-authentication function not available (import failed)", level="WARNING")
                        print("Warning: Gmail authentication module not available. Cannot attempt interactive re-authorization.")
                    
                    if not access_token:
                        # Only show "incomplete" message if we actually attempted auth
                        if _attempt_gmail_reauth_interactive:
                            _log("Gmail access token not available after re-authentication attempt", level="WARNING")
                            print("Authentication incomplete. Please finish Gmail consent, then retry.")
                        print("      XML export completed successfully (file saved if outputFilePath configured).")
                
                if access_token:
                    # Build email message
                    _log("Building email message for year {} to {} recipient(s)".format(year, len(recipients)), level="DEBUG")
                    msg = MIMEMultipart()
                    msg['To'] = ', '.join(recipients)
                    msg['Subject'] = 'NACOR XML Export - {}'.format(year)
                    
                    # Attach XML file
                    if file_path and os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        _log("Attaching XML file from disk: {} ({} bytes)".format(file_path, file_size), level="DEBUG")
                        with open(file_path, 'rb') as f:
                            attach = MIMEApplication(f.read(), _subtype='xml')
                            attach.add_header('Content-Disposition', 'attachment', 
                                            filename=os.path.basename(file_path))
                            msg.attach(attach)
                    else:
                        # Attach XML content directly
                        xml_bytes = xml_content.encode('utf-8')
                        _log("Attaching XML content directly: {} bytes".format(len(xml_bytes)), level="DEBUG")
                        attach = MIMEApplication(xml_bytes, _subtype='xml')
                        attach.add_header('Content-Disposition', 'attachment', 
                                        filename='NACOR_Export_{}.xml'.format(year))
                        msg.attach(attach)
                    
                    # Email body
                    body = "NACOR XML export for year {} is attached.\n\n".format(year)
                    body += "Generated: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    msg.attach(MIMEText(body, 'plain'))
                    
                    # Send via Gmail API
                    if requests:
                        _log("Sending email via Gmail API", level="DEBUG")
                        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                        headers = {'Authorization': 'Bearer {}'.format(access_token), 
                                 'Content-Type': 'application/json'}
                        data = {'raw': raw}
                        
                        resp = requests.post('https://gmail.googleapis.com/gmail/v1/users/me/messages/send', 
                                           headers=headers, json=data)
                        
                        _log("Gmail API response: status_code={}".format(resp.status_code), level="DEBUG")
                        
                        if resp.status_code == 200:
                            email_sent = True
                            _log("NACOR XML email sent successfully to {}".format(', '.join(recipients)), level="INFO")
                            print("Email sent successfully to: {}".format(', '.join(recipients)))
                        else:
                            _log("Gmail API error: {} - {}".format(resp.status_code, resp.text), level="ERROR")
                            print("Error sending email: {} - {}".format(resp.status_code, resp.text))
                    else:
                        _log("requests module not available for email sending", level="ERROR")
                        print("Error: requests module not available for email sending.")
            except Exception as e:
                _log("Error sending email: {}".format(e), level="ERROR")
                print("Error sending email: {}".format(e))
    
    return True, file_path, email_sent


def run_nacor_export(config, target_year=None):
    """
    Main orchestration function for NACOR XML export.
    
    Args:
        config: Configuration dictionary
        target_year: Optional year to export (None = prompt user or export all)
    
    Returns:
        dict: Summary of export results
    """
    _log("NACOR export utility started", level="INFO")
    _log("Target year parameter: {}".format(target_year if target_year else "None (user will select)"), level="DEBUG")
    
    print("\n" + "="*60)
    print("NACOR XML Export Utility")
    print("="*60)
    
    # Get paths from existing config keys
    csv_path = config.get('CSV_FILE_PATH', '')
    _log("CSV file path from config: {}".format(csv_path if csv_path else "Not configured"), level="DEBUG")
    if not csv_path:
        print("Error: CSV_FILE_PATH not configured in config.json")
        return {'success': False, 'error': 'CSV_FILE_PATH not configured'}
    
    if not os.path.exists(csv_path):
        print("Error: CSV file not found: {}".format(csv_path))
        return {'success': False, 'error': 'CSV file not found'}
    
    # Get MediLink config for local_storage_path
    if extract_medilink_config:
        medi = extract_medilink_config(config)
    else:
        medi = config.get('MediLink_Config', {})
    
    docx_directory = medi.get('local_storage_path', '')
    if not docx_directory:
        print("Warning: local_storage_path not configured in MediLink_Config. Continuing with CSV data only.")
    elif not os.path.exists(docx_directory):
        print("Warning: local_storage_path directory not found: {}. Continuing with CSV data only.".format(docx_directory))
        docx_directory = None
    
    # Get output directory from existing config
    output_directory = config.get('outputFilePath', '')
    if not output_directory:
        print("Warning: outputFilePath not configured. XML files will not be saved to disk.")
    
    # Get vendor/submitter metadata from nacor_export config
    nacor_config = config.get('MediLink_Config', {}).get('nacor_export', {})
    vendor_id = nacor_config.get('vendor_id', '999ZZ99')
    vendor_name = nacor_config.get('vendor_name', 'AQI Sample Vendor')
    
    # Get submission info
    submission_info = {
        'process_name': nacor_config.get('process_name', 'AQITestProcess'),
        'submitter_name': nacor_config.get('submitter_name', 'John Doe'),
        'submitter_email': nacor_config.get('submitter_email', 'j.doe@sample.org'),
        'contact_name': nacor_config.get('contact_name', 'Amanda Doe'),
        'contact_email': nacor_config.get('contact_email', 'a.doe@sample.org'),
        'schema_version': nacor_config.get('schema_version', '2025V1.0'),
        'vendor_id': vendor_id,
        'submission_type': str(nacor_config.get('submission_type', '1'))
    }
    
    # Step 1: Discover available years (returns preloaded data)
    print("\nStep 1: Discovering available years...")
    preloaded_data = discover_available_years(config)
    
    if not preloaded_data or not preloaded_data.get('year_counts'):
        _log("No data found during year discovery", level="WARNING")
        print("No data found in CSV or DOCX files.")
        return {'success': False, 'error': 'No data found'}
    
    available_years = preloaded_data['year_counts']
    _log("Year discovery complete: {} year(s) with data".format(len(available_years)), level="INFO")
    _log("Available years: {}".format(sorted(available_years.keys())), level="DEBUG")
    
    # Step 2: Year selection
    print(format_year_selection_menu(available_years))
    selected_years = get_year_selection(available_years)
    
    if selected_years == []:
        _log("Export cancelled by user during year selection", level="INFO")
        print("Export cancelled by user.")
        return {'success': False, 'error': 'Cancelled by user'}
    
    # Determine target years for data collection
    if selected_years is None:
        # All years
        target_years = None
        years_to_process = sorted(available_years.keys())
        _log("User selected all years for export", level="INFO")
    else:
        # Specific years
        target_years = selected_years
        years_to_process = sorted(selected_years)
        _log("User selected specific years: {}".format(years_to_process), level="INFO")
    
    # Step 2.5: QA Check - Missing DOCX files
    print("\nStep 2.5: QA Check - Checking for missing DOCX files...")
    missing_docx_data = check_missing_docx_files(preloaded_data, selected_years)
    missing_count = missing_docx_data.get('missing_count', 0)
    _log("QA check complete: {} surgery dates missing DOCX files".format(missing_count), level="INFO" if missing_count > 0 else "DEBUG")
    missing_report = format_missing_docx_report(missing_docx_data)
    print(missing_report)
    
    # Step 3: Pre-export summary and confirmation
    summary = format_export_summary(selected_years, available_years, config)
    print(summary)
    
    # Always prompt to continue (regardless of missing files)
    if missing_docx_data.get('missing_count', 0) > 0:
        _log("Proceeding with export despite {} missing DOCX files".format(missing_count), level="INFO")
        print("\nNote: Some surgery dates are missing DOCX files. Export will proceed with CSV data only for those dates.")
    
    confirm = input("\nProceed with export? (Y/N): ").strip().upper()
    if confirm != 'Y':
        _log("Export cancelled by user at confirmation prompt", level="INFO")
        print("Export cancelled.")
        return {'success': False, 'error': 'Cancelled by user'}
    
    _log("Export confirmed by user, starting data processing", level="INFO")
    
    # Step 4: Collect and process data
    print("\n" + "="*60)
    print("Processing Export")
    print("="*60)
    
    # Collect data for selected years (reuse preloaded data)
    print("\nStep 1/4: Collecting patient data...")
    try:
        # Pass preloaded_data to avoid reloading files
        data_by_year = collect_patient_data_by_year(config, target_year=None, preloaded_data=preloaded_data)
        
        if not data_by_year:
            _log("No data found after collection phase", level="WARNING")
            print("No data found after collection.")
            return {'success': False, 'error': 'No data found'}
        
        # Filter to selected years if specific years were chosen
        if target_years is not None:
            _log("Filtering data to selected years: {}".format(target_years), level="DEBUG")
            data_by_year = {year: data_by_year[year] for year in target_years if year in data_by_year}
        
        if not data_by_year:
            _log("No data found for selected years after filtering", level="WARNING")
            print("No data found for selected years.")
            return {'success': False, 'error': 'No data found for selected years'}
        
        total_records = sum(len(records) for records in data_by_year.values())
        _log("Data collection complete: {} year(s), {} total records".format(len(data_by_year), total_records), level="INFO")
        _log("Years with data: {}".format(sorted(data_by_year.keys())), level="DEBUG")
        print("Found data for {} year(s): {}".format(len(data_by_year), sorted(data_by_year.keys())))
    except Exception as e:
        _log("Error collecting data: {}".format(e), level="ERROR")
        print("Error collecting data: {}".format(e))
        return {'success': False, 'error': str(e)}
    
    # Process each year
    results = {}
    total_years = len(data_by_year)
    _log("Starting export processing for {} year(s)".format(total_years), level="INFO")
    
    for year_idx, (year, patient_records) in enumerate(sorted(data_by_year.items()), 1):
        _log("Processing year {} ({}/{}) with {} records".format(year, year_idx, total_years, len(patient_records)), level="INFO")
        print("\n" + "-"*60)
        print("Processing year {} ({}/{})".format(year, year_idx, total_years))
        print("-"*60)
        
        # Map records to NACOR structure
        print("Step 2/4: Mapping data to NACOR structure...")
        mapped_records = []
        total_records = len(patient_records)
        _log("Mapping {} records to NACOR structure for year {}".format(total_records, year), level="DEBUG")
        
        for idx, record in enumerate(patient_records):
            if (idx + 1) % 100 == 0 or idx == 0:
                _print_progress(idx + 1, total_records, "Mapping records")
            
            try:
                mapped = map_to_nacor_structure(record, vendor_id, vendor_name)
                if mapped:
                    mapped_records.append(mapped)
                else:
                    _log("Record {} returned None from map_to_nacor_structure".format(idx), level="DEBUG")
            except Exception as e:
                _log("Error mapping record {}: {}".format(idx, e), level="WARNING")
                continue
        
        if mapped_records:
            _print_progress(total_records, total_records, "Mapping complete")
            print()  # New line after progress bar
        
        _log("Mapping complete for year {}: {} of {} records mapped successfully".format(year, len(mapped_records), total_records), level="INFO")
        
        if not mapped_records:
            _log("No valid mapped records for year {}, skipping".format(year), level="WARNING")
            print("Warning: No valid records to export for year {}".format(year))
            results[year] = {'success': False, 'error': 'No valid records'}
            continue
        
        # Generate XML
        print("Step 3/4: Generating XML...")
        _log("Generating XML for year {} with {} records".format(year, len(mapped_records)), level="DEBUG")
        try:
            xml_content = generate_nacor_xml(mapped_records, year, submission_info)
            if xml_content:
                xml_size = len(xml_content)
                _log("XML generated successfully for year {}: {} bytes, {} records".format(year, xml_size, len(mapped_records)), level="INFO")
                _log("XML size: {} bytes ({} KB)".format(xml_size, xml_size // 1024), level="DEBUG")
                print("XML generated successfully ({:,} records)".format(len(mapped_records)))
            else:
                _log("XML generation returned empty content for year {}".format(year), level="ERROR")
                print("Error: XML generation returned empty content")
                results[year] = {'success': False, 'error': 'XML generation failed'}
                continue
        except Exception as e:
            _log("Error generating XML for year {}: {}".format(year, e), level="ERROR")
            print("Error generating XML: {}".format(e))
            results[year] = {'success': False, 'error': str(e)}
            continue
        
        # Export XML (always attempts email)
        print("Step 4/4: Exporting XML...")
        _log("Exporting XML for year {} (file save and email)".format(year), level="INFO")
        try:
            success, file_path, email_sent = export_nacor_xml(
                year, xml_content, config, output_directory
            )
            
            if success:
                _log("Export complete for year {}: file={}, email_sent={}".format(year, file_path or "Not saved", email_sent), level="INFO")
                results[year] = {
                    'success': True,
                    'records': len(mapped_records),
                    'file_path': file_path,
                    'email_sent': email_sent
                }
                print("Export complete for year {}".format(year))
            else:
                _log("Export failed for year {}".format(year), level="ERROR")
                results[year] = {'success': False, 'error': 'Export failed'}
        except Exception as e:
            _log("Error exporting XML for year {}: {}".format(year, e), level="ERROR")
            print("Error exporting XML: {}".format(e))
            results[year] = {'success': False, 'error': str(e)}
    
    # Step 5: Final Summary
    print("\n" + "="*60)
    print("Export Summary")
    print("="*60)
    
    successful_years = [y for y, r in results.items() if r.get('success')]
    failed_years = [y for y, r in results.items() if not r.get('success')]
    
    _log("Export processing complete: {} successful, {} failed".format(len(successful_years), len(failed_years)), level="INFO")
    
    if successful_years:
        _log("Successful years: {}".format(successful_years), level="DEBUG")
        print("Successful exports: {}".format(len(successful_years)))
        total_exported = 0
        for year in sorted(successful_years):
            result = results[year]
            record_count = result.get('records', 0)
            total_exported += record_count
            print("  Year {}: {:,} records".format(year, record_count))
            if result.get('file_path'):
                print("    File: {}".format(result['file_path']))
            if result.get('email_sent'):
                print("    Email: Sent")
            elif result.get('file_path'):
                print("    Email: Failed (file saved locally)")
        print("  Total records exported: {:,}".format(total_exported))
    
    if failed_years:
        print("\nFailed exports: {}".format(len(failed_years)))
        for year in sorted(failed_years):
            result = results[year]
            print("  Year {}: {}".format(year, result.get('error', 'Unknown error')))
    
    if not successful_years and not failed_years:
        print("No exports completed.")
    
    # QA Status
    if missing_docx_data and missing_docx_data.get('missing_count', 0) > 0:
        print("\nQA Status:")
        print("  Missing DOCX files: {} surgery date(s)".format(missing_docx_data.get('missing_count', 0)))
        print("  Note: Export proceeded with CSV data only for missing dates.")
    
    print("="*60)
    
    # Final summary log
    total_exported = sum(r.get('records', 0) for r in results.values() if r.get('success'))
    _log("NACOR export utility completed: success={}, years={}/{}, records={}".format(
        len(successful_years) > 0, len(successful_years), 
        len(successful_years) + len(failed_years),
        total_exported
    ), level="INFO")
    
    return {
        'success': len(successful_years) > 0,
        'results': results,
        'total_years': total_years,
        'successful_years': len(successful_years),
        'failed_years': len(failed_years),
        'qa_status': {
            'missing_docx_count': missing_docx_data.get('missing_count', 0) if missing_docx_data else 0,
            'missing_docx_dates': missing_docx_data.get('missing_dates', []) if missing_docx_data else []
        }
    }
