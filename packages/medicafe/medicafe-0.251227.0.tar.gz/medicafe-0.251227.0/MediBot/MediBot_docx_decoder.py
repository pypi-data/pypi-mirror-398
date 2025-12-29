#MediBot_docx_decoder.py
from datetime import datetime
from collections import OrderedDict
import os, re, zipfile, pprint, time, sys

# Add workspace directory to Python path for MediCafe imports
current_dir = os.path.dirname(os.path.abspath(__file__))
workspace_dir = os.path.dirname(current_dir)
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

try:
    from docx import Document
except ImportError:
    Document = None
try:
    from lxml import etree
except ImportError:
    etree = None

from MediCafe.core_utils import get_shared_config_loader
MediLink_ConfigLoader = get_shared_config_loader()
if MediLink_ConfigLoader is None:
    raise ImportError(
        "[MediBot_docx_decoder] CRITICAL: MediLink_ConfigLoader module import failed. "
        "This module requires MediLink_ConfigLoader to function. "
        "Check PYTHONPATH, module dependencies, and ensure MediCafe package is properly installed."
    )
# Pre-compile regex patterns for better performance (XP/3.4.4 compatible)
_DIAGNOSIS_CODE_PATTERN = re.compile(r'H\d{2}\.\d+')
_DAY_WEEK_PATTERN = re.compile(r"(MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY)")
_MONTH_DAY_PATTERN = re.compile(r"(JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER) \d{1,2}")
_YEAR_PATTERN = re.compile(r"\d{4}")
_YEAR_SPLIT_PATTERNS = [
    re.compile(r'(\d{3}) (\d{1})'),
    re.compile(r'(\d{1}) (\d{3})'),
    re.compile(r'(\d{2}) (\d{2})')
]
_DAY_SPLIT_REASSEMBLY_PATTERN = re.compile(
    r'((?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER))\s+(\d{1})\s+(\d{1})\b',
    re.IGNORECASE
)
_DIGIT_PARTS_PATTERN = re.compile(r'\b(\d{1,2})\b')
_COMMA_PATTERN = re.compile(r',')

# Pre-compile abbreviation patterns for normalize_text optimization
_MONTH_ABBR_PATTERNS = {
    'JAN': re.compile(r'\bJAN\b', re.IGNORECASE),
    'FEB': re.compile(r'\bFEB\b', re.IGNORECASE),
    'MAR': re.compile(r'\bMAR\b', re.IGNORECASE),
    'APR': re.compile(r'\bAPR\b', re.IGNORECASE),
    'MAY': re.compile(r'\bMAY\b', re.IGNORECASE),
    'JUN': re.compile(r'\bJUN\b', re.IGNORECASE),
    'JUL': re.compile(r'\bJUL\b', re.IGNORECASE),
    'AUG': re.compile(r'\bAUG\b', re.IGNORECASE),
    'SEP': re.compile(r'\bSEP\b', re.IGNORECASE),
    'OCT': re.compile(r'\bOCT\b', re.IGNORECASE),
    'NOV': re.compile(r'\bNOV\b', re.IGNORECASE),
    'DEC': re.compile(r'\bDEC\b', re.IGNORECASE)
}

_DAY_ABBR_PATTERNS = {
    'MON': re.compile(r'\bMON\b', re.IGNORECASE),
    'TUE': re.compile(r'\bTUE\b', re.IGNORECASE),
    'WED': re.compile(r'\bWED\b', re.IGNORECASE),
    'THU': re.compile(r'\bTHU\b', re.IGNORECASE),
    'FRI': re.compile(r'\bFRI\b', re.IGNORECASE),
    'SAT': re.compile(r'\bSAT\b', re.IGNORECASE),
    'SUN': re.compile(r'\bSUN\b', re.IGNORECASE)
}

