"""
MediCafe Migration Helpers

This module provides tools to help migrate existing MediBot and MediLink modules
to use the new MediCafe smart import system. It includes analysis tools,
migration utilities, and validation functions.

Usage:
    # Analyze a module's imports
    from MediCafe.migration_helpers import analyze_module_imports
    analysis = analyze_module_imports('MediBot/MediBot.py')
    
    # Generate migration suggestions
    from MediCafe.migration_helpers import suggest_migration
    suggestions = suggest_migration('MediBot/MediBot.py')
    
    # Validate smart import system
    from MediCafe.migration_helpers import validate_smart_import_system
    validate_smart_import_system()
"""

import os
import re
import ast
import importlib
# from typing import Dict, List, Tuple, Optional, Set, Any  # Removed for Python 3.4.4 compatibility
# from pathlib import Path  # Replaced with os.path for Python 3.4.4 compatibility
import warnings

def analyze_module_imports(file_path):
    """Analyze the import statements in a Python module."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return {'error': 'File not found: {}'.format(file_path)}
    except Exception as e:
        return {'error': 'Error reading file: {}'.format(e)}
    
    # Parse imports using AST
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return {'error': 'Syntax error in file: {}'.format(e)}
    
    imports = {
        'standard_library': [],
        'third_party': [],
        'medicafe_imports': [],
        'medibot_imports': [],
        'medilink_imports': [],
        'relative_imports': [],
        'other_imports': []
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                imports = _categorize_import(module_name, imports)
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ''
            level = node.level
            
            if level > 0:  # Relative import
                imports['relative_imports'].append({
                    'module': module_name,
                    'names': [alias.name for alias in node.names],
                    'level': level
                })
            else:
                imports = _categorize_import(module_name, imports, node.names)
    
    # Count imports by category
    import_counts = {key: len(value) for key, value in imports.items()}
    
    # Suggest smart import alternatives
    smart_import_suggestions = _generate_smart_import_suggestions(imports)
    
    return {
        'file_path': file_path,
        'imports': imports,
        'import_counts': import_counts,
        'smart_import_suggestions': smart_import_suggestions,
        'migration_complexity': _assess_migration_complexity(imports)
    }

def _categorize_import(module_name, imports, names=None):
    """Categorize an import based on the module name."""
    import_info = {
        'module': module_name,
        'names': [alias.name for alias in names] if names else None
    }
    
    if module_name.startswith('MediCafe'):
        imports['medicafe_imports'].append(import_info)
    elif module_name.startswith('MediBot'):
        imports['medibot_imports'].append(import_info)
    elif module_name.startswith('MediLink'):
        imports['medilink_imports'].append(import_info)
    elif module_name in ['os', 'sys', 'json', 'datetime', 're', 'pathlib', 'typing', 'collections']:
        imports['standard_library'].append(import_info)
    elif '.' in module_name or module_name in ['pandas', 'numpy', 'requests', 'flask', 'django']:
        imports['third_party'].append(import_info)
    else:
        imports['other_imports'].append(import_info)
    
    return imports

def _generate_smart_import_suggestions(imports):
    """Generate suggestions for using smart import system."""
    suggestions = []
    
    # Check for MediCafe imports that could be simplified
    medicafe_imports = imports.get('medicafe_imports', [])
    if medicafe_imports:
        components = []
        for imp in medicafe_imports:
            if imp['module'] == 'MediCafe.api_core':
                components.append('api_core')
            elif imp['module'] == 'MediCafe.logging_config':
                components.append('logging_config')
            elif imp['module'] == 'MediCafe.core_utils':
                components.append('core_utils')
            # Add more mappings as needed
        
        if components:
            suggestion = {
                'type': 'smart_import_conversion',
                'original': "Multiple MediCafe imports: {}".format([imp['module'] for imp in medicafe_imports]),
                'suggested': "from MediCafe import get_components\n{} = get_components({})".format(', '.join(components), ', '.join(repr(c) for c in components))
            }
            suggestions.append(suggestion)
    
    # Check for cross-package imports that indicate need for smart import
    cross_package_imports = []
    cross_package_imports.extend(imports.get('medibot_imports', []))
    cross_package_imports.extend(imports.get('medilink_imports', []))
    
    if cross_package_imports:
        suggestion = {
            'type': 'cross_package_optimization',
            'original': 'Cross-package imports detected',
            'suggested': 'Consider using setup_for_medibot() or setup_for_medilink() for comprehensive component access'
        }
        suggestions.append(suggestion)
    
    return suggestions

def _assess_migration_complexity(imports: Dict) -> str:
    """Assess the complexity of migrating a module to smart import system."""
    total_relevant_imports = (
        len(imports.get('medicafe_imports', [])) +
        len(imports.get('medibot_imports', [])) +
        len(imports.get('medilink_imports', []))
    )
    
    if total_relevant_imports == 0:
        return 'none'
    elif total_relevant_imports <= 3:
        return 'low'
    elif total_relevant_imports <= 7:
        return 'medium'
    else:
        return 'high'

def suggest_migration(file_path):
    """Generate detailed migration suggestions for a module."""
    analysis = analyze_module_imports(file_path)
    
    if 'error' in analysis:
        return analysis
    
    suggestions = []
    
    # Determine module type based on file path
    module_type = _determine_module_type(file_path)
    
    if module_type:
        suggestions.append({
            'type': 'module_setup',
            'title': 'Use {} setup function'.format(module_type),
            'description': 'Replace individual imports with setup_for_{}()'.format(module_type.split("_")[0]),
            'example': _generate_setup_example(module_type, analysis)
        })
    
    # Add specific component suggestions
    component_suggestions = _generate_component_suggestions(analysis)
    suggestions.extend(component_suggestions)
    
    return {
        'file_path': file_path,
        'module_type': module_type,
        'migration_complexity': analysis['migration_complexity'],
        'suggestions': suggestions,
        'estimated_effort': _estimate_migration_effort(analysis)
    }

def _determine_module_type(file_path):
    """Determine the appropriate module type based on file path and name."""
    file_name = os.path.basename(file_path).lower()
    
    if 'medibot' in file_path.lower():
        if 'preprocessor' in file_name:
            return 'medibot_preprocessor'
        elif 'ui' in file_name:
            return 'medibot_ui'
        elif 'crosswalk' in file_name:
            return 'medibot_crosswalk'
        elif 'docx' in file_name or 'document' in file_name:
            return 'medibot_document_processing'
        else:
            return 'medibot_preprocessor'  # Default
    
    elif 'medilink' in file_path.lower():
        if 'claim' in file_name:
            return 'medilink_claim_processing'
        elif 'deductible' in file_name:
            return 'medilink_deductible_processing'
        elif 'gmail' in file_name or 'mail' in file_name:
            return 'medilink_communication'
        elif 'data' in file_name or 'mgmt' in file_name:
            return 'medilink_data_management'
        else:
            return 'medilink_main'  # Default
    
    return None

def _generate_setup_example(module_type: str, analysis: Dict) -> str:
    """Generate an example of how to use the setup function."""
    if module_type.startswith('medibot'):
        setup_func = "setup_for_medibot('{}')".format(module_type)
    elif module_type.startswith('medilink'):
        setup_func = "setup_for_medilink('{}')".format(module_type)
    else:
        setup_func = "get_api_access()"
    
    example = """
