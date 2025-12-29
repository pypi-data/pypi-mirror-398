"""
MediCafe Smart Import System

This module provides intelligent import management for the entire MediCafe ecosystem,
allowing MediBot and MediLink modules to request components without worrying about
circular imports or complex dependency management.

Usage Examples:
    # Simple component requests
    from MediCafe.smart_import import get_components
    api_core, logging_config = get_components('api_core', 'logging_config')
    
    # Get everything for a specific module type
    from MediCafe.smart_import import setup_for_medibot
    components = setup_for_medibot('preprocessor')
    
    # Use components
    api_core = components['api_core']
    logging = components['logging_config']
    
    # Get API suite for any module
    from MediCafe.smart_import import get_api_access
    api_suite = get_api_access()
"""

import sys
import importlib
import inspect
# from typing import Any, Dict, List, Optional, Union, Tuple, Set  # Removed for Python 3.4.4 compatibility
# from functools import lru_cache  # Removed as not used
import threading
# from pathlib import Path  # Replaced with os.path for Python 3.4.4 compatibility
import os
import warnings

# Define typing aliases for Python 3.4.4 compatibility
# Removed typing import to prevent subscriptable type errors in Python 3.4
# from typing import Any, Dict, List, Optional, Union, Tuple, Set  # Removed for Python 3.4.4 compatibility

# Python 3.4.4 compatibility - define as basic types
Any = object
Dict = dict
List = list
Optional = object
Union = object
Tuple = tuple
Set = set