# Month and day mapping dictionaries
_MONTH_MAP = {
    'JAN': 'JANUARY', 'FEB': 'FEBRUARY', 'MAR': 'MARCH', 'APR': 'APRIL', 
    'MAY': 'MAY', 'JUN': 'JUNE', 'JUL': 'JULY', 'AUG': 'AUGUST', 
    'SEP': 'SEPTEMBER', 'OCT': 'OCTOBER', 'NOV': 'NOVEMBER', 'DEC': 'DECEMBER'
}
_DAY_MAP = {
    'MON': 'MONDAY', 'TUE': 'TUESDAY', 'WED': 'WEDNESDAY', 'THU': 'THURSDAY', 
    'FRI': 'FRIDAY', 'SAT': 'SATURDAY', 'SUN': 'SUNDAY'
}


def parse_docx(filepath, surgery_dates, capture_schedule_positions=False):  # Accept surgery_dates as a parameter
    if Document is None:
        MediLink_ConfigLoader.log("docx module not available, cannot parse .docx files", level="WARNING")
        return {}
    
    # TIMING: Start individual DOCX file processing
    file_start_time = time.time()
    
    try:
        # TIMING: Start document opening
        doc_open_start = time.time()
        doc = Document(filepath)  # Open the .docx file
        doc_open_end = time.time()
        doc_open_duration = doc_open_end - doc_open_start
    except Exception as e:
        MediLink_ConfigLoader.log("Error opening document: {}".format(e), level="ERROR")  # Log error
        return {}

    patient_data = OrderedDict()  # Initialize OrderedDict to store data
    schedule_positions = {}  # NEW: Track patient order in schedule
    MediLink_ConfigLoader.log("Extracting Date of Service from {}".format(filepath), level="DEBUG")
    
    # TIMING: Start date extraction
    date_extraction_start = time.time()
    date_of_service = extract_date_of_service(filepath)  # Extract date of service
    date_extraction_end = time.time()
    date_extraction_duration = date_extraction_end - date_extraction_start
    MediLink_ConfigLoader.log("Date of Service recorded as: {}".format(date_of_service), level="DEBUG")

    # TIMING: Start date conversion and validation
    date_validation_start = time.time()
    
    # Convert date_of_service to match the format of surgery_dates
    date_of_service_dt = datetime.strptime(date_of_service, '%m-%d-%Y')  # Convert to datetime object
    
    # Check if the date_of_service is in the passed surgery_dates
    # If surgery_dates is None, we bypass this check (used for single-file CLI processing)
    if surgery_dates is not None and date_of_service_dt not in surgery_dates:  # Direct comparison with datetime objects
        MediLink_ConfigLoader.log("Date of Service {} not found in provided surgery dates. Skipping document.".format(date_of_service_dt), level="DEBUG")
        return {}  # Early exit if date is not found
    
    if surgery_dates is None:
        MediLink_ConfigLoader.log("Bypassing surgery dates check for single file processing of {}.".format(date_of_service), level="INFO")
    else:
        MediLink_ConfigLoader.log("Date of Service {} found in surgery dates. Proceeding with parsing of the document.".format(date_of_service), level="DEBUG")  # Log that date of service was found
    
    # Convert back to MM-DD-YYYY format (ensures normalization)
    date_of_service = date_of_service_dt.strftime('%m-%d-%Y')  
    
    date_validation_end = time.time()
    date_validation_duration = date_validation_end - date_validation_start

    # TIMING: Start table processing
    table_processing_start = time.time()
    tables_processed = 0
    rows_processed = 0
    patients_found = 0

    for table in doc.tables:  # Iterate over tables in the document
        tables_processed += 1
        for row_idx, row in enumerate(table.rows):
            rows_processed += 1
            cells = [cell.text.strip() for cell in row.cells]
            if len(cells) > 4 and cells[3].startswith('#'):
                try:
                    patient_id = parse_patient_id(cells[3])
                    diagnosis_code = parse_diagnosis_code(cells[4])
                    left_or_right_eye = parse_left_or_right_eye(cells[4])
                    femto_yes_or_no = parse_femto_yes_or_no(cells[4])

                    if patient_id not in patient_data:
                        patient_data[patient_id] = {}
                        patients_found += 1

                    if date_of_service in patient_data[patient_id]:
                        MediLink_ConfigLoader.log("Duplicate entry for patient ID {} on date {}. Skipping.".format(patient_id, date_of_service), level="WARNING")
                    else:
                        patient_data[patient_id][date_of_service] = [diagnosis_code, left_or_right_eye, femto_yes_or_no]
                        
                        # NEW: Store schedule position if requested
                        if capture_schedule_positions:
                            if patient_id not in schedule_positions:
                                schedule_positions[patient_id] = {}
                            schedule_positions[patient_id][date_of_service] = row_idx
                except Exception as e:
                    MediLink_ConfigLoader.log("Error processing row: {}. Error: {}".format(cells, e), level="ERROR")
    
    table_processing_end = time.time()
    table_processing_duration = table_processing_end - table_processing_start

    # TIMING: Start validation
    validation_start = time.time()
    
    # Validation steps
    validate_unknown_entries(patient_data)
    validate_diagnostic_code(patient_data)
    
    validation_end = time.time()
    validation_duration = validation_end - validation_start

    # TIMING: End total file processing
    file_end_time = time.time()
    total_duration = file_end_time - file_start_time
    
    # Log timing details for slow files (more than 0.5 seconds)
    if total_duration > 0.5:
        print("    - DOCX file timing breakdown:")
        print("      * Document opening: {:.3f}s".format(doc_open_duration))
        print("      * Date extraction: {:.3f}s".format(date_extraction_duration))
        print("      * Date validation: {:.3f}s".format(date_validation_duration))
        print("      * Table processing: {:.3f}s ({} tables, {} rows, {} patients)".format(
            table_processing_duration, tables_processed, rows_processed, patients_found))
        print("      * Validation: {:.3f}s".format(validation_duration))
        print("      * Total: {:.3f}s".format(total_duration))
    
    # Return both data structures if schedule positions were captured
    if capture_schedule_positions:
        return patient_data, schedule_positions
    else:
        return patient_data


