# ublkit

**Simple, powerful UBL XML to JSON/CSV converter with built-in exception handling**

[![PyPI version](https://badge.fury.io/py/ublkit.svg)](https://badge.fury.io/py/ublkit)
[![Python Versions](https://img.shields.io/pypi/pyversions/ublkit.svg)](https://pypi.org/project/ublkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[ublkit](https://pypi.org/project/ublkit/) is a lightweight wrapper that converts UBL XML documents (Invoice, CreditNote, Order, DespatchAdvice, etc.) to JSON or CSV format with a simple, clean API.

---

## ✨ Features

- 🚀 **Zero Configuration** - Works out of the box with sensible defaults
- 📁 **Flexible Output** - Convert to JSON or flattened CSV format
- 🎯 **Single File or Batch** - Process one file or entire directories
- 🔄 **Parallel Processing** - Fast batch conversion with multithreading
- 📊 **CSV File Splitting** - Automatically split large CSVs into manageable chunks
- 🛡️ **Robust Error Handling** - Never crashes, always provides detailed error info
- 📝 **Comprehensive Logging** - Uses py-logex for production-grade logging
- ⚙️ **YAML Configuration** - Easy, flexible configuration
- 🎨 **Data Preservation** - Prevents Excel from corrupting your data
- 📋 **Detailed Summaries** - File-by-file status and aggregate statistics

---

## 📦 Installation

```bash
pip install ublkit
```

**Requirements:**
- Python >= 3.8
- lxml >= 4.9.0
- polars >= 0.19.0
- pyyaml >= 6.0
- py-logex-enhanced >= 0.1.0

---

## 🚀 Quick Start

### Single File Conversion

```python
from ublkit import convert_file

# Convert to JSON
result = convert_file(
    xml_path="invoice.xml",
    output_format="json",
    config_path="./config/ublkit.yaml"
)

# Result contains everything in memory
if result["success"]:
    print(f"UBL Type: {result['ubl_document_type']}")
    print(f"Processing time: {result['processing_time_seconds']:.2f}s")
    data = result["content"]  # Your converted data
else:
    print(f"Error: {result['error_message']}")
```

### Batch Processing

```python
from ublkit import convert_batch

# Convert entire directory to CSV
summary = convert_batch(
    input_dir="./xml_files",
    output_dir="./output",
    output_format="csv",
    config_path="./config/ublkit.yaml"
)

print(f"Processed: {summary.total_files}")
print(f"Successful: {summary.successful}")
print(f"Failed: {summary.failed}")
```

---

## ⚙️ Configuration

Create `ublkit.yaml` in your project root:

```yaml
# Logging configuration (uses py-logex library)
logging:
  level: "INFO"
  file: "ublkit.log"
  rotation: "500 MB"
  retention: "10 days"
  compression: "zip"

# Processing configuration
processing:
  max_workers: 4                   # Parallel threads
  encoding: "utf-8"

# CSV output configuration
csv:
  max_records_per_file: 50000      # Split large CSVs
  preservation_method: "apostrophe" # Prevent Excel corruption
  key_separator: " | "

# Output directories
output:
  summary_dir: "./summaries"
  logs_dir: "./logs"

# Feature flags
features:
  enable_dry_run: false
```

### CSV Preservation Methods

Prevent Excel from corrupting your data:
- `apostrophe`: Prepends `'` to values (Excel standard)
- `quotes`: Wraps values in double quotes
- `brackets`: Wraps values in `[` `]`

---

## 🎯 API Reference

### `convert_file()`

Convert a single XML file (in-memory, no disk writes).

```python
result = convert_file(
    xml_path: str,              # Path to UBL XML file
    output_format: str,         # "json" or "csv"
    config_path: str            # Path to ublkit.yaml (required)
) -> dict
```

**Returns:**
```python
{
    "success": bool,
    "error_message": str,
    "processing_time_seconds": float,
    "source_file": str,
    "file_size_bytes": int,
    "ubl_document_type": str,
    "output_format": str,
    "content": dict | list      # Converted data
}
```

### `convert_batch()`

Convert multiple XML files (writes to disk).

```python
summary = convert_batch(
    input_dir: str,             # Directory containing XML files
    output_dir: str,            # Output directory
    output_format: str,         # "json" or "csv"
    config_path: str            # Path to ublkit.yaml (required)
) -> ProcessingSummary
```

**Returns:** `ProcessingSummary` object with:
- `total_files`: Total files processed
- `successful`: Successfully converted
- `failed`: Failed conversions
- `results`: List of per-file results
- `start_time`, `end_time`: Processing timestamps

---

## 🛠️ CLI Usage

```bash
# Single file to JSON
ublkit convert invoice.xml --format json --output output.json --config ublkit.yaml

# Batch to CSV
ublkit batch ./xml_files ./output --format csv --config ublkit.yaml

# Dry run (preview without writing)
ublkit batch ./xml_files ./output --dry-run --config ublkit.yaml
```

---

## 📊 CSV Output Format

UBLKit flattens nested XML into key-value pairs:

```csv
Key,Value,Filename
Invoice | ID | value,'INV-001',invoice_001.xml
Invoice | IssueDate | value,'2024-12-27',invoice_001.xml
Invoice | AccountingSupplierParty | Party | PartyName | Name | value,'ACME Corp',invoice_001.xml
```

Benefits:
- ✅ See all data at a glance
- ✅ Easy validation and debugging
- ✅ Works with any UBL document type
- ✅ Automatic file splitting for large datasets

---

## 🧪 Development

```bash
# Clone repository
git clone https://github.com/sherozshaikh/ublkit.git
cd ublkit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=ublkit --cov-report=html

# Format code
black src tests
isort src tests

# Type checking
mypy src
```

---

## 📖 Supported UBL Document Types

UBLKit works with **any** UBL 2.x document type:
- Invoice
- CreditNote
- DebitNote
- Order
- OrderResponse
- DespatchAdvice
- ReceiptAdvice
- ApplicationResponse
- And more...

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [lxml](https://lxml.de/) for robust XML processing
- Uses [polars](https://www.pola.rs/) for efficient CSV operations
- Powered by [py-logex](https://github.com/sherozshaikh/py-logex) for production logging

---

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/sherozshaikh/ublkit/issues)
- **PyPI**: [https://pypi.org/project/ublkit/](https://pypi.org/project/ublkit/)

---

Made with ❤️ for the UBL community