# Replace multiple imports with smart import
from MediCafe import {setup_func.split('(')[0]}
components = {setup_func}

# Access components
api_core = components.get('api_core')
logging_config = components.get('logging_config')
# ... other components as needed
"""
    return example.strip()

def _generate_component_suggestions(analysis):
    """Generate specific component-level suggestions."""
    suggestions = []
    
    # Look for common patterns
    imports = analysis.get('imports', {})
    
    # Check for logging imports
    for imp in imports.get('medicafe_imports', []):
        if 'logging' in imp['module'].lower():
            suggestions.append({
                'type': 'component_simplification',
                'title': 'Simplify logging import',
                'description': 'Use get_logging() convenience function',
                'example': 'from MediCafe import get_logging\nlogging_config = get_logging()'
            })
            break
    
    # Check for API imports
    api_imports = [imp for imp in imports.get('medicafe_imports', []) 
                   if 'api' in imp['module'].lower()]
    if api_imports:
        suggestions.append({
            'type': 'api_suite',
            'title': 'Use API access suite',
            'description': 'Consolidate API-related imports',
            'example': 'from MediCafe import get_api_access\napi_suite = get_api_access()'
        })
    
    return suggestions

def _estimate_migration_effort(analysis: Dict) -> str:
    """Estimate the effort required for migration."""
    complexity = analysis['migration_complexity']
    import_counts = analysis['import_counts']
    
    total_imports = sum(import_counts.values())
    relevant_imports = (
        import_counts.get('medicafe_imports', 0) +
        import_counts.get('medibot_imports', 0) +
        import_counts.get('medilink_imports', 0)
    )
    
    if complexity == 'none':
        return 'No migration needed'
    elif complexity == 'low' and relevant_imports <= 2:
        return 'Minimal (< 30 minutes)'
    elif complexity == 'medium' and relevant_imports <= 5:
        return 'Moderate (30-60 minutes)'
    else:
        return 'Significant (> 60 minutes)'

def validate_smart_import_system():
    """Validate the smart import system functionality."""
    results = {
        'system_available': False,
        'component_tests': {},
        'module_type_tests': {},
        'errors': [],
        'warnings': []
    }
    
    try:
        from MediCafe import get_components, setup_for_medibot, setup_for_medilink
        results['system_available'] = True
        
        # Test core components
        core_components = ['logging_config', 'core_utils']
        for component in core_components:
            try:
                comp = get_components(component, silent_fail=True)
                results['component_tests'][component] = comp is not None
            except Exception as e:
                results['component_tests'][component] = False
                results['errors'].append("Failed to load {}: {}".format(component, e))
        
        # Test module types
        module_types = ['medibot_preprocessor', 'medilink_main']
        for module_type in module_types:
            try:
                if 'medibot' in module_type:
                    components = setup_for_medibot(module_type)
                else:
                    components = setup_for_medilink(module_type)
                results['module_type_tests'][module_type] = len(components) > 0
            except Exception as e:
                results['module_type_tests'][module_type] = False
                results['errors'].append("Failed to setup {}: {}".format(module_type, e))
        
    except ImportError as e:
        results['errors'].append("Smart import system not available: {}".format(e))
    
    return results

def batch_analyze_directory(directory, pattern="*.py"):
    """Analyze all Python files in a directory for migration opportunities."""
    directory_path = directory
    
    if not os.path.exists(directory_path):
        return {'error': 'Directory not found: {}'.format(directory)}
    
    results = {
        'directory': directory,
        'files_analyzed': 0,
        'migration_candidates': [],
        'summary': {
            'high_complexity': 0,
            'medium_complexity': 0,
            'low_complexity': 0,
            'no_migration_needed': 0
        }
    }
    
    for file_path in directory_path.glob(pattern):
        if file_path.is_file():
            analysis = analyze_module_imports(str(file_path))
            results['files_analyzed'] += 1
            
            if 'error' not in analysis:
                complexity = analysis['migration_complexity']
                results['summary']['{}_complexity'.format(complexity)] += 1
                
                if complexity != 'none':
                    results['migration_candidates'].append({
                        'file': str(file_path),
                        'complexity': complexity,
                        'import_counts': analysis['import_counts']
                    })
    
    return results

def generate_migration_report(directories):
    """Generate a comprehensive migration report for multiple directories."""
    report_lines = [
        "MediCafe Smart Import System - Migration Report",
        "=" * 50,
        ""
    ]
    
    total_files = 0
    total_candidates = 0
    
    for directory in directories:
        if os.path.exists(directory):
            analysis = batch_analyze_directory(directory)
            
            if 'error' not in analysis:
                report_lines.extend([
                    "Directory: {}".format(directory),
                    "Files analyzed: {}".format(analysis['files_analyzed']),
                    "Migration candidates: {}".format(len(analysis['migration_candidates'])),
                    ""
                ])
                
                total_files += analysis['files_analyzed']
                total_candidates += len(analysis['migration_candidates'])
                
                # Add complexity breakdown
                summary = analysis['summary']
                report_lines.extend([
                    "Complexity breakdown:",
                    "  High: {}".format(summary['high_complexity']),
                    "  Medium: {}".format(summary['medium_complexity']),
                    "  Low: {}".format(summary['low_complexity']),
                    "  None: {}".format(summary['no_migration_needed']),
                    ""
                ])
    
    # Add summary
    report_lines.extend([
        "Overall Summary:",
        "Total files analyzed: {}".format(total_files),
        "Total migration candidates: {}".format(total_candidates),
        "Migration rate: {:.1f}%".format((total_candidates/total_files*100)) if total_files > 0 else "N/A",
        ""
    ])
    
    # Add validation results
    validation = validate_smart_import_system()
    report_lines.extend([
        "Smart Import System Status:",
        "System available: {}".format(validation['system_available']),
        "Component tests passed: {}/{}".format(sum(validation['component_tests'].values()), len(validation['component_tests'])),
        "Module type tests passed: {}/{}".format(sum(validation['module_type_tests'].values()), len(validation['module_type_tests'])),
    ])
    
    if validation['errors']:
        report_lines.extend([
            "",
            "Errors:",
            *["  - {}".format(error) for error in validation['errors']]
        ])
    
    return "\n".join(report_lines)

# Convenience function for quick analysis
def quick_migration_check():
    """Perform a quick migration check of the main directories."""
    directories = ['MediBot', 'MediLink']
    existing_dirs = [d for d in directories if os.path.exists(d)]
    
    if not existing_dirs:
        print("No MediBot or MediLink directories found in current location.")
        return
    
    report = generate_migration_report(existing_dirs)
    print(report)
    
    # Suggest next steps
    print("\nNext Steps:")
    print("1. Review migration candidates with high/medium complexity")
    print("2. Use suggest_migration(file_path) for detailed suggestions")
    print("3. Test smart import system with validate_smart_import_system()")
    print("4. Start migration with low-complexity files first")