def validate_unknown_entries(patient_data):
    for patient_id, dates in list(patient_data.items()):
        for date, details in list(dates.items()):
            if 'Unknown' in details:
                warning_message = "Warning: 'Unknown' entry found. Patient ID: {}, Date: {}, Details: {}".format(patient_id, date, details)
                MediLink_ConfigLoader.log(warning_message, level="WARNING")
                del patient_data[patient_id][date]
        if not patient_data[patient_id]:  # If no dates left for the patient, remove the patient
            del patient_data[patient_id]


def validate_diagnostic_code(patient_data):
    for patient_id, dates in patient_data.items():
        for date, details in dates.items():
            diagnostic_code, eye, _ = details
            if diagnostic_code[-1].isdigit():
                if eye == 'Left' and not diagnostic_code.endswith('2'):
                    log_and_warn(patient_id, date, diagnostic_code, eye)
                elif eye == 'Right' and not diagnostic_code.endswith('1'):
                    log_and_warn(patient_id, date, diagnostic_code, eye)


def log_and_warn(patient_id, date, diagnostic_code, eye):
    warning_message = (
        "Warning: Mismatch found for Patient ID: {}, Date: {}, "
        "Diagnostic Code: {}, Eye: {}".format(patient_id, date, diagnostic_code, eye)
    )
    MediLink_ConfigLoader.log(warning_message, level="WARNING")


