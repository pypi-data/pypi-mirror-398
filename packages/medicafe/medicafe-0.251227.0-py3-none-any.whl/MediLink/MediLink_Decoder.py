# MediLink_Decoder.py
import os, sys, csv

# Add workspace directory to Python path for MediCafe imports
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(current_dir)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from MediCafe.core_utils import get_shared_config_loader

# Get shared config loader
MediLink_ConfigLoader = get_shared_config_loader()
if MediLink_ConfigLoader:
    load_configuration = MediLink_ConfigLoader.load_configuration
    log = MediLink_ConfigLoader.log
else:
    # Fallback functions if config loader is not available
    def load_configuration():
        return {}, {}
    def log(message, level="INFO"):
        print("[{}] {}".format(level, message))
from MediLink_Parser import parse_era_content, parse_277_content, parse_277IBR_content, parse_277EBR_content, parse_dpt_content, parse_ebt_content, parse_ibt_content, parse_999_content

# Define new_fieldnames globally
new_fieldnames = ['Claim #', 'Payer', 'Status', 'Patient', 'Proc.', 'Serv.', 'Allowed', 'Paid', 'Pt Resp', 'Charged']

# Cross-file duplicate suppression set. This allows de-duplication across multiple input files
# within a single run. Safe on XP; memory footprint is minimal for typical claim volumes.
GLOBAL_SEEN_CLAIM_NUMBERS = set()

class UnifiedRecord:
    def __init__(self, claim_number='', status='', patient='', payer='', proc_date='', serv_date='', allowed='', paid='', pt_resp='', charged=''):
        self.claim_number = claim_number
        self.payer = payer  # Added payer to the constructor
        self.status = status
        self.patient = patient
        self.proc_date = proc_date
        self.serv_date = serv_date
        self.allowed = allowed
        self.paid = paid
        self.pt_resp = pt_resp
        self.charged = charged

    def to_dict(self):
        return {
            'Claim #': self.claim_number,
            'Payer': self.payer,  # Added payer to the dictionary representation
            'Status': self.status,
            'Patient': self.patient,
            'Proc.': self.proc_date,
            'Serv.': self.serv_date,
            'Allowed': self.allowed,
            'Paid': self.paid,
            'Pt Resp': self.pt_resp,
            'Charged': self.charged
        }

    def __repr__(self):
        return ("UnifiedRecord(claim_number='{0}', status='{1}', patient='{2}', payer='{3}', proc_date='{4}', serv_date='{5}', "
                "allowed='{6}', paid='{7}', pt_resp='{8}', charged='{9}')").format(
            self.claim_number, self.status, self.patient, self.payer, self.proc_date,
            self.serv_date, self.allowed, self.paid, self.pt_resp, self.charged)  # Added payer to the repr

def process_decoded_file(file_path, output_directory, return_records=False, debug=False): # Renamed from process_file
    os.makedirs(output_directory, exist_ok=True)

    file_type = determine_file_type(file_path)
    content = read_file(file_path)

    parse_functions = {
        'ERA': parse_era_content,
        '277': parse_277_content,
        '277IBR': parse_277IBR_content,
        '277EBR': parse_277EBR_content,
        'DPT': parse_dpt_content,
        'EBT': parse_ebt_content,
        'IBT': parse_ibt_content,
        '999': parse_999_content
    }

    parse_function = parse_functions.get(file_type)
    if parse_function is None:
        log("Unsupported file type: {}".format(file_type))
        return []

    records = parse_function(content, debug=debug)
    formatted_records = format_records(records, file_type)

    if not return_records:
        display_table([record.to_dict() for record in formatted_records])
        output_file_path = os.path.join(output_directory, "{}_decoded.csv".format(os.path.basename(file_path)))
        write_records_to_csv(formatted_records, output_file_path)
        log("Decoded data written to {}".format(output_file_path))

    return formatted_records  # Returns list of UnifiedRecord instances

def determine_file_type(file_path):
    file_extensions = {
        '.era': 'ERA',
        '.277': '277',
        '.277ibr': '277IBR',
        '.277ebr': '277EBR',
        '.dpt': 'DPT',
        '.ebt': 'EBT',
        '.ibt': 'IBT'
    }
    
    for ext, file_type in file_extensions.items():
        if file_path.endswith(ext):
            return file_type
            
    log("Unsupported file type for file: {}".format(file_path))
    return None

def read_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def write_records_to_csv(records, output_file_path):
    if not records:
        log("No records to write.", 'error')
        return

    # Use the global variable for fieldnames
    fieldnames = new_fieldnames
    
    with open(output_file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_dict())

