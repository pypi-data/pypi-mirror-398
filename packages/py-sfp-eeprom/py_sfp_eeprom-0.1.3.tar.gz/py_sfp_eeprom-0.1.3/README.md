# Python SFP EEPROM

A Python library to manage SFP module EEPROM data based on SFF-8472 specifications.

## Features

- Create A0h EEPROM from scratch
- Load A0h EEPROM from binary bytes
- Get and set individual EEPROM fields
- Automatic checksum calculation and validation
- Export EEPROM as 256-byte binary data
- Human-readable field access and information display
- Support for all SFF-8472 standard fields

## Installation

Install from PyPI:

```bash
pip install py-sfp-eeprom
```

Or for development, you can install in editable mode:

```bash
pip install -e .
```

## Quick Start

### Creating an EEPROM from Scratch

```python
from sfp_eeprom import SFPA0h

# Create a new empty EEPROM
eeprom = SFPA0h()

# Set vendor information
eeprom.set('vendor_name', 'ACME FIBER')
eeprom.set('vendor_pn', 'SFP-10G-LR')
eeprom.set('vendor_sn', 'ABC123456789')
eeprom.set('vendor_oui', bytes.fromhex('001122'))

# Set transceiver type using named constants
eeprom.set('identifier', SFPA0h.IDENTIFIER_SFP)    # SFP/SFP+/SFP28
eeprom.set('connector', SFPA0h.CONNECTOR_LC)       # LC connector
eeprom.set('encoding', SFPA0h.ENCODING_64B66B)     # 64B/66B encoding

# Set specifications
eeprom.set('wavelength', 1310)  # 1310nm
eeprom.set('br_nominal', 103)   # 10.3 Gbps

# Update checksums
eeprom.update_checksums()

# Export to binary file
with open('eeprom.bin', 'wb') as f:
    f.write(eeprom.to_bytes())
```

### Loading an Existing EEPROM

```python
from sfp_eeprom import SFPA0h

# Read from binary file
with open('eeprom.bin', 'rb') as f:
    data = f.read()

# Create EEPROM object
eeprom = SFPA0h.from_bytes(data)

# Access fields
print(f"Vendor: {eeprom.get('vendor_name')}")
print(f"Part Number: {eeprom.get('vendor_pn')}")
print(f"Serial: {eeprom.get('vendor_sn')}")

# Get comprehensive info
info = eeprom.get_info()
print(info)
```

### Modifying EEPROM Values

```python
from sfp_eeprom import SFPA0h

# Load existing EEPROM
eeprom = SFPA0h.from_bytes(data)

# Change serial number
eeprom.set('vendor_sn', 'NEW-SN-12345')

# Change wavelength
eeprom.set('wavelength', 1550)  # 1550nm

# Checksums are automatically recalculated
# when you use the set() method

# Export modified EEPROM
modified_data = eeprom.to_bytes()
```

## Named Constants

The library provides named constants for common field values, making code more readable:

### Identifier Types
- `IDENTIFIER_UNKNOWN` - Unknown/unspecified (0x00)
- `IDENTIFIER_GBIC` - GBIC (0x01)
- `IDENTIFIER_SOLDERED` - Soldered to motherboard (0x02)
- `IDENTIFIER_SFP` - SFP/SFP+/SFP28 (0x03)
- `IDENTIFIER_XFP` - XFP (0x06)
- `IDENTIFIER_QSFP` - QSFP (0x0C)
- `IDENTIFIER_QSFP_PLUS` - QSFP+ or later (0x0D)
- `IDENTIFIER_QSFP28` - QSFP28 or later (0x11)
- And more...

### Connector Types
- `CONNECTOR_UNKNOWN` - Unknown/unspecified (0x00)
- `CONNECTOR_SC` - SC connector (0x01)
- `CONNECTOR_LC` - LC connector (0x07)
- `CONNECTOR_MT_RJ` - MT-RJ connector (0x08)
- `CONNECTOR_MU` - MU connector (0x09)
- `CONNECTOR_RJ45` - RJ45 connector (0x22)
- `CONNECTOR_MPO_1X12` - MPO 1x12 connector (0x0C)
- And more...

### Encoding Types
- `ENCODING_UNSPECIFIED` - Unspecified (0x00)
- `ENCODING_8B10B` - 8B/10B (0x01)
- `ENCODING_4B5B` - 4B/5B (0x02)
- `ENCODING_NRZ` - NRZ (0x03)
- `ENCODING_64B66B` - 64B/66B (0x06)