def extract_date_of_service(docx_path, use_in_memory=True):
    # TIMING: Start date extraction process
    extraction_start_time = time.time()
    
    extract_to = "extracted_docx_debug"
    in_memory_result = None
    directory_based_result = None

    # Log the selected approach
    if use_in_memory:
        MediLink_ConfigLoader.log("Using In-Memory extraction approach for Surgery Schedule.", level="INFO")
    else:
        MediLink_ConfigLoader.log("Using Directory-Based extraction approach for Surgery Schedule.", level="INFO")

    # Directory-Based Extraction
    if not use_in_memory:  # Only perform directory-based extraction if in-memory is not selected
        # TIMING: Start directory-based extraction
        dir_extraction_start = time.time()
        
        try:
            if not os.path.exists(extract_to):
                os.makedirs(extract_to)
                MediLink_ConfigLoader.log("Created extraction directory: {}".format(extract_to), level="DEBUG")
            
            with zipfile.ZipFile(docx_path, 'r') as docx:
                MediLink_ConfigLoader.log("Opened DOCX file: {}".format(docx_path), level="DEBUG")
                docx.extractall(extract_to)
                MediLink_ConfigLoader.log("Extracted DOCX to: {}".format(extract_to), level="DEBUG")
            
            file_path = find_text_in_xml(extract_to, "Surgery Schedule")
            if file_path:
                MediLink_ConfigLoader.log("Found XML file with target text: {}".format(file_path), level="DEBUG")
                directory_based_result = extract_date_from_file(file_path)
                MediLink_ConfigLoader.log("Directory-Based Extraction Result: {}".format(directory_based_result), level="DEBUG")
            else:
                MediLink_ConfigLoader.log("Target text 'Surgery Schedule' not found in any XML files.", level="WARNING")
        except zipfile.BadZipFile as e:
            MediLink_ConfigLoader.log("BadZipFile Error opening DOCX file {}: {}".format(docx_path, e), level="ERROR")
        except Exception as e:
            MediLink_ConfigLoader.log("Error opening DOCX file {}: {}".format(docx_path, e), level="ERROR")
        
        # TIMING: End directory-based extraction
        dir_extraction_end = time.time()
        dir_extraction_duration = dir_extraction_end - dir_extraction_start

    # In-Memory Extraction  // Single-Pass Processing is typically more efficient in terms of both time and memory compared to list creation for header isolation.
    if use_in_memory:  # Only perform in-memory extraction if selected
        # TIMING: Start in-memory extraction
        mem_extraction_start = time.time()
        
        try:
            with zipfile.ZipFile(docx_path, 'r') as docx:
                MediLink_ConfigLoader.log("Opened DOCX file for In-Memory extraction: {}".format(docx_path), level="DEBUG")
                xml_files_processed = 0
                for file_info in docx.infolist():
                    if file_info.filename.endswith('.xml'):
                        xml_files_processed += 1
                        MediLink_ConfigLoader.log("Processing XML file in-memory: {}".format(file_info.filename), level="DEBUG")
                        with docx.open(file_info) as file:
                            try:
                                xml_content = file.read()  # Read the entire XML content
                                MediLink_ConfigLoader.log("Read XML content from {}".format(file_info.filename), level="DEBUG")
                                if "Surgery Schedule" in xml_content.decode('utf-8', errors='ignore'):
                                    MediLink_ConfigLoader.log("Found 'Surgery Schedule' in file: {}".format(file_info.filename), level="DEBUG")
                                    in_memory_result = extract_date_from_content(xml_content)
                                    MediLink_ConfigLoader.log("In-Memory Extraction Result from {}: {}".format(file_info.filename, in_memory_result), level="DEBUG")
                                    break  # Stop after finding the first relevant file
                            except Exception as e:
                                MediLink_ConfigLoader.log("Error parsing XML file {} (In-Memory): {}".format(file_info.filename, e), level="ERROR")
                
                if in_memory_result is None:
                    MediLink_ConfigLoader.log("Target text 'Surgery Schedule' not found in any XML files (In-Memory).", level="WARNING")
        except zipfile.BadZipFile as e:
            MediLink_ConfigLoader.log("BadZipFile Error opening DOCX file for In-Memory extraction {}: {}".format(docx_path, e), level="ERROR")
        except Exception as e:
            MediLink_ConfigLoader.log("Error during In-Memory extraction of DOCX file {}: {}".format(docx_path, e), level="ERROR")
        
        # TIMING: End in-memory extraction
        mem_extraction_end = time.time()
        mem_extraction_duration = mem_extraction_end - mem_extraction_start

    # Clean up the extracted directory if it exists
    try:
        if os.path.exists(extract_to):
            remove_directory(extract_to)
            MediLink_ConfigLoader.log("Cleaned up extracted files in: {}".format(extract_to), level="DEBUG")
    except Exception as e:
        MediLink_ConfigLoader.log("Error cleaning up extraction directory {}: {}".format(extract_to, e), level="ERROR")

    # TIMING: End total extraction process
    extraction_end_time = time.time()
    total_extraction_duration = extraction_end_time - extraction_start_time
    
    # Log timing details for slow extractions (more than 0.2 seconds)
    if total_extraction_duration > 0.2:
        print("      - Date extraction timing:")
        if not use_in_memory and 'dir_extraction_duration' in locals():
            print("        * Directory-based: {:.3f}s".format(dir_extraction_duration))
        if use_in_memory and 'mem_extraction_duration' in locals():
            print("        * In-memory: {:.3f}s ({} XML files)".format(mem_extraction_duration, xml_files_processed if 'xml_files_processed' in locals() else 0))
        print("        * Total: {:.3f}s".format(total_extraction_duration))

    # Decide which result to return (prefer in-memory if available)
    if in_memory_result:
        return in_memory_result
    elif directory_based_result:
        return directory_based_result
    else:
        return None

def find_text_in_xml(extract_dir, target_text):
    target_pattern = re.compile(re.escape(target_text), re.IGNORECASE)
    for root_dir, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.xml') and file != '[Content_Types].xml':  # Skip Content_Types.xml
                file_path = os.path.join(root_dir, file)
                try:
                    tree = etree.parse(file_path)
                    root = tree.getroot()
                    collected_text = []
                    
                    # Prefer dynamic namespace detection; fall back to the XP-safe hardcoded URI.
                    nsmap = root.nsmap or {}
                    detected_w_ns = nsmap.get('w')
                    hardcoded_w_ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                    effective_w_ns = detected_w_ns or hardcoded_w_ns
                    namespaces = {'w': effective_w_ns}
                    
                    # Log the namespace choice to verify behavior without changing functionality.
                    MediLink_ConfigLoader.log(
                        "DOCX namespace resolution: detected='{}', using='{}', matches_hardcoded={}".format(
                            detected_w_ns, effective_w_ns, str(effective_w_ns == hardcoded_w_ns)
                        ),
                        level="INFO"
                    )
                    
                    for elem in root.xpath('//w:t', namespaces=namespaces):
                        if elem.text:
                            collected_text.append(elem.text.strip())
                    combined_text = ' '.join(collected_text)
                    if target_pattern.search(combined_text):
                        MediLink_ConfigLoader.log("Found target text '{}' in file: {}".format(target_text, file_path), level="DEBUG")
                        return file_path
                except etree.XMLSyntaxError as e:
                    MediLink_ConfigLoader.log("XMLSyntaxError parsing file {}: {}".format(file_path, e), level="ERROR")
                except Exception as e:
                    MediLink_ConfigLoader.log("Error parsing XML file {}: {}".format(file_path, e), level="ERROR")
    MediLink_ConfigLoader.log("Target text '{}' not found in any XML files within directory: {}".format(target_text, extract_dir), level="WARNING")
    return None