def format_records(records, file_type):
    formatted_records = []
    seen_claim_numbers = set()  # Set to track unique claim numbers within this file

    for i, record in enumerate(records):
        # Determine the claim number based on the file type
        if file_type == 'IBT':
            claim_number = record.get('Patient Control Number', '')
        elif file_type == 'ERA':
            claim_number = record.get('Chart Number', '')
        elif file_type == 'EBT':
            claim_number = record.get('Patient Control Number', '')
        elif file_type == '277':
            claim_number = record.get('Claim #', '')
        elif file_type == '999':
            claim_number = ''  # 999 lacks a direct claim number
        else:
            claim_number = ''  # Default to empty if file type is not recognized

        # Skip records without a claim number, except for 999 summary/detail rows
        if not claim_number and file_type != '999':
            log("Record {} missing claim_number. Skipping.".format(i + 1), level="WARNING")
            continue

        # Check for duplicates (within this file and across files in this run)
        if claim_number and (claim_number in seen_claim_numbers or claim_number in GLOBAL_SEEN_CLAIM_NUMBERS):
            log("Duplicate claim_number {} found at record {}. Skipping.".format(claim_number, i + 1), level="DEBUG")
            continue

        if claim_number:
            seen_claim_numbers.add(claim_number)
            GLOBAL_SEEN_CLAIM_NUMBERS.add(claim_number)  # Add to cross-file set so later files also skip

        unified_record = UnifiedRecord()

        # Populate the unified_record based on the file type
        if file_type == 'IBT':
            unified_record.claim_number = claim_number
            unified_record.status = record.get('Status', '')
            unified_record.patient = record.get('Patient Name', '')
            unified_record.proc_date = format_date(record.get('To Date', ''))
            unified_record.serv_date = format_date(record.get('From Date', ''))
            unified_record.charged = record.get('Charge', '')

        elif file_type == 'ERA':
            unified_record.claim_number = claim_number
            unified_record.status = record.get('claimStatus', '')
            unified_record.patient = record.get('Patient', '')
            unified_record.proc_date = format_date(record.get('processed_date', ''))
            unified_record.serv_date = format_date(record.get('Date of Service', ''))
            unified_record.allowed = record.get('Allowed Amount', '')
            unified_record.paid = record.get('Amount Paid', '')
            unified_record.pt_resp = record.get('Patient Responsibility', '')
            unified_record.charged = record.get('Charge', '')

        elif file_type == 'EBT':
            if 'Patient Control Number' in record:
                unified_record.claim_number = claim_number
                message_type = record.get('Message Type', '').upper()
                status_mapping = {
                    'A': 'Accepted',
                    'R': 'Rejected',
                }
                unified_record.status = record.get('Message', '') or status_mapping.get(message_type, message_type)
                unified_record.payer = record.get('Message Initiator', '')
                unified_record.patient = record.get('Patient Name', '')
                unified_record.proc_date = format_date(record.get('To Date', ''))
                unified_record.serv_date = format_date(record.get('From Date', ''))
                unified_record.allowed = ''
                unified_record.paid = ''
                unified_record.pt_resp = ''
                unified_record.charged = record.get('Charge', '')
                log("Formatted EBT Record {}: {}".format(i + 1, unified_record), level="DEBUG")
            else:
                log("Skipped non-claim EBT Record {}: {}".format(i + 1, record), level="DEBUG")
                continue

        elif file_type == '277':
            unified_record.claim_number = claim_number
            unified_record.status = record.get('Status', '')
            unified_record.patient = record.get('Patient', '')
            unified_record.proc_date = format_date(record.get('Proc.', ''))
            unified_record.serv_date = format_date(record.get('Serv.', ''))
            unified_record.allowed = ''
            unified_record.paid = record.get('Paid', '')
            unified_record.pt_resp = ''
            unified_record.charged = record.get('Charged', '')

        elif file_type == '999':
            # Show 999 summary rows; leave claim_number empty
            unified_record.claim_number = ''
            unified_record.status = record.get('Status', '')
            unified_record.patient = ''
            unified_record.payer = record.get('Functional ID', '')
            unified_record.proc_date = ''
            unified_record.serv_date = ''
            unified_record.allowed = ''
            unified_record.paid = ''
            unified_record.pt_resp = ''
            unified_record.charged = ''

        # Append the unified record to the list
        formatted_records.append(unified_record)

    return formatted_records

def format_date(date_str):
    if date_str and len(date_str) >= 8:
        return date_str[4:6] + '-' + date_str[6:8]  # Adjusted to match sample date format 'YYYYMMDD'
    return ''

