# -*- coding: ascii -*-
"""
MediBot Notepad Utilities
Windows XP + Python 3.4.4 + ASCII-only compatible module for generating notepad files.

This module provides utilities to create and open text files containing patient table data
for manual review and reference.
"""

import os
import subprocess
import tempfile
from datetime import datetime


def format_patient_table_for_notepad(patient_info, title):
    """
    Format patient table data for notepad display.
    
    Args:
        patient_info: List of tuples (surgery_date, patient_name, patient_id, diagnosis_code, patient_row)
        title: Title for the table section
        
    Returns:
        str: Formatted text content suitable for notepad display
    """
    if not patient_info:
        return title + "\n\nNo patients found.\n"
    
    lines = []
    lines.append(title)
    lines.append("")
    
    # Normalize data to avoid None and unexpected container types in sort key
    normalized_info = []
    for surgery_date, patient_name, patient_id, diagnosis_code, patient_row in patient_info:
        # Normalize date into comparable key and display string
        display_date = None
        current_date_dt = None
        try:
            if hasattr(surgery_date, 'strftime'):
                display_date = surgery_date.strftime('%m-%d')
                current_date_dt = surgery_date
            elif isinstance(surgery_date, str):
                # Date strings may be MM-DD-YYYY or already MM-DD
                parts = surgery_date.split('-') if surgery_date else []
                if len(parts) == 3 and all(parts):
                    display_date = "{}-{}".format(parts[0], parts[1])
                    try:
                        current_date_dt = datetime.strptime(surgery_date, '%m-%d-%Y')
                    except Exception:
                        current_date_dt = None
                else:
                    display_date = surgery_date or 'Unknown Date'
                    current_date_dt = None
            else:
                display_date = str(surgery_date) if surgery_date is not None else 'Unknown Date'
                current_date_dt = None
        except Exception:
            display_date = str(surgery_date) if surgery_date is not None else 'Unknown Date'
            current_date_dt = None
        
        # Normalize diagnosis display: only show "-Not Found-" when explicitly flagged as N/A
        display_diagnosis = diagnosis_code
        if diagnosis_code == 'N/A':
            display_diagnosis = '-Not Found-'
        elif not diagnosis_code or diagnosis_code.strip() == '':
            display_diagnosis = '-Not Found-'
        
        # Extract patient name parts for sorting
        last_name_key = ''
        first_name_key = ''
        
        # Try to get last/first from patient_row if available
        if patient_row:
            try:
                last_name_key = str(patient_row.get('Last Name', '')).upper()
                first_name_key = str(patient_row.get('First Name', '')).upper()
            except (AttributeError, TypeError):
                pass
        
        # Build primary date for this patient (used for grouping)
        primary_date_dt = current_date_dt
        
        # If last/first not available from row, parse from display name "LAST, FIRST ..."
        if not last_name_key and isinstance(patient_name, str):
            try:
                parts = [p.strip() for p in patient_name.split(',')]
                if len(parts) >= 1:
                    last_name_key = parts[0].upper()
                if len(parts) >= 2:
                    first_name_key = parts[1].split()[0].upper() if parts[1] else ''
            except Exception:
                last_name_key = ''
                first_name_key = ''

        # Build composite sort key per requirement: by earliest date, then last name within date
        composite_sort_key = (primary_date_dt, last_name_key, first_name_key, str(patient_id or ''))
        
        normalized_info.append((composite_sort_key, display_date, str(patient_name or ''), str(patient_id or ''), display_diagnosis))
    
    # Sort so that all entries for a patient are grouped under their earliest date
    normalized_info.sort(key=lambda x: x[0])
    
    # Calculate column widths for proper alignment
    max_patient_id_len = max(len(pid) for _, _, _, pid, _ in normalized_info)
    max_patient_name_len = max(len(pname) for _, _, pname, _, _ in normalized_info)
    max_diagnosis_len = max(len(dcode) for _, _, _, _, dcode in normalized_info)
    
    # Ensure minimum widths for readability
    max_patient_id_len = max(max_patient_id_len, 10)  # "Patient ID" header
    max_patient_name_len = max(max_patient_name_len, 12)  # "Patient Name" header
    max_diagnosis_len = max(max_diagnosis_len, 9)  # "Diagnosis" header
    
    # Add table header
    header_format = "     {:<6} | {:<" + str(max_patient_id_len) + "} | {:<" + str(max_patient_name_len) + "} | {:<" + str(max_diagnosis_len) + "}"
    lines.append(header_format.format("Date", "Patient ID", "Patient Name", "Diagnosis"))
    
    # Add separator line
    separator_format = "     {:<6} | {:<" + str(max_patient_id_len) + "} | {:<" + str(max_patient_name_len) + "} | {:<" + str(max_diagnosis_len) + "}"
    lines.append(separator_format.format("-" * 6, "-" * max_patient_id_len, "-" * max_patient_name_len, "-" * max_diagnosis_len))
    
    current_patient = None
    
    for sort_key, formatted_date, patient_name, patient_id, display_diagnosis in normalized_info:
        if current_patient == patient_id:
            patient_id_dashes = '-' * len(patient_id)
            patient_name_dashes = '-' * len(patient_name)
            secondary_format = "     {:<6} | {:<" + str(max_patient_id_len) + "} | {:<" + str(max_patient_name_len) + "} | {:<" + str(max_diagnosis_len) + "}"
            lines.append(secondary_format.format(formatted_date, patient_id_dashes, patient_name_dashes, display_diagnosis))
        else:
            current_patient = patient_id
            primary_format = "     {:<6} | {:<" + str(max_patient_id_len) + "} | {:<" + str(max_patient_name_len) + "} | {:<" + str(max_diagnosis_len) + "}"
            lines.append(primary_format.format(formatted_date, patient_id, patient_name, display_diagnosis))
    
    lines.append("")
    lines.append("Generated on: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    return "\n".join(lines)


def create_and_open_notepad_file(content, filename_prefix="existing_patients"):
    """
    Create a text file with the given content and open it in notepad.
    Compatible with Windows XP and Python 3.4.4.
    
    Args:
        content: Text content to write to the file
        filename_prefix: Prefix for the generated filename
        
    Returns:
        str: Path to the created file, or None if an error occurred
    """
    try:
        # Generate a unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = "{}_{}.txt".format(filename_prefix, timestamp)
        
        # Use the temp directory for the file
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        # Write the file with ASCII encoding for XP compatibility
        with open(file_path, 'w') as f:
            # Ensure content is ASCII-compatible
            ascii_content = content.encode('ascii', 'replace').decode('ascii')
            f.write(ascii_content)
        
        # Open the file in notepad using Windows XP compatible method
        try:
            # Use subprocess to avoid shell=True security issues
            subprocess.Popen(['notepad.exe', file_path])
        except Exception:
            # Fallback method for older systems
            os.system('notepad.exe "{}"'.format(file_path))
        
        return file_path
        
    except Exception as e:
        # Return None on error - caller should handle gracefully
        return None


def generate_existing_patients_notepad(patient_info, title):
    """
    Generate a notepad file for existing patients table.

    Args:
        patient_info: List of tuples (surgery_date, patient_name, patient_id, diagnosis_code, patient_row)
        title: Title for the table section

    Returns:
        str: Path to the created file, or None if an error occurred
    """
    content = format_patient_table_for_notepad(patient_info, title)
    return create_and_open_notepad_file(content, "existing_patients")


def generate_combined_patients_notepad(existing_patient_info, existing_title, dual_date_patient_info=None, dual_date_title=None):
    """
    Generate a combined notepad file for existing patients and dual-date anticipatory patients.

    Args:
        existing_patient_info: List of tuples (surgery_date, patient_name, patient_id, diagnosis_code, patient_row) for existing patients
        existing_title: Title for the existing patients table section
        dual_date_patient_info: Optional list of tuples for dual-date anticipatory patients
        dual_date_title: Optional title for the dual-date patients table section

    Returns:
        str: Path to the created file, or None if an error occurred
    """
    content = format_patient_table_for_notepad(existing_patient_info, existing_title)

    # If dual-date patients are provided, append their table
    if dual_date_patient_info and dual_date_title:
        dual_date_content = format_patient_table_for_notepad(dual_date_patient_info, dual_date_title)
        content += "\n\n" + dual_date_content  # Add spacing between tables

    return create_and_open_notepad_file(content, "existing_patients")