def extract_date_from_file(file_path):
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        collected_text = []
        
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}  # Hardcoded for XP handling BUG
        for elem in root.xpath('//w:t', namespaces=namespaces):
            if elem.text:
                collected_text.append(elem.text.strip())
        
        combined_text = ' '.join(collected_text)
        combined_text = reassemble_year(combined_text)  # Fix OCR splitting years
        combined_text = normalize_text(combined_text)  # Normalize abbreviations
        combined_text = reassemble_day(combined_text)   # Fix split day digits (e.g., '1 1' -> '11')
        combined_text = _COMMA_PATTERN.sub('', combined_text)  # Remove commas if they exist

        # Log the combined text
        MediLink_ConfigLoader.log("Combined text from file '{}': {}".format(file_path, combined_text[:200]), level="DEBUG")
        
        day_of_week = _DAY_WEEK_PATTERN.search(combined_text, re.IGNORECASE)
        month_day = _MONTH_DAY_PATTERN.search(combined_text, re.IGNORECASE)
        year_match = _YEAR_PATTERN.search(combined_text, re.IGNORECASE)

        # Log the results of the regex searches
        MediLink_ConfigLoader.log("Day of week found: {}".format(day_of_week.group() if day_of_week else 'None'), level="DEBUG")
        MediLink_ConfigLoader.log("Month and day found: {}".format(month_day.group() if month_day else 'None'), level="DEBUG")
        MediLink_ConfigLoader.log("Year found: {}".format(year_match.group() if year_match else 'None'), level="DEBUG")
        
        if day_of_week and month_day and year_match:
            date_str = "{} {} {}".format(day_of_week.group(), month_day.group(), year_match.group())
            try:
                date_obj = datetime.strptime(date_str, '%A %B %d %Y')
                extracted_date = date_obj.strftime('%m-%d-%Y')
                MediLink_ConfigLoader.log("Extracted date: {}".format(extracted_date), level="DEBUG")
                return extracted_date
            except ValueError as e:
                MediLink_ConfigLoader.log("Error converting date: {}. Error: {}".format(date_str, e), level="ERROR")
        else:
            MediLink_ConfigLoader.log(
                "Date components not found or incomplete. Combined text: '{}', Day of week: {}, Month and day: {}, Year: {}".format(
                    combined_text,
                    day_of_week.group() if day_of_week else 'None',
                    month_day.group() if month_day else 'None',
                    year_match.group() if year_match else 'None'
                ), level="WARNING"
            )
    except etree.XMLSyntaxError as e:
        MediLink_ConfigLoader.log("XMLSyntaxError in extract_date_from_file '{}': {}".format(file_path, e), level="ERROR")
    except Exception as e:
        MediLink_ConfigLoader.log("Error extracting date from file '{}': {}".format(file_path, e), level="ERROR")

    return None


def extract_date_from_content(xml_content):
    try:
        # Parse the XML content into an ElementTree
        tree = etree.fromstring(xml_content)
        root = tree  # root is already the root element in this case
        collected_text = []

        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        MediLink_ConfigLoader.log("Using namespaces: {}".format(namespaces), level="DEBUG")

        # Extract text from all <w:t> elements
        for elem in root.xpath('//w:t', namespaces=namespaces):
            if elem.text:
                collected_text.append(elem.text.strip())

        # Log the collected text snippets
        MediLink_ConfigLoader.log("Collected text snippets: {}".format(collected_text), level="DEBUG")

        combined_text = ' '.join(collected_text)
        combined_text = reassemble_year(combined_text)  # Fix OCR splitting years
        combined_text = normalize_text(combined_text)    # Normalize abbreviations
        combined_text = reassemble_day(combined_text)   # Fix split day digits (e.g., '1 1' -> '11')
        combined_text = _COMMA_PATTERN.sub('', combined_text)   # Remove commas if they exist

        # Log the combined text
        MediLink_ConfigLoader.log("Combined text: {}".format(combined_text[:200]), level="DEBUG")  # Log first 200 characters

        day_of_week = _DAY_WEEK_PATTERN.search(combined_text, re.IGNORECASE)
        month_day = _MONTH_DAY_PATTERN.search(combined_text, re.IGNORECASE)
        year_match = _YEAR_PATTERN.search(combined_text, re.IGNORECASE)

        MediLink_ConfigLoader.log("Day of week found: {}".format(day_of_week.group() if day_of_week else 'None'), level="DEBUG")
        MediLink_ConfigLoader.log("Month and day found: {}".format(month_day.group() if month_day else 'None'), level="DEBUG")
        MediLink_ConfigLoader.log("Year found: {}".format(year_match.group() if year_match else 'None'), level="DEBUG")

        if day_of_week and month_day and year_match:
            date_str = "{} {} {}".format(day_of_week.group(), month_day.group(), year_match.group())
            try:
                date_obj = datetime.strptime(date_str, '%A %B %d %Y')
                extracted_date = date_obj.strftime('%m-%d-%Y')
                MediLink_ConfigLoader.log("Extracted date: {}".format(extracted_date), level="DEBUG")
                return extracted_date
            except ValueError as e:
                MediLink_ConfigLoader.log("Error converting date: {}. Error: {}".format(date_str, e), level="ERROR")
        else:
            MediLink_ConfigLoader.log(
                "Date components not found or incomplete. Combined text: '{}', Day of week: {}, Month and day: {}, Year: {}".format(
                    combined_text,
                    day_of_week.group() if day_of_week else 'None',
                    month_day.group() if month_day else 'None',
                    year_match.group() if year_match else 'None'
                ), level="WARNING"
            )
    except etree.XMLSyntaxError as e:
        MediLink_ConfigLoader.log("XMLSyntaxError in extract_date_from_content: {}".format(e), level="ERROR")
    except Exception as e:
        MediLink_ConfigLoader.log("Error extracting date from content: {}".format(e), level="ERROR")

    return None