def display_table(records):
    """
    Display records in a formatted table after deduplication.
    
    Args:
        records (list): List of UnifiedRecord instances.
    """
    # Deduplicate records before displaying
    records = deduplicate_records(records)

    if not records:
        print("No records to display.")
        return

    # PERFORMANCE FIX: Single-pass optimization - determine used fields and calculate widths in one pass
    used_fields = []
    col_widths = {}
    
    # First pass: identify used fields and initialize widths
    for field in new_fieldnames:
        col_widths[field] = len(field)  # Header width
        
    # Second pass: check for used fields and calculate max widths
    for record in records:
        for field in new_fieldnames:
            value_str = str(record.get(field, ''))
            if value_str.strip() and field not in used_fields:
                used_fields.append(field)
            if field in col_widths:
                col_widths[field] = max(col_widths[field], len(value_str))
    
    # Filter col_widths to only used fields
    col_widths = {field: col_widths[field] for field in used_fields}

    if not used_fields:
        print("No data to display.")
        return

    # Create table header
    header = " | ".join("{:<{}}".format(field, col_widths[field]) for field in used_fields)
    print(header)
    print("-" * len(header))

    # Create table rows
    for record in records:
        row = " | ".join("{:<{}}".format(str(record.get(field, '')), col_widths[field]) for field in used_fields)
        print(row)

def display_consolidated_records(records):
    """
    Display the consolidated records in a formatted table.
    Removes any records that are completely empty or only contain whitespace.
    If no valid records are found, displays a message to that effect.
    """
    # Deduplicate records before displaying
    records = deduplicate_records(records)

    # If records are UnifiedRecord instances, convert them to dictionaries
    if records and isinstance(records[0], UnifiedRecord):
        dict_records = [record.to_dict() for record in records]
    elif records and isinstance(records[0], dict):
        dict_records = records
    else:
        log("Invalid record format for display.", level="ERROR")
        return
    
    # Filter out records that are completely empty or only contain whitespace
    filtered_records = [
        record for record in dict_records 
        if any(str(record.get(field, '')).strip() for field in new_fieldnames)
    ]
    
    if not filtered_records:
        print("No valid records to display after filtering empty rows.")
        return
    
    # PERFORMANCE FIX: Single-pass optimization - determine used fields and calculate widths in one pass
    used_fields = []
    col_widths = {}
    
    # First pass: initialize column widths with header lengths
    for field in new_fieldnames:
        col_widths[field] = len(field)
        
    # Second pass: check for used fields and calculate max widths
    for record in filtered_records:
        for field in new_fieldnames:
            value_str = str(record.get(field, ''))
            if value_str.strip() and field not in used_fields:
                used_fields.append(field)
            if field in col_widths:
                col_widths[field] = max(col_widths[field], len(value_str))
    
    # Filter col_widths to only used fields
    col_widths = {field: col_widths[field] for field in used_fields}

    if not used_fields:
        print("No data to display.")
        return
    
    # Print header
    header = " | ".join("{:<{}}".format(field, col_widths[field]) for field in used_fields)
    print(header)
    print("-" * len(header))
    
    # Print each row
    for record in filtered_records:
        row = " | ".join("{:<{}}".format(str(record.get(field, '')), col_widths[field]) for field in used_fields)
        print(row)

def deduplicate_records(records):
    """
    Remove duplicate records based on claim_number.
    
    Args:
        records (list): List of UnifiedRecord instances.
    
    Returns:
        list: List of unique UnifiedRecord instances.
    """
    unique_records_dict = {}
    for record in records:
        if record.claim_number not in unique_records_dict:
            unique_records_dict[record.claim_number] = record
        else:
            log("Duplicate record found for claim_number {}. Skipping.".format(record.claim_number), "DEBUG")
    
    return list(unique_records_dict.values())

if __name__ == "__main__":
    config, _ = load_configuration()
    
    files = sys.argv[1:]
    if not files:
        log("No files provided as arguments.", 'error')
        sys.exit(1)

    output_directory = config['MediLink_Config'].get('local_storage_path')
    all_records = []
    for file_path in files:
        try:
            records = process_decoded_file(file_path, output_directory, return_records=True)
            all_records.extend(records)
        except Exception as e:
            log("Failed to process {}: {}".format(file_path, e), 'error')
    
    # Call the deduplication function
    unique_records = deduplicate_records(all_records)

    display_consolidated_records([record.to_dict() for record in unique_records])

    if input("Do you want to export the consolidated records to a CSV file? (y/n): ").strip().lower() == 'y':
        consolidated_csv_path = os.path.join(output_directory, "Consolidated_Records.csv")
        write_records_to_csv(unique_records, consolidated_csv_path)
        log("Consolidated records written to {}".format(consolidated_csv_path))
