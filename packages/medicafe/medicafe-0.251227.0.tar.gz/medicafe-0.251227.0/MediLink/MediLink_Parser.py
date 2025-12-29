# MediLink_Parser.py
import re

# Pre-compile regex patterns for better performance
_EBT_KEY_VALUE_PATTERN = re.compile(r'([^:]+):\s*(.+?)(?=\s{2,}[^:]+:|$)')
_ERA_SEGMENT_PATTERN = re.compile(r'\*')
_277_SEGMENT_PATTERN = re.compile(r'\*')

def parse_era_content(content, debug=False):
    extracted_data = []
    normalized_content = content.replace('~\n', '~')  # Normalize line endings
    lines = normalized_content.split('~')

    record = {}
    check_eft, payer_address = None, None
    allowed_amount, write_off, patient_responsibility, adjustment_amount = 0, 0, 0, 0
    is_payer_section = False

    for line in lines:
        segments = _ERA_SEGMENT_PATTERN.split(line)

        if segments[0] == 'TRN' and len(segments) > 2:
            check_eft = segments[2]  # Extract check/EFT number

        if segments[0] == 'N1':
            if segments[1] == 'PR':
                is_payer_section = True  # Enter payer section
            elif segments[1] == 'PE':
                is_payer_section = False  # Exit payer section

        if is_payer_section and segments[0] == 'N3' and len(segments) > 1:
            payer_address = segments[1]  # Extract payer address

        if segments[0] == 'CLP' and len(segments) >= 5:
            if record:
                # Calculate adjustment amount if not explicitly provided
                if adjustment_amount == 0 and (write_off > 0 or patient_responsibility > 0):
                    adjustment_amount = write_off + patient_responsibility

                # Update record with calculated amounts
                record.update({
                    'Payer Address': payer_address,
                    'Allowed Amount': allowed_amount,
                    'Write Off': write_off,
                    'Patient Responsibility': patient_responsibility,
                    'Adjustment Amount': adjustment_amount,
                })
                extracted_data.append(record)

                # Reset counters for next record
                allowed_amount, write_off, patient_responsibility, adjustment_amount = 0, 0, 0, 0

            # Start new record
            record = {
                'Check EFT': check_eft,
                'Chart Number': segments[1],
                'Payer Address': payer_address,
                'Amount Paid': segments[4],
                'Charge': segments[3],
            }

        elif segments[0] == 'CAS':
            try:
                if segments[1] == 'CO':
                    write_off += float(segments[3])  # Contractual obligation
                elif segments[1] == 'PR':
                    patient_responsibility += float(segments[3])  # Patient responsibility
                elif segments[1] == 'OA':
                    adjustment_amount += float(segments[3])  # Other adjustments
            except (ValueError, IndexError):
                # Skip malformed CAS segments
                continue

        elif segments[0] == 'AMT' and segments[1] == 'B6':
            try:
                allowed_amount += float(segments[2])  # Allowed amount
            except (ValueError, IndexError):
                # Skip malformed AMT segments
                continue

        elif segments[0] == 'DTM' and (segments[1] == '232' or segments[1] == '472'):
            record['Date of Service'] = segments[2]  # Service date

    # Process final record
    if record:
        if adjustment_amount == 0 and (write_off > 0 or patient_responsibility > 0):
            adjustment_amount = write_off + patient_responsibility
        record.update({
            'Allowed Amount': allowed_amount,
            'Write Off': write_off,
            'Patient Responsibility': patient_responsibility,
            'Adjustment Amount': adjustment_amount,
        })
        extracted_data.append(record)

    if debug:
        print("Parsed ERA Content:")
        for data in extracted_data:
            print(data)

    return extracted_data

def parse_277_content(content, debug=False):
    segments = content.split('~')
    records = []
    current_record = {}
    
    for segment in segments:
        parts = _277_SEGMENT_PATTERN.split(segment)
        if parts[0] == 'HL':
            if current_record:
                records.append(current_record)  # Save completed record
                current_record = {}  # Start new record
        elif parts[0] == 'NM1':
            if parts[1] == 'QC' and len(parts) > 4:
                current_record['Patient'] = ' '.join([parts[3], parts[4]])  # Patient name
            elif parts[1] == '41' and len(parts) > 3:
                current_record['Clearing House'] = parts[3]  # Clearing house
            elif parts[1] == 'PR' and len(parts) > 3:
                current_record['Payer'] = parts[3]  # Payer name
        elif parts[0] == 'TRN' and len(parts) > 2:
            current_record['Claim #'] = parts[2]  # Claim number
        elif parts[0] == 'STC' and len(parts) > 1:
            current_record['Status'] = parts[1]  # Claim status
            if len(parts) > 4:
                current_record['Paid'] = parts[4]  # Paid amount
        elif parts[0] == 'DTP' and len(parts) > 3:
            if parts[1] == '472':
                current_record['Serv.'] = parts[3]  # Service date
            elif parts[1] == '050':
                current_record['Proc.'] = parts[3]  # Process date
        elif parts[0] == 'AMT' and parts[1] == 'YU' and len(parts) > 2:
            current_record['Charged'] = parts[2]  # Charged amount

    if current_record:
        records.append(current_record)  # Add final record

    if debug:
        print("Parsed 277 Content:")
        for record in records:
            print(record)

    return records

def parse_277IBR_content(content, debug=False):
    return parse_277_content(content, debug)

def parse_277EBR_content(content, debug=False):
    return parse_277_content(content, debug)