class ComponentRegistry:
    """Registry for managing all available components and their dependencies."""
    
    def __init__(self):
        self._components = {}
        self._modules = {}
        self._dependencies = {}
        self._loading_stack = []
        self._lock = threading.RLock()
        self._module_configs = {}
        self._failed_loads = set()
        
    def register_component(self, name, component, dependencies=None):
        """Register a component with optional dependencies."""
        with self._lock:
            self._components[name] = component
            self._dependencies[name] = dependencies or []
            
    def register_module_config(self, module_name, config):
        """Register configuration for a specific module's needs."""
        self._module_configs[module_name] = config
        
    def get_component(self, name, silent_fail=False):
        """Get a component, loading it if necessary."""
        with self._lock:
            # Return cached component if available
            if name in self._components:
                return self._components[name]
            
            # Skip if previously failed and silent_fail is True
            if silent_fail and name in self._failed_loads:
                return None
            
            # Check for circular imports
            if name in self._loading_stack:
                error_msg = "Circular import detected: {} -> {}".format(' -> '.join(self._loading_stack), name)
                if silent_fail:
                    warnings.warn(error_msg)
                    return None
                raise ImportError(error_msg)
            
            self._loading_stack.append(name)
            try:
                component = self._load_component(name)
                self._components[name] = component
                return component
            except ImportError as e:
                self._failed_loads.add(name)
                if silent_fail:
                    return None
                raise e
            finally:
                if name in self._loading_stack:
                    self._loading_stack.remove(name)
                
    def _load_component(self, name: str) -> Any:
        """Load a component dynamically."""
        # Component loading mappings
        component_mappings = {
            # MediCafe core components
            'api_core': 'MediCafe.api_core',
            'api_factory': 'MediCafe.api_factory', 
            'api_utils': 'MediCafe.api_utils',
            'core_utils': 'MediCafe.core_utils',
            'graphql_utils': 'MediCafe.graphql_utils',
            'logging_config': 'MediCafe.logging_config',
            'medicafe_config_loader': 'MediCafe.MediLink_ConfigLoader',
            'launcher': 'MediCafe.launcher',
            
            # MediBot components
            'medibot_main': 'MediBot.MediBot',
            'medibot_preprocessor': 'MediBot.MediBot_Preprocessor',
            'medibot_preprocessor_lib': 'MediBot.MediBot_Preprocessor_lib',
            'medibot_crosswalk_library': 'MediBot.MediBot_Crosswalk_Library',
            'medibot_crosswalk_utils': 'MediBot.MediBot_Crosswalk_Utils',
            'medibot_dataformat_library': 'MediBot.MediBot_dataformat_library',
            'medibot_docx_decoder': 'MediBot.MediBot_docx_decoder',
            'medibot_ui': 'MediBot.MediBot_UI',
            'medibot_charges': 'MediBot.MediBot_Charges',
            'medibot_post': 'MediBot.MediBot_Post',
            'get_medicafe_version': 'MediBot.get_medicafe_version',
            'update_medicafe': 'MediBot.update_medicafe',
            'update_json': 'MediBot.update_json',
            
            # MediLink components
            'medilink_main': 'MediLink.MediLink_main',
            'medilink_azure': 'MediLink.MediLink_Azure',
            'medilink_claim_status': 'MediLink.MediLink_ClaimStatus',
            'medilink_datamgmt': 'MediLink.MediLink_DataMgmt',
            'medilink_decoder': 'MediLink.MediLink_Decoder',
            'medilink_deductible': 'MediLink.MediLink_Deductible',
            'medilink_deductible_validator': 'MediLink.MediLink_Deductible_Validator',
            'medilink_display_utils': 'MediLink.MediLink_Display_Utils',
            'medilink_down': 'MediLink.MediLink_Down',
            'medilink_gmail': 'MediLink.MediLink_Gmail',
            'medilink_mailer': 'MediLink.MediLink_Mailer',
            'medilink_parser': 'MediLink.MediLink_Parser',
            'medilink_patient_processor': 'MediLink.MediLink_PatientProcessor',
            'medilink_scan': 'MediLink.MediLink_Scan',
            'medilink_scheduler': 'MediLink.MediLink_Scheduler',
            'medilink_ui': 'MediLink.MediLink_UI',
            'medilink_up': 'MediLink.MediLink_Up',
            'medilink_insurance_utils': 'MediLink.MediLink_insurance_utils',
            'medilink_charges': 'MediLink.MediLink_Charges',
            'medilink_837p_cob_library': 'MediLink.MediLink_837p_cob_library',
            'medilink_837p_encoder': 'MediLink.MediLink_837p_encoder',
            'medilink_837p_encoder_library': 'MediLink.MediLink_837p_encoder_library',
            'medilink_837p_utilities': 'MediLink.MediLink_837p_utilities',
            'medilink_api_generator': 'MediLink.MediLink_API_Generator',
            'soumit_api': 'MediLink.Soumit_api',
        }
        
        if name not in component_mappings:
            raise ImportError("Unknown component: {}. Available components: {}".format(name, list(component_mappings.keys())))
            
        module_path = component_mappings[name]
        try:
            module = importlib.import_module(module_path)
            
            # Special handling for components that may fail due to missing config files
            if name in ['api_core', 'logging_config', 'core_utils']:
                try:
                    # Test if the module can initialize properly
                    if hasattr(module, 'load_configuration'):
                        # This will use our new graceful fallback
                        module.load_configuration()
                except Exception as config_error:
                    # Log the config error but don't fail the import
                    warnings.warn("Component '{}' loaded but configuration failed: {}".format(name, config_error))
            
            return module
        except ImportError as e:
            raise ImportError("Failed to load component '{}' from '{}': {}".format(name, module_path, e))

# Global registry instance
_registry = ComponentRegistry()

