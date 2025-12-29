# MediCafe

**Comprehensive Healthcare Data Processing and Claims Management System**

MediCafe is a production-ready healthcare automation suite designed to streamline medical practice administrative workflows. The system automates data processing, claims submission, payer communication, and revenue cycle management tasks for healthcare providers.

## 🎯 Overview

MediCafe consists of two integrated components:

- **MediBot**: Automated document processing, data validation, and Medisoft data entry automation
- **MediLink**: Claims submission, payer API integration, EDI processing (837P, 835, 999, 277CA), and eligibility verification

### Key Capabilities

- **Claims Management**: Generate and submit 837P claims with COB (Coordination of Benefits) support
- **Payer API Integration**: Direct integration with UnitedHealthcare (UHCAPI), OptumAI, Availity, and PNT Data
- **Eligibility & Status**: Real-time eligibility verification, claim status checking, and deductible inquiry
- **ERA Processing**: Automated 835 remittance processing and reconciliation
- **Data Processing**: CSV parsing, validation, crosswalk mapping, and fixed-width file handling
- **Performance Optimized**: 70-85% faster processing through algorithmic improvements and caching

## 🚀 Installation

### Standard Installation

```bash
pip install medicafe
```

### Virtual Environment (Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install medicafe
```

### Development Installation

```bash
git clone https://github.com/katanada2/MediCafe.git
cd MediCafe
pip install -e .
```

## 📖 Quick Start

### Command-Line Interface

MediCafe provides a unified command-line entry point:

```bash
# Show available commands
medicafe --help

# Or using Python module syntax
python -m MediCafe --help
```

### Available Commands

- `medicafe medibot [config_file]` - Run MediBot data entry automation
- `medicafe medilink` - Run MediLink claims processing interface
- `medicafe claims_status` - Check UnitedHealthcare claim status
- `medicafe deductible` - Check UnitedHealthcare deductible information
- `medicafe download_emails` - Download payer emails via Gmail (future work)
- `medicafe send_error_report` - Generate and email support bundle
- `medicafe version` - Display version information

### Example Workflows

**Process and submit claims:**
```bash
medicafe medilink
```

**Check claim status for recent submissions:**
```bash
medicafe claims_status
```

**Verify patient deductibles:**
```bash
medicafe deductible
```

## 🔧 Configuration

MediCafe uses JSON-based configuration files located in the `json/` directory:

- `config.json` - Main system configuration (API endpoints, credentials, file paths)
- `crosswalk.json` - Data mapping tables (payer IDs, diagnosis codes, procedure codes)
- `medisoftconfig.json` - Medisoft-specific settings

See `docs/MEDICAFE_MASTER_GUIDE.md` for detailed configuration instructions.

## 🔌 API Integrations

### Supported Payer APIs

- **UnitedHealthcare (UHCAPI)**: Eligibility, claim status, deductible inquiry
- **OptumAI**: Real Claims Inquiry (GraphQL), eligibility verification
- **Availity**: Claims submission, ERA processing, acknowledgments
- **PNT Data**: Claims routing and processing

### Supported EDI Transactions

- **837P**: Professional claims submission
- **835**: Electronic Remittance Advice (ERA)
- **999**: Implementation Acknowledgment
- **277CA**: Claim Status Response
- **270/271**: Eligibility Inquiry/Response

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Master System Guide](docs/MEDICAFE_MASTER_GUIDE.md)** - Complete system documentation
- **[API Architecture Guide](docs/MEDICAFE_API_ARCHITECTURE.md)** - API client implementation details
- **[COB/Medicare Integration Guide](docs/COB_MEDICARE_INTEGRATION_GUIDE.md)** - Coordination of Benefits implementation
- **[Deductibles Workflow Guide](docs/DEDUCTIBLES_WORKFLOW_GUIDE.md)** - Deductible checking workflow
- **[OPTUM Integration Roadmap](docs/OPTUM_INTEGRATION_ROADMAP.md)** - OptumAI integration details
- **[Testing Guide](docs/TESTING_GUIDE.md)** - Test suite documentation

See `docs/README.md` for the complete documentation index.

## 🛠️ Future Work

### Gmail Pipeline (Planned)

Automated email ingestion from payer communications is planned for future releases. The infrastructure exists in `cloud/orchestrator/` but is not yet integrated into the main workflow.

See `cloud/orchestrator/FRESH_SETUP_GUIDE.md` for planned setup instructions.

## ⚡ Performance

Recent optimizations have significantly improved system performance:

- **70-85% faster** overall processing time
- **80-95% reduction** in API calls through intelligent caching
- **Eliminated O(n²) complexity** in data processing operations
- **Optimized memory management** for constrained environments

See `docs/PERFORMANCE_OPTIMIZATION_SOLUTION.md` for technical details.

## 🔒 Security & Compliance

- **HIPAA Compliance**: No protected health information (PHI) in logs
- **Secure Credential Management**: OAuth 2.0 token-based authentication
- **Error Reporting**: Automated support bundle generation with PHI exclusion
- **Audit Logging**: Comprehensive logging for compliance and troubleshooting

## 💻 System Requirements

### Runtime Requirements (End Users)

- **Python**: 3.4.4+ (tested on legacy Windows XP environments)
- **OS**: Windows XP+ or Linux
- **Memory**: Optimized for constrained environments (~200 patients, ~100 parameters per patient)

### Development/Build Requirements

- **Python**: 3.11+ (required for `build_package.py` and development tools)
- **Note**: The build script requires Python 3.11+, but the built package targets Python 3.4.4+ for runtime compatibility

### Modern Environments

MediCafe also runs on modern Python 3.5+ and Windows 10/11 systems. The codebase maintains backward compatibility while supporting newer Python features where available.

## 🏗️ Architecture

```
MediCafe/
├── MediBot/                 # Data processing and automation
│   ├── MediBot.py          # Main entry point
│   ├── MediBot_UI.py       # User interface
│   └── MediBot_*.py        # Processing modules
├── MediLink/               # Claims and API integration
│   ├── MediLink_main.py    # Main entry point
│   ├── MediLink_UI.py      # User interface
│   └── MediLink_*.py       # Claims modules
├── MediCafe/               # Core utilities package
│   ├── api_core.py         # Unified API client
│   ├── graphql_utils.py    # GraphQL operations
│   ├── core_utils.py       # Shared utilities
│   └── MediLink_ConfigLoader.py  # Configuration management
├── json/                   # Configuration files
├── cloud/orchestrator/     # Gmail pipeline orchestration (future work)
├── tools/                  # Utility scripts
└── docs/                   # Comprehensive documentation
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in `PYTHONPATH` or use `python -m MediCafe`
2. **API Authentication**: Verify credentials in `json/config.json`
3. **File Path Issues**: Check `CSV_FILE_PATH` and other path configurations
4. **Python 3.4 Compatibility**: Some features require Python 3.4.4+ syntax