def parse_dpt_content(content, debug=False):
    extracted_data = []
    lines = content.splitlines()
    record = {}
    
    for line in lines:
        if 'Patient Account Number:' in line:
            if record:
                extracted_data.append(record)  # Save completed record
            record = {}  # Start new record
        
        # More efficient split - only split on first occurrence
        colon_pos = line.find(':')
        if colon_pos != -1:
            key = line[:colon_pos].strip()
            value = line[colon_pos + 1:].strip()
            record[key] = value  # Add key-value pair to current record
    
    if record:
        extracted_data.append(record)  # Add final record

    if debug:
        print("Parsed DPT Content:")
        for data in extracted_data:
            print(data)

    return extracted_data

def parse_ebt_content(content, debug=False):
    extracted_data = []  # List to hold all extracted records
    lines = content.splitlines()  # Split the content into individual lines
    record = {}  # Dictionary to hold the current record being processed
    
    for line in lines:
        # Check for the start of a new record based on the presence of 'Patient Name'
        if 'Patient Name:' in line and record:
            ebt_post_processor(record)  # Process the current record before adding it to the list
            extracted_data.append(record)  # Add the completed record to the list
            record = {}  # Reset the record for the next entry

        # Find all key-value pairs in the current line
        matches = _EBT_KEY_VALUE_PATTERN.findall(line)
        for key, value in matches:
            key = key.strip()  # Remove leading/trailing whitespace from the key
            value = value.strip()  # Remove leading/trailing whitespace from the value
            record[key] = value  # Add the key-value pair to the current record

    # Process and add the last record if it exists
    if record:
        ebt_post_processor(record)  # Final processing of the last record
        extracted_data.append(record)  # Add the last record to the list

    # Debug output to show parsed data if debugging is enabled
    if debug:
        print("Parsed EBT Content:")
        for data in extracted_data:
            print(data)

    return extracted_data  # Return the list of extracted records

def ebt_post_processor(record):
    # Process the 'Message Initiator' field to separate it from 'Message Type'
    if 'Message Initiator' in record and 'Message Type:' in record['Message Initiator']:
        parts = record['Message Initiator'].split('Message Type:')  # Split the string into parts
        record['Message Initiator'] = parts[0].strip()  # Clean up the 'Message Initiator'
        record['Message Type'] = parts[1].strip()  # Clean up the 'Message Type'

def parse_ibt_content(content, debug=False):
    extracted_data = []
    lines = content.splitlines()
    record = {}
    
    for line in lines:
        if 'Submitter Batch ID:' in line:
            if record:
                extracted_data.append(record)  # Save completed record
            record = {}  # Start new record
        
        # More efficient split - only split on first occurrence
        colon_pos = line.find(':')
        if colon_pos != -1:
            key = line[:colon_pos].strip()
            value = line[colon_pos + 1:].strip()
            record[key] = value  # Add key-value pair to current record
    
    if record:
        extracted_data.append(record)  # Add final record

    if debug:
        print("Parsed IBT Content:")
        for data in extracted_data:
            print(data)

    return extracted_data

def parse_999_content(content, debug=False):
    """
    Minimal 999 Implementation Acknowledgment parser.
    Extracts overall transaction set acknowledgment (AK9) and per-set (AK5) statuses when available.
    Returns a list with a single summary dict plus optional per-set entries.
    """
    records = []
    segments = content.split('~')
    overall_status = None
    functional_id = None
    control_numbers = []  # AK2 ST02 values
    per_set_statuses = []  # List of {'set_control': str, 'status': str}

    for seg in segments:
        parts = seg.split('*')
        if not parts or not parts[0]:
            continue
        tag = parts[0]
        if tag == 'AK1' and len(parts) > 1:
            functional_id = parts[1]
        elif tag == 'AK2' and len(parts) > 2:
            # Transaction Set Acknowledgment - capture ST02 control number
            control_numbers.append(parts[2])
        elif tag == 'AK5' and len(parts) > 1:
            # Transaction Set Response Trailer - status code in AK5-01 (A, E, R)
            status_code = parts[1]
            per_set_statuses.append({'status': status_code})
        elif tag == 'AK9' and len(parts) > 1:
            # Functional Group Response Trailer - overall status in AK9-01
            overall_status = parts[1]

    # Map X12 codes to friendly text
    status_map = {'A': 'Accepted', 'E': 'Accepted with Errors', 'R': 'Rejected'}
    overall_text = status_map.get(overall_status, overall_status or '')

    summary = {
        'Ack Type': '999',
        'Functional ID': functional_id or '',
        'Status': overall_text,
        'Sets Acknowledged': len(control_numbers) if control_numbers else 0,
    }
    records.append(summary)

    # Optionally include per-set detail rows
    for idx, st in enumerate(per_set_statuses):
        detail = {
            'Ack Type': '999',
            'Functional ID': functional_id or '',
            'Set #': str(idx + 1),
            'Status': status_map.get(st.get('status', ''), st.get('status', '')),
        }
        # Claim # not available in 999; leave out
        records.append(detail)

    if debug:
        print('Parsed 999 Content:')
        for r in records:
            print(r)
    return records

def determine_file_type(file_path):
    file_extensions = {
        '.era': 'ERA',
        '.277': '277',
        '.277ibr': '277IBR',
        '.277ebr': '277EBR',
        '.dpt': 'DPT',
        '.ebt': 'EBT',
        '.ibt': 'IBT',
        '.999': '999'
    }
    
    for ext, file_type in file_extensions.items():
        if file_path.endswith(ext):
            return file_type
            
    log("Unsupported file type for file: {}".format(file_path))
    return None