class ComponentProvider:
    """Main interface for requesting components."""
    
    def __init__(self, registry: ComponentRegistry):
        self.registry = registry
        self._setup_module_configs()
        
    def _setup_module_configs(self):
        """Setup predefined configurations for known module types."""
        configs = {
            # MediBot configurations
            'medibot_preprocessor': {
                'core_dependencies': ['api_core', 'logging_config', 'core_utils'],
                'optional_dependencies': ['api_factory', 'api_utils'],
                'shared_resources': ['medibot_dataformat_library', 'medibot_crosswalk_utils']
            },
            'medibot_ui': {
                'core_dependencies': ['medibot_main', 'logging_config'],
                'optional_dependencies': ['core_utils', 'api_core'],
                'shared_resources': ['medibot_preprocessor', 'medibot_crosswalk_library']
            },
            'medibot_crosswalk': {
                'core_dependencies': ['logging_config', 'core_utils'],
                'optional_dependencies': ['api_core'],
                'shared_resources': ['medibot_crosswalk_library', 'medibot_crosswalk_utils', 'medibot_dataformat_library']
            },
            'medibot_document_processing': {
                'core_dependencies': ['logging_config', 'core_utils'],
                'optional_dependencies': ['api_core'],
                'shared_resources': ['medibot_docx_decoder', 'medibot_preprocessor_lib']
            },
            
            # MediLink configurations
            'medilink_main': {
                'core_dependencies': ['api_core', 'logging_config', 'core_utils'],
                'optional_dependencies': ['api_factory', 'graphql_utils'],
                'shared_resources': ['medilink_datamgmt', 'medilink_parser']
            },
            'medilink_claim_processing': {
                'core_dependencies': ['api_core', 'logging_config', 'medilink_datamgmt'],
                'optional_dependencies': ['graphql_utils', 'api_utils'],
                'shared_resources': ['medilink_837p_encoder', 'medilink_837p_utilities', 'medilink_claim_status', 'medilink_charges']
            },
            'medilink_deductible_processing': {
                'core_dependencies': ['api_core', 'logging_config', 'medilink_datamgmt'],
                'optional_dependencies': ['graphql_utils'],
                'shared_resources': ['medilink_deductible', 'medilink_deductible_validator', 'medilink_insurance_utils']
            },
            'medilink_communication': {
                'core_dependencies': ['logging_config', 'core_utils'],
                'optional_dependencies': ['api_core'],
                'shared_resources': ['medilink_gmail', 'medilink_mailer', 'medilink_display_utils']
            },
            'medilink_data_management': {
                'core_dependencies': ['api_core', 'logging_config'],
                'optional_dependencies': ['graphql_utils'],
                'shared_resources': ['medilink_datamgmt', 'medilink_up', 'medilink_down', 'medilink_parser']
            },
            
            # General configurations
            'general_api_access': {
                'core_dependencies': ['api_core', 'api_factory'],
                'optional_dependencies': ['api_utils', 'graphql_utils'],
                'shared_resources': ['logging_config', 'core_utils']
            },
            'logging_only': {
                'core_dependencies': ['logging_config'],
                'optional_dependencies': [],
                'shared_resources': []
            },
            'utilities_only': {
                'core_dependencies': ['core_utils'],
                'optional_dependencies': ['api_utils'],
                'shared_resources': ['logging_config']
            }
        }
        
        for module_name, config in configs.items():
            self.registry.register_module_config(module_name, config)
    
    def __call__(self, *component_names, **kwargs):
        """Get one or more components by name."""
        silent_fail = kwargs.get('silent_fail', False)
        if len(component_names) == 1:
            return self.registry.get_component(component_names[0], silent_fail=silent_fail)
        
        results = []
        for name in component_names:
            component = self.registry.get_component(name, silent_fail=silent_fail)
            results.append(component)
        return tuple(results)
    
    def for_module(self, module_type, silent_fail=False):
        """Get all components needed for a specific module type."""
        if module_type not in self.registry._module_configs:
            available_types = list(self.registry._module_configs.keys())
            raise ValueError("Unknown module type: {}. Available types: {}".format(module_type, available_types))
            
        config = self.registry._module_configs[module_type]
        components = {}
        
        # Load core dependencies (these must succeed unless silent_fail is True)
        for dep in config.get('core_dependencies', []):
            component = self.registry.get_component(dep, silent_fail=silent_fail)
            if component is not None:
                components[dep] = component
            
        # Load optional dependencies (always fail silently)
        for dep in config.get('optional_dependencies', []):
            try:
                component = self.registry.get_component(dep, silent_fail=True)
                if component is not None:
                    components[dep] = component
            except ImportError:
                pass
                
        # Load shared resources (always fail silently)
        for dep in config.get('shared_resources', []):
            try:
                component = self.registry.get_component(dep, silent_fail=True)
                if component is not None:
                    components[dep] = component
            except ImportError:
                pass
                
        return components
    
    def get_api_suite(self):
        """Get the complete API access suite."""
        return self.for_module('general_api_access')
    
    def get_medibot_suite(self, module_type='medibot_preprocessor'):
        """Get components specifically for MediBot operations."""
        return self.for_module(module_type)
    
    def get_medilink_suite(self, module_type='medilink_main'):
        """Get components specifically for MediLink operations."""
        return self.for_module(module_type)
    
    def list_available_components(self):
        """List all available component names."""
        # Get component mappings from registry's _load_component method
        component_mappings = {
            'api_core', 'api_factory', 'api_utils', 'core_utils', 'graphql_utils', 'logging_config',
            'medicafe_config_loader', 'medibot_main', 'medibot_preprocessor', 'medibot_preprocessor_lib',
            'medibot_crosswalk_library', 'medibot_crosswalk_utils', 'medibot_dataformat_library',
            'medibot_docx_decoder', 'medibot_ui', 'medibot_charges', 'medibot_post',
            'get_medicafe_version', 'update_medicafe', 'update_json', 'medilink_main',
            'medilink_azure', 'medilink_claim_status', 'medilink_datamgmt', 'medilink_decoder',
            'medilink_deductible', 'medilink_deductible_validator', 'medilink_display_utils',
            'medilink_down', 'medilink_gmail', 'medilink_mailer', 'medilink_parser',
            'medilink_patient_processor', 'medilink_scan', 'medilink_scheduler', 'medilink_ui',
            'medilink_up', 'medilink_insurance_utils', 'medilink_837p_cob_library',
            'medilink_837p_encoder', 'medilink_837p_encoder_library', 'medilink_837p_utilities',
            'medilink_api_generator', 'soumit_api'
        }
        return sorted(list(component_mappings))
    
    def list_available_module_types(self):
        """List all available module type configurations."""
        return sorted(list(self.registry._module_configs.keys()))