def remove_directory(path):
    if os.path.exists(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                    MediLink_ConfigLoader.log("Removed file: {}".format(os.path.join(root, name)), level="DEBUG")
                except Exception as e:
                    MediLink_ConfigLoader.log("Error removing file {}: {}".format(os.path.join(root, name), e), level="ERROR")
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                    MediLink_ConfigLoader.log("Removed directory: {}".format(os.path.join(root, name)), level="DEBUG")
                except Exception as e:
                    MediLink_ConfigLoader.log("Error removing directory {}: {}".format(os.path.join(root, name), e), level="ERROR")
        try:
            os.rmdir(path)
            MediLink_ConfigLoader.log("Removed extraction root directory: {}".format(path), level="DEBUG")
        except Exception as e:
            MediLink_ConfigLoader.log("Error removing root directory {}: {}".format(path, e), level="ERROR")


def reassemble_day(text):
    """
    Handles cases where the day of the month is split into two single digits,
    e.g., 'DECEMBER 1 1' -> 'DECEMBER 11'.
    Uses the pre-compiled _DAY_SPLIT_REASSEMBLY_PATTERN for performance.
    """
    return _DAY_SPLIT_REASSEMBLY_PATTERN.sub(r'\1 \2\3', text)


def normalize_text(text):
    # Optimized single-pass processing to avoid O(n2) complexity
    # Process all abbreviations in one pass instead of multiple regex calls
    for abbr, pattern in _MONTH_ABBR_PATTERNS.items():
        text = pattern.sub(_MONTH_MAP[abbr], text)
    for abbr, pattern in _DAY_ABBR_PATTERNS.items():
        text = pattern.sub(_DAY_MAP[abbr], text)
    
    return text


def reassemble_year(text):
    # Optimized year reassembly with early exit conditions
    # First, handle the most common cases with pre-compiled patterns
    for pattern in _YEAR_SPLIT_PATTERNS:
        text = pattern.sub(r'\1\2', text)
    
    # Handle the less common cases where the year might be split as (1,1,2) or (2,1,1) or (1,2,1)
    parts = _DIGIT_PARTS_PATTERN.findall(text)
    parts_len = len(parts)
    if parts_len >= 4:
        # PERFORMANCE FIX: Use direct indexing instead of range(len()) pattern
        max_index = parts_len - 3
        for i in range(max_index):
            candidate = ''.join(parts[i:i + 4])
            if len(candidate) == 4 and candidate.isdigit():
                # More efficient pattern construction
                pattern_parts = [r'\b' + part + r'\b' for part in parts[i:i + 4]]
                pattern = r'\s+'.join(pattern_parts)
                text = re.sub(pattern, candidate, text)
                break  # Early exit after first successful combination
    
    return text


def parse_patient_id(text):
    try:
        return text.split()[0].lstrip('#')  # Extract patient ID number (removing the '#')
    except Exception as e:
        MediLink_ConfigLoader.log("Error parsing patient ID: {}. Error: {}".format(text, e), level="ERROR")
        return None


def parse_diagnosis_code(text):
    try:
        # Use pre-compiled pattern for better performance
        matches = _DIAGNOSIS_CODE_PATTERN.findall(text)
        
        if matches:
            return matches[0]  # Return the first match
        else:
            # Fallback to original method if no match is found
            if '(' in text and ')' in text:  # Extract the diagnosis code before the '/'
                full_code = text[text.index('(')+1:text.index(')')]
                return full_code.split('/')[0]
            return text.split('/')[0]
    
    except Exception as e:
        MediLink_ConfigLoader.log("Error parsing diagnosis code: {}. Error: {}".format(text, e), level="ERROR")
        return "Unknown"


def parse_left_or_right_eye(text):
    try:
        if 'LEFT EYE' in text.upper():
            return 'Left'
        elif 'RIGHT EYE' in text.upper():
            return 'Right'
        else:
            return 'Unknown'
    except Exception as e:
        MediLink_ConfigLoader.log("Error parsing left or right eye: {}. Error: {}".format(text, e), level="ERROR")
        return 'Unknown'


def parse_femto_yes_or_no(text):
    try:
        if 'FEMTO' in text.upper():
            return True
        else:
            return False
    except Exception as e:
        MediLink_ConfigLoader.log("Error parsing femto yes or no: {}. Error: {}".format(text, e), level="ERROR")
        return False


def rotate_docx_files(directory, surgery_dates=None):
    """
    Process all DOCX files in the specified directory that contain "DR" and "SS" in their filename.
    
    Parameters:
    - directory (str): Path to the directory containing DOCX files
    - surgery_dates (set, optional): Set of surgery dates to filter by. 
                                     If None or empty, the script will skip documents 
                                     that don't match its internal date header.
    
    Returns:
    - dict: Combined patient data from all processed files
    """
    # PERFORMANCE OPTIMIZATION: Use os.listdir() for more efficient file system operations
    # This reduces the number of file system calls and improves performance with large directories
    valid_files = []
    try:
        # Use os.listdir() for better performance (XP/3.4.4 compatible)
        for filename in os.listdir(directory):
            # Filter files that contain "DR" and "SS" in the filename
            if (filename.endswith('.docx') and 
                "DR" in filename and 
                "SS" in filename):
                filepath = os.path.join(directory, filename)
                valid_files.append(filepath)
    except OSError as e:
        print("Error accessing directory '{}': {}".format(directory, e))
        return {}

    if not valid_files:
        print("No valid DOCX files found in directory: {}".format(directory))
        return {}

    # Initialize combined patient data dictionary
    combined_patient_data = {}
    
    # Ensure surgery_dates is a set for strict validation in batch mode
    # This prevents accidental bypassing of the date check when processing a directory
    strict_dates = surgery_dates if surgery_dates is not None else set()
    
    # Process each valid DOCX file
    for filepath in valid_files:
        filename = os.path.basename(filepath)  # Extract filename for display
        print("Processing file: {}".format(filename))
        
        try:
            # Parse the document with strict_dates parameter
            patient_data_dict = parse_docx(filepath, surgery_dates=strict_dates)
            
            # Combine patient data from this file with overall results
            for patient_id, service_dates in patient_data_dict.items():
                if patient_id not in combined_patient_data:
                    combined_patient_data[patient_id] = {}
                combined_patient_data[patient_id].update(service_dates)
            
            # Print results for this file
            print("Data from file '{}':".format(filename))
            pprint.pprint(patient_data_dict)
            print()
            
        except Exception as e:
            print("Error processing file '{}': {}".format(filename, e))
            MediLink_ConfigLoader.log("Error processing DOCX file '{}': {}".format(filepath, e), level="ERROR")
            continue  # Continue with next file instead of crashing

    return combined_patient_data


def main():
    # Upgrade: Handle command line arguments for single file processing
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if os.path.isfile(filepath) and filepath.lower().endswith('.docx'):
            print("Processing single file: {}".format(filepath))
            # Call parse_docx with surgery_dates=None to bypass the validation check
            try:
                patient_data = parse_docx(filepath, surgery_dates=None)
                print("\nExtracted Patient Data:")
                pprint.pprint(patient_data)
                
                if not patient_data:
                    print("\nNo patient data found in file or date extraction failed.")
            except Exception as e:
                print("Error processing file '{}': {}".format(filepath, e))
        else:
            if not os.path.isfile(filepath):
                print("Error: File not found: {}".format(filepath))
            else:
                print("Error: File is not a .docx file: {}".format(filepath))
    else:
        # Fallback to directory rotation if no arguments provided
        # Call the function with the directory containing your .docx files
        directory = "C:\\Users\\danie\\Downloads\\"
        # Note: surgery_dates parameter is now optional
        rotate_docx_files(directory)


if __name__ == "__main__":
    main()