### Extended Identifier
- `EXT_IDENTIFIER_GBIC` - GBIC definition (0x00)
- `EXT_IDENTIFIER_SFF` - SFF-8472 compliant (0x04)

Example using constants:
```python
eeprom.set('identifier', SFPA0h.IDENTIFIER_SFP)
eeprom.set('connector', SFPA0h.CONNECTOR_LC)
eeprom.set('encoding', SFPA0h.ENCODING_64B66B)
```

## Supported Fields

The library supports all standard SFF-8472 A0h fields:

### Identification Fields
- `identifier` - Transceiver type (0x03 = SFP)
- `ext_identifier` - Extended identifier
- `connector` - Connector type (0x07 = LC)

### Vendor Information
- `vendor_name` - 16-character vendor name
- `vendor_oui` - IEEE company ID (3 bytes)
- `vendor_pn` - Part number (16 characters)
- `vendor_rev` - Revision (4 characters)
- `vendor_sn` - Serial number (16 characters)
- `date_code` - Manufacturing date (8 characters: YYMMDD + lot code)

### Transceiver Specifications
- `transceiver` - Compliance codes (8 bytes)
- `encoding` - Encoding type
- `br_nominal` - Nominal bit rate (units of 100 Mbps)
- `br_max` - Upper bit rate margin
- `br_min` - Lower bit rate margin
- `wavelength` - Wavelength in nm (or copper attenuation)

### Link Lengths
- `length_smf_km` - Single-mode fiber, km
- `length_smf` - Single-mode fiber, 100m units
- `length_50um` - 50µm OM2 fiber, 10m units
- `length_62_5um` - 62.5µm OM1 fiber, 10m units
- `length_copper` - Copper cable, 1m units
- `length_om3` - 50µm OM3 fiber, 10m units

### Options and Diagnostics
- `options` - Implemented options (2 bytes)
- `diagnostic_monitoring` - Diagnostic monitoring type
- `enhanced_options` - Enhanced options
- `sff8472_compliance` - SFF-8472 compliance level

### Checksums
- `cc_base` - Checksum for base ID (bytes 0-62)
- `cc_ext` - Checksum for extended ID (bytes 64-94)

## API Reference

### SFPA0h Class

#### `__init__(data=None)`
Create a new EEPROM instance. If `data` is provided, it must be exactly 256 bytes.

#### `get(field_name)`
Get a field value in human-readable format (str, int, or bytes).

#### `set(field_name, value)`
Set a field value. Automatically updates checksums for affected regions.

#### `to_bytes()`
Export the complete EEPROM as 256 bytes.

#### `from_bytes(data)` (class method)
Create an EEPROM instance from 256 bytes of data.

#### `update_checksums()`
Manually recalculate and update both CC_BASE and CC_EXT checksums.

#### `validate_checksums()`
Validate both checksums. Returns dict with `cc_base` and `cc_ext` boolean values.

#### `get_info()`
Get a dictionary of all human-readable EEPROM information.

## Examples

### Creating an EEPROM (examples/example.py)

See `examples/example.py` for a complete demonstration of creating an EEPROM from scratch, setting all fields, validating checksums, and exporting to a binary file.

```bash
python examples/example.py
```

This will create an `eeprom_a0h.bin` file with a complete, valid SFP EEPROM image.

### Reading an EEPROM (examples/read_eeprom.py)

Use the `examples/read_eeprom.py` CLI tool to read and display information from an existing EEPROM binary file:

```bash
# Display EEPROM information
python examples/read_eeprom.py eeprom_a0h.bin

# Display with hex dump
python examples/read_eeprom.py eeprom_a0h.bin --hex

# Get help
python examples/read_eeprom.py --help
```

The tool displays:
- Identification information (transceiver type, connector type)
- Vendor information (name, OUI, part number, serial number, date code)
- Transceiver specifications (encoding, bit rate, wavelength)
- Supported link lengths
- Options and diagnostic monitoring information
- Checksum validation status
- Optional hex dump of the entire EEPROM

Exit codes:
- `0` - Success (checksums valid)
- `1` - File error or invalid EEPROM
- `2` - EEPROM loaded but checksums invalid

## Specifications

Based on SFF-8472 (SFP MSA) specification for the A0h lower page (256 bytes).

## License

This is free and unencumbered software released into the public domain.
