import re
from datetime import datetime

def log(message):
    print("LOG: {}".format(message))

def parse_837p_file(content):
    patient_details = []
    date_of_submission = None
    try:
    
        log("Parsing submitted 837p...")

        # Extract the submission date from the GS segment
        gs_match = re.search(r'GS\*HC\*[^*]*\*[^*]*\*([0-9]{8})\*([0-9]{4})', content)
        if gs_match:
            date = gs_match.group(1)
            time = gs_match.group(2)
            date_of_submission = datetime.strptime("{}{}".format(date, time), "%Y%m%d%H%M").strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Fallback to the current date and time if GS segment is not found
            date_of_submission = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Split content using 'SE*{count}*{control_number}~' as delimiter
        patient_records = re.split(r'SE\*\d+\*\d{4}~', content)
        
        # Remove any empty strings from list that may have been added from split
        patient_records = [record for record in patient_records if record.strip()]
        
        for record in patient_records:
            # Extract patient name
            name_match = re.search(r'NM1\*IL\*1\*([^*]+)\*([^*]+)\*([^*]*)', record)
            # Extract service date
            service_date_match = re.search(r'DTP\*472\D*8\*([0-9]{8})', record)
            # Extract claim amount
            amount_match = re.search(r'CLM\*[^\*]*\*([0-9]+\.?[0-9]*)', record)
            
            if name_match and service_date_match and amount_match:
                # Handle optional middle name
                middle_name = name_match.group(3).strip() if name_match.group(3) else ""
                patient_name = "{} {} {}".format(name_match.group(2), middle_name, name_match.group(1)).strip()
                service_date = "{}-{}-{}".format(service_date_match.group(1)[:4], service_date_match.group(1)[4:6], service_date_match.group(1)[6:])
                amount_billed = float(amount_match.group(1))
                
                patient_details.append({
                    "name": patient_name,
                    "service_date": service_date,
                    "amount_billed": amount_billed
                })
    except Exception as e:
        print("Error reading or parsing the 837p file: {0}".format(str(e)))
    
    # Optionally, return also date_of_submission as a separate variable  
    return patient_details, date_of_submission

# Mocked file content based on your provided sample data
file_content = """
GS*HC*ZCHC0113*OPTUM*20240414*1130*1*X*005010X222A1~
NM1*IL*1*BURLAP*CAROLINE*A***MI*995796519~
CLM*BURLO000032624*540.00***24:B:1*Y*A*Y*Y~
DTP*472*D8*20240328~
SE*26*0001~
NM1*IL*1*GAMORA*WHOIS*R***MI*987654307~
CLM*GAMOA000032824*450.00***24:B:1*Y*A*Y*Y~
DTP*472*D8*20240318~
SE*26*0002~
ST*837*0002*005010X222A1~
BHT*0019*00*GORJA000*20240414*1130*CH~
"""

# Run the function with the mocked content
parsed_details = parse_837p_file(file_content)
for detail in parsed_details:
    print(detail)
