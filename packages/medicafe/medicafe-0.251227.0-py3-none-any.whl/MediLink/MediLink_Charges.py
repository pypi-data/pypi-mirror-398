# MediLink_Charges.py
"""MediLink_Charges.py

Overview
--------
This module provides core charge calculation and bundling functionality for the MediLink system, with wrappers for MediBot integration. It handles medical billing charges for ophthalmology (cataract surgeries), calculating based on anesthesia minutes and supporting multi-eye bundling. Primary integration point is enrich_with_charges (via MediBot_Charges.py) called from MediBot.py before data_entry_loop.

Key Features
------------
- Tiered pricing with capping (>59 minutes caps at 59, with notification/log).
- Bundling for even costs across eyes; flags 'bundling_pending' if patient exists (via MediBot check_existing_patients) or diagnosis suggests bilateral.
- Read-only historical lookups (e.g., MATRAN) with user notifications for manual edits; never alters data.
- Deductible checks (placeholder; integrate with OptumAI via config).
- Refund processing for expired bundling (post-30 days).
- Interactive UI tie-in via MediBot_UI extensions for minutes input.

Pricing Structure (Private Insurance)
------------------------------------
Default tiered pricing based on procedure duration:
- $450 for 1-15 minutes
- $480 for 16-22 minutes  
- $510 for 23-27 minutes
- $540 for 28-37 minutes
- $580 for 38-59 minutes (maximum allowed duration)

Medicare pricing follows different rules and is configurable through the system.

Integration with MediLink
-------------------------
This module is designed to work with:
- MediLink_837p_encoder_library.py: For claim segment generation
- MediLink_DataMgmt.py: For patient and procedure data management
- MediLink_ClaimStatus.py: For charge tracking and status updates
- MediCafe smart import system: For modular loading

Usage
-----
The module can be used in several ways:
1. Direct charge calculation for individual procedures
2. Batch processing of multiple procedures with bundling
3. Integration with MediLink claim generation workflow
4. Charge validation and adjustment for existing claims

Example:
    from MediLink import MediLink_Charges
    
    # Calculate charge for a procedure
    charge_info = MediLink_Charges.calculate_procedure_charge(
        minutes=25, 
        insurance_type='private',
        procedure_code='66984'
    )
    
    # Bundle charges for bilateral procedures
    bundled_charges = MediLink_Charges.bundle_bilateral_charges(
        [charge_info_1, charge_info_2]
    )

Data Format
-----------
The module works with standardized charge data structures that are compatible with
837p claim requirements:
- Charge amounts in dollars and cents
- Procedure codes (CPT/HCPCS)
- Service dates and duration
- Insurance-specific modifiers
- Bundling and adjustment flags

Compatibility
-------------
- Python 3.4.4+ compatible
- ASCII-only character encoding
- Windows XP SP3 compatible
- No external dependencies beyond MediLink core modules

Author: MediLink Development Team
Version: 1.0.0
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

# Import centralized logging configuration
try:
    from MediCafe.logging_config import DEBUG, PERFORMANCE_LOGGING
except ImportError:
    # Fallback to local flags if centralized config is not available
    DEBUG = False
    PERFORMANCE_LOGGING = False

# Set up project paths
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Import MediLink core utilities
try:
    from MediCafe.core_utils import get_shared_config_loader
    MediLink_ConfigLoader = get_shared_config_loader()
except ImportError:
    print("Warning: Unable to import MediCafe.core_utils. Using fallback configuration.")
    MediLink_ConfigLoader = None

# Default pricing configuration for private insurance
DEFAULT_PRIVATE_PRICING_TIERS = [
    {'min_minutes': 1, 'max_minutes': 15, 'charge': Decimal('450.00')},
    {'min_minutes': 16, 'max_minutes': 34, 'charge': Decimal('540.00')},
    {'min_minutes': 35, 'max_minutes': 59, 'charge': Decimal('580.00')},
]

# Default Medicare pricing (placeholder - should be configured)
DEFAULT_MEDICARE_PRICING_TIERS = [
    {'min_minutes': 1, 'max_minutes': 30, 'charge': Decimal('300.00')},
    {'min_minutes': 31, 'max_minutes': 45, 'charge': Decimal('350.00')},
    {'min_minutes': 46, 'max_minutes': 59, 'charge': Decimal('400.00')},
]

class ChargeCalculationError(Exception):
    """Custom exception for charge calculation errors"""
    pass

class ChargeBundlingError(Exception):
    """Custom exception for charge bundling errors"""
    pass

class ChargeInfo:
    """
    Container class for charge information compatible with 837p requirements
    """
    def __init__(self, procedure_code='', service_date=None, minutes=0, 
                 base_charge=Decimal('0.00'), adjusted_charge=None, 
                 insurance_type='private', patient_id='', claim_id=''):
        self.procedure_code = procedure_code
        self.service_date = service_date or datetime.now().date()
        self.minutes = minutes
        self.base_charge = Decimal(str(base_charge))
        self.adjusted_charge = Decimal(str(adjusted_charge)) if adjusted_charge else self.base_charge
        self.insurance_type = insurance_type.lower()
        self.patient_id = patient_id
        self.claim_id = claim_id
        self.bundling_group = None  # For multi-procedure bundling
        self.adjustment_reason = None
        self.created_timestamp = datetime.now()
        self.flags = {}  # e.g., {'bundling_pending': True, 'Pending for Deductible': True}
        
    def to_dict(self):
        """Convert to dictionary format for 837p integration"""
        return {
            'procedure_code': self.procedure_code,
            'service_date': self.service_date.strftime('%Y%m%d') if self.service_date else '',
            'minutes': self.minutes,
            'base_charge': str(self.base_charge),
            'adjusted_charge': str(self.adjusted_charge),
            'insurance_type': self.insurance_type,
            'patient_id': self.patient_id,
            'claim_id': self.claim_id,
            'bundling_group': self.bundling_group,
            'adjustment_reason': self.adjustment_reason,
            'created_timestamp': self.created_timestamp.isoformat()
        }
        
    def to_837p_format(self):
        """Format charge data for 837p claim integration"""
        return {
            'charge_amount': str(self.adjusted_charge),
            'service_units': str(self.minutes),
            'procedure_code': self.procedure_code,
            'service_date': self.service_date.strftime('%Y%m%d') if self.service_date else '',
            'line_item_charge': str(self.adjusted_charge)
        }

def get_pricing_tiers(insurance_type='private'):
    """
    Get pricing tiers for the specified insurance type
    
    Args:
        insurance_type (str): Type of insurance ('private', 'medicare', etc.)
        
    Returns:
        list: List of pricing tier dictionaries
    """
    if DEBUG:
        print("Getting pricing tiers for insurance type: {}".format(insurance_type))
    
    # Try to load from configuration first
    if MediLink_ConfigLoader:
        try:
            config_tiers = MediLink_ConfigLoader.get('pricing_tiers', {}).get(insurance_type.lower())
            if config_tiers:
                return config_tiers
        except Exception as e:
            if DEBUG:
                print("Warning: Could not load pricing tiers from config: {}".format(e))
    
    # Fall back to default tiers
    if insurance_type.lower() == 'medicare':
        return DEFAULT_MEDICARE_PRICING_TIERS
    else:
        return DEFAULT_PRIVATE_PRICING_TIERS

def calculate_base_charge(minutes, insurance_type='private'):
    """
    Calculate base charge for a procedure based on minutes and insurance type
    
    Args:
        minutes (int): Duration of procedure in minutes
        insurance_type (str): Type of insurance
        
    Returns:
        Decimal: Calculated charge amount
        
    Raises:
        ChargeCalculationError: If minutes are invalid or no tier matches
    """
    if DEBUG:
        print("Calculating base charge for {} minutes, {} insurance".format(minutes, insurance_type))
    
    # Validate input
    if not isinstance(minutes, int) or minutes <= 0:
        raise ChargeCalculationError("Minutes must be a positive integer, got: {}".format(minutes))
    
    if minutes > 59:
        minutes = 59  # Cap at 59
        if MediLink_ConfigLoader:
            MediLink_ConfigLoader.log("Capped duration to 59 minutes", level="INFO")
        print("Confirm intended duration >59? (Rare case)")
    
    # Get pricing tiers for insurance type
    pricing_tiers = get_pricing_tiers(insurance_type)
    
    # Find matching tier
    for tier in pricing_tiers:
        if tier['min_minutes'] <= minutes <= tier['max_minutes']:
            charge = Decimal(str(tier['charge']))
            if DEBUG:
                print("Found matching tier: ${} for {} minutes".format(charge, minutes))
            return charge
    
    # No tier found
    raise ChargeCalculationError("No pricing tier found for {} minutes with {} insurance".format(
        minutes, insurance_type))

def calculate_procedure_charge(minutes, insurance_type='private', procedure_code='', 
                             service_date=None, patient_id='', claim_id=''):
    """
    Calculate complete charge information for a procedure
    
    Args:
        minutes (int): Duration of procedure in minutes
        insurance_type (str): Type of insurance
        procedure_code (str): CPT/HCPCS procedure code
        service_date (date): Date of service
        patient_id (str): Patient identifier
        claim_id (str): Claim identifier
        
    Returns:
        ChargeInfo: Complete charge information object
    """
    if DEBUG:
        print("Calculating procedure charge for patient {} claim {}".format(patient_id, claim_id))
    
    try:
        base_charge = calculate_base_charge(minutes, insurance_type)
        
        charge_info = ChargeInfo(
            procedure_code=procedure_code,
            service_date=service_date,
            minutes=minutes,
            base_charge=base_charge,
            insurance_type=insurance_type,
            patient_id=patient_id,
            claim_id=claim_id
        )
        
        if DEBUG:
            print("Created charge info: ${}".format(charge_info.base_charge))
        
        return charge_info
        
    except Exception as e:
        raise ChargeCalculationError("Failed to calculate procedure charge: {}".format(str(e)))

def bundle_bilateral_charges(charge_list, bundling_strategy='average'):
    """
    Bundle charges for bilateral procedures (e.g., both eyes)
    
    Args:
        charge_list (list): List of ChargeInfo objects to bundle
        bundling_strategy (str): Strategy for bundling ('average', 'total_split')
        
    Returns:
        list: List of ChargeInfo objects with adjusted charges
        
    Raises:
        ChargeBundlingError: If bundling fails
    """
    if DEBUG:
        print("Bundling {} charges using {} strategy".format(len(charge_list), bundling_strategy))
    
    if not charge_list or len(charge_list) < 2:
        if DEBUG:
            print("No bundling needed for {} charges".format(len(charge_list)))
        return charge_list
    
    try:
        if bundling_strategy == 'average':
            # Calculate average charge and apply to all procedures
            total_charge = sum(charge.base_charge for charge in charge_list)
            average_charge = total_charge / len(charge_list)
            # Round to nearest cent
            average_charge = average_charge.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            bundling_group = "bundle_{}".format(datetime.now().strftime('%Y%m%d_%H%M%S'))
            
            for charge in charge_list:
                charge.adjusted_charge = average_charge
                charge.bundling_group = bundling_group
                charge.adjustment_reason = "Bilateral procedure bundling - average"
                
                # Use MediBot's existing patient check to assume prior procedure if patient exists
                if MediLink_ConfigLoader and MediLink_ConfigLoader.get('MediBot', {}).get('Preprocessor'):
                    MediBot_Preprocessor = MediLink_ConfigLoader.get('MediBot', {}).get('Preprocessor')
                    if MediBot_Preprocessor.check_existing_patients([charge.patient_id])[0]:  # Exists, assume prior
                        charge.flags['bundling_pending'] = True
                
            if DEBUG:
                print("Applied average bundling: ${} per procedure".format(average_charge))
                
        elif bundling_strategy == 'total_split':
            # Split total evenly among procedures
            total_charge = sum(charge.base_charge for charge in charge_list)
            split_charge = total_charge / len(charge_list)
            split_charge = split_charge.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            bundling_group = "split_{}".format(datetime.now().strftime('%Y%m%d_%H%M%S'))
            
            for charge in charge_list:
                charge.adjusted_charge = split_charge
                charge.bundling_group = bundling_group
                charge.adjustment_reason = "Bilateral procedure bundling - total split"
                
            if DEBUG:
                print("Applied total split bundling: ${} per procedure".format(split_charge))
        else:
            raise ChargeBundlingError("Unknown bundling strategy: {}".format(bundling_strategy))
            
        return charge_list
        
    except Exception as e:
        raise ChargeBundlingError("Failed to bundle charges: {}".format(str(e)))

def validate_charge_data(charge_info):
    """
    Validate charge information for completeness and accuracy
    
    Args:
        charge_info (ChargeInfo): Charge information to validate
        
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    if not charge_info.procedure_code:
        errors.append("Procedure code is required")
    
    if not charge_info.patient_id:
        errors.append("Patient ID is required")
    
    if charge_info.minutes <= 0:
        errors.append("Minutes must be positive")
    
    if charge_info.minutes > 59:
        errors.append("Minutes cannot exceed 59")
    
    if charge_info.base_charge <= 0:
        errors.append("Base charge must be positive")
    
    if charge_info.adjusted_charge <= 0:
        errors.append("Adjusted charge must be positive")
    
    # Check insurance type
    valid_insurance_types = ['private', 'medicare', 'medicaid', 'commercial']
    if charge_info.insurance_type not in valid_insurance_types:
        errors.append("Invalid insurance type: {}".format(charge_info.insurance_type))
    
    # Check service date
    if charge_info.service_date and charge_info.service_date > datetime.now().date():
        errors.append("Service date cannot be in the future")
    
    is_valid = len(errors) == 0
    
    if DEBUG and not is_valid:
        print("Charge validation failed: {}".format("; ".join(errors)))
    
    return is_valid, errors

def format_charges_for_837p(charge_list):
    """
    Format charge information for 837p claim generation
    
    Args:
        charge_list (list): List of ChargeInfo objects
        
    Returns:
        list: List of 837p-formatted charge dictionaries
    """
    if DEBUG:
        print("Formatting {} charges for 837p".format(len(charge_list)))
    
    formatted_charges = []
    
    for charge in charge_list:
        # Validate charge first
        is_valid, errors = validate_charge_data(charge)
        if not is_valid:
            if DEBUG:
                print("Skipping invalid charge: {}".format("; ".join(errors)))
            continue
        
        formatted_charge = charge.to_837p_format()
        formatted_charges.append(formatted_charge)
    
    if DEBUG:
        print("Successfully formatted {} charges for 837p".format(len(formatted_charges)))
    
    return formatted_charges

# Utility functions for integration with other MediLink modules

def get_charge_summary(charge_list):
    """
    Get summary statistics for a list of charges
    
    Args:
        charge_list (list): List of ChargeInfo objects
        
    Returns:
        dict: Summary statistics
    """
    if not charge_list:
        return {
            'total_charges': Decimal('0.00'),
            'average_charge': Decimal('0.00'),
            'charge_count': 0,
            'bundled_count': 0,
            'insurance_breakdown': {}
        }
    
    total_charges = sum(charge.adjusted_charge for charge in charge_list)
    average_charge = total_charges / len(charge_list)
    bundled_count = sum(1 for charge in charge_list if charge.bundling_group)
    
    # Insurance type breakdown
    insurance_breakdown = {}
    for charge in charge_list:
        ins_type = charge.insurance_type
        if ins_type not in insurance_breakdown:
            insurance_breakdown[ins_type] = {'count': 0, 'total': Decimal('0.00')}
        insurance_breakdown[ins_type]['count'] += 1
        insurance_breakdown[ins_type]['total'] += charge.adjusted_charge
    
    return {
        'total_charges': total_charges,
        'average_charge': average_charge.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        'charge_count': len(charge_list),
        'bundled_count': bundled_count,
        'insurance_breakdown': insurance_breakdown
    }

def log_charge_activity(charge_info, activity_type='created'):
    """
    Log charge-related activity for audit purposes
    
    Args:
        charge_info (ChargeInfo): Charge information
        activity_type (str): Type of activity ('created', 'modified', 'bundled')
    """
    if DEBUG:
        log_message = "Charge {} for patient {} claim {}: ${} ({} min, {})".format(
            activity_type,
            charge_info.patient_id,
            charge_info.claim_id,
            charge_info.adjusted_charge,
            charge_info.minutes,
            charge_info.insurance_type
        )
        print("[CHARGE_LOG] {}".format(log_message))

# Add historical lookup prototype
def lookup_historical_charges(patient_id, procedure_codes, date_range):
    # Read-only MATRAN parse (TBD format)
    # Prototype: Return mock priors
    priors = []  # List of ChargeInfo
    if priors:
        print("Edit MATRAN for {} - Adjust prior from {} to {} for bundling".format(patient_id, priors[0].base_charge, 'new_value'))
    return priors

# Add deductible check
def check_deductible_unmet(charge_info):
    # Prototype: External check
    return True  # Flag as Pending if True

# Add refund logic for expired bundling
def process_refund_if_expired(charge_info):
    if charge_info.flags.get('bundling_pending') and (datetime.now() - charge_info.service_date).days > 30:
        # Prototype refund
        print("Process refund for expired bundling: {}".format(charge_info.patient_id))

# Module initialization
if __name__ == "__main__":
    print("MediLink_Charges.py - Medical Billing Charge Calculation Module")
    print("Version 1.0.0")
    print("For integration with MediLink 837p claim generation system")