### Error Reporting

Generate a support bundle for troubleshooting:

```bash
medicafe send_error_report
```

This creates a comprehensive diagnostic package (excluding PHI) for support.

## 📝 Recent Improvements

### 2024-2025 Updates

- ✅ **Cache Optimization** (Nov 2025): Invalid code validation, date parsing consistency, +10-15% cache hit rate
- ✅ **API Client Consolidation**: Unified API client architecture
- ✅ **Performance Optimizations**: 70-85% faster processing
- ✅ **Enhanced Error Handling**: Detailed logging and user guidance
- ✅ **COB Library Integration**: Medicare secondary billing support
- ✅ **OptumAI Integration**: Real Claims Inquiry implementation
- ✅ **Documentation Consolidation**: Streamlined documentation structure

See `docs/MEDICAFE_MASTER_GUIDE.md` for complete changelog and `docs/fixes/CACHE_FIXES_IMPLEMENTATION.md` for cache optimization details.

## 🤝 Contributing

This is community-supported software. Contributions are welcome:

1. Open an issue for bugs or feature requests
2. Include Python version, OS, and exact command/error details
3. Follow existing code style and Python 3.4.4 compatibility guidelines

## 📄 License

MIT License. See `LICENSE` file for details.

## 👤 Author

**Daniel Vidaud**  
Email: daniel@personalizedtransformation.com

## 🔗 Links

- **Source Code**: [GitHub Repository](https://github.com/katanada2/MediCafe)
- **Issue Tracker**: [GitHub Issues](https://github.com/katanada2/MediCafe/issues)
- **Documentation**: See `docs/README.md` for complete documentation index

---

**Note**: MediCafe is designed for healthcare administrative workflows. Ensure proper HIPAA compliance and security measures are in place for production deployments.