# Global component provider
get_components = ComponentProvider(_registry)

# Convenience functions for common use cases
def get_api_access():
    """Get standard API access components."""
    return get_components.get_api_suite()

def get_logging():
    """Get logging configuration."""
    return get_components('logging_config')

def get_core_utils():
    """Get core utilities."""
    return get_components('core_utils')

def setup_for_medibot(module_type: str = 'medibot_preprocessor'):
    """Setup everything needed for MediBot operations."""
    return get_components.get_medibot_suite(module_type)

def setup_for_medilink(module_type: str = 'medilink_main'):
    """Setup everything needed for MediLink operations."""
    return get_components.get_medilink_suite(module_type)

# Helper functions for discovery
def list_components():
    """List all available component names."""
    return get_components.list_available_components()

def list_module_types():
    """List all available module type configurations."""
    return get_components.list_available_module_types()

def describe_module_type(module_type: str):
    """Describe what components a module type provides."""
    if module_type in _registry._module_configs:
        config = _registry._module_configs[module_type]
        print("Module Type: {}".format(module_type))
        print("Core Dependencies: {}".format(config.get('core_dependencies', [])))
        print("Optional Dependencies: {}".format(config.get('optional_dependencies', [])))
        print("Shared Resources: {}".format(config.get('shared_resources', [])))
    else:
        print("Unknown module type: {}".format(module_type))
        print("Available types: {}".format(list_module_types()))

# Module initialization and validation
def validate_setup():
    """Validate that the import system is working correctly."""
    try:
        # Test core components
        logging_config = get_components('logging_config')
        core_utils = get_components('core_utils')
        
        print("[+] MediCafe Smart Import System initialized successfully")
        print("[+] Available components: {}".format(len(list_components())))
        print("[+] Available module types: {}".format(len(list_module_types())))
        return True
    except Exception as e:
        print("[-] MediCafe Smart Import System validation failed: {}".format(e))
        return False

# Advanced usage examples and documentation
def show_usage_examples():
    """Show usage examples for the smart import system."""
    examples = """
    MediCafe Smart Import System - Usage Examples
    
    1. Basic component import:
        from MediCafe.smart_import import get_components
        api_core, logging_config = get_components('api_core', 'logging_config')
    
    2. Setup for MediBot:
        from MediCafe.smart_import import setup_for_medibot
        components = setup_for_medibot('medibot_preprocessor')
        api_core = components['api_core']
    
    3. Setup for MediLink:
        from MediCafe.smart_import import setup_for_medilink
        components = setup_for_medilink('medilink_claim_processing')
        datamgmt = components['medilink_datamgmt']
    
    4. Get API access suite:
        from MediCafe.smart_import import get_api_access
        api_suite = get_api_access()
        api_core = api_suite['api_core']
        api_factory = api_suite['api_factory']
    
    5. Discovery functions:
        from MediCafe.smart_import import list_components, list_module_types
        print("Available components:", list_components())
        print("Available module types:", list_module_types())
    """
    print(examples)

# Auto-validation on import (silent)
if __name__ != '__main__':
    try:
        # Silent validation - don't print success messages on import
        logging_config = get_components('logging_config', silent_fail=True)
        if logging_config:
            pass  # Successfully validated
    except:
        pass  # Silent fail on import
