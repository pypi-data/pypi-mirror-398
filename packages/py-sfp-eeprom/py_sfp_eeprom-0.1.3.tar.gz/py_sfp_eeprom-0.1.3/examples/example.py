#!/usr/bin/env python3
"""
Example script demonstrating how to create an SFP EEPROM from scratch.

This example creates a complete A0h EEPROM image with vendor information,
validates checksums, and exports it to a binary file.
"""

import sys
from pathlib import Path

# Add the parent directory to the path to import the library
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sfp_eeprom import SFPA0h


def main():
    print("=" * 70)
    print("SFP EEPROM A0h Creation Example")
    print("=" * 70)
    print()

    # Create a new EEPROM from scratch
    print("Creating new EEPROM...")
    eeprom = SFPA0h()

    # Set basic identification fields
    print("\n1. Setting identification fields...")
    eeprom.set('identifier', SFPA0h.IDENTIFIER_SFP)           # SFP/SFP+/SFP28
    eeprom.set('ext_identifier', SFPA0h.EXT_IDENTIFIER_SFF)   # GBIC/SFP function
    eeprom.set('connector', SFPA0h.CONNECTOR_LC)              # LC connector

    # Set encoding and bit rate
    print("2. Setting transceiver specifications...")
    eeprom.set('encoding', SFPA0h.ENCODING_64B66B)  # 64B/66B encoding
    eeprom.set('br_nominal', 103)                   # 10.3 Gbps nominal (103 * 100 Mbps)
    eeprom.set('br_max', 0)                         # No upper margin specified
    eeprom.set('br_min', 0)                         # No lower margin specified

    # Set wavelength (1310nm for example)
    print("3. Setting wavelength...")
    eeprom.set('wavelength', 1310)          # 1310 nm

    # Set link lengths
    print("4. Setting supported link lengths...")
    eeprom.set('length_smf_km', 10)         # 10 km (automatically sets length_smf to 100)
    # Other length fields default to 0

    # Set vendor information
    print("5. Setting vendor information...")
    eeprom.set('vendor_name', 'ACME FIBER')
    eeprom.set('vendor_oui', bytes.fromhex('001122'))  # Example IEEE OUI
    eeprom.set('vendor_pn', 'SFP-10G-LR')
    eeprom.set('vendor_rev', 'A1')
    eeprom.set('vendor_sn', 'ABC123456789')

    # Set date code (YYMMDD format + lot code)
    print("6. Setting manufacturing date...")
    eeprom.set('date_code', '25112500')     # November 25, 2025, lot 00

    # Set options and diagnostic monitoring
    print("7. Setting options and monitoring capabilities...")
    eeprom.set('options',
               SFPA0h.OPTIONS_TX_DISABLE |      # TX_DISABLE signal implemented
               SFPA0h.OPTIONS_TX_FAULT |        # TX_FAULT signal implemented
               SFPA0h.OPTIONS_RX_LOS)           # Loss of Signal implemented
    eeprom.set('diagnostic_monitoring',
               SFPA0h.DIAG_MONITORING_REQUIRED |               # Digital diagnostic monitoring implemented
               SFPA0h.DIAG_MONITORING_INTERNALLY_CALIBRATED |  # Internally calibrated
               SFPA0h.DIAG_MONITORING_RX_POWER_AVG)            # Average power measurement
    eeprom.set('enhanced_options', 0x00)                       # No enhanced options
    eeprom.set('sff8472_compliance', SFPA0h.SFF8472_REV_9_3)   # SFF-8472 Rev 9.3

    # Set transceiver codes using named constants
    print("8. Setting transceiver compliance codes...")
    eeprom.set_transceiver_codes(
        SFPA0h.TRANSCEIVER_10GBASE_LR,    # 10GBASE-LR
        SFPA0h.TRANSCEIVER_SINGLE_MODE     # Single-mode fiber
    )

    # Update checksums
    print("9. Calculating and updating checksums...")
    eeprom.update_checksums()

    # Validate checksums
    print("\n10. Validating checksums...")
    checksums = eeprom.validate_checksums()
    print(f"    CC_BASE valid: {checksums['cc_base']}")
    print(f"    CC_EXT valid:  {checksums['cc_ext']}")

    # Display EEPROM information
    print("\n" + "=" * 70)
    print("EEPROM Information Summary")
    print("=" * 70)
    info = eeprom.get_info()

    print(f"\nIdentifier:        {info['identifier']['description']} (0x{info['identifier']['value']:02X})")
    print(f"Connector:         {info['connector']['description']} (0x{info['connector']['value']:02X})")
    print(f"\nVendor Name:       {info['vendor_name']}")
    print(f"Vendor OUI:        {info['vendor_oui']}")
    print(f"Part Number:       {info['vendor_pn']}")
    print(f"Revision:          {info['vendor_rev']}")
    print(f"Serial Number:     {info['vendor_sn']}")
    print(f"Date Code:         {info['date_code']}")
    print(f"\nWavelength:        {info['wavelength']} nm")
    print(f"Bit Rate:          {info['br_nominal'] * 100} Mbps")
    print(f"Encoding:          0x{info['encoding']:02X}")
    print(f"\nLink Lengths:")
    print(f"  SMF:             {info['length_smf_km']} km")
    print(f"  50um (OM2):      {info['length_50um'] * 10} m")
    print(f"  62.5um (OM1):    {info['length_62_5um'] * 10} m")
    print(f"  OM3:             {info['length_om3'] * 10} m")
    print(f"  Copper:          {info['length_copper']} m")

    # Export to binary file
    output_file = 'eeprom_a0h.bin'
    print(f"\n{'=' * 70}")
    print(f"Exporting EEPROM to {output_file}...")
    eeprom_bytes = eeprom.to_bytes()

    with open(output_file, 'wb') as f:
        f.write(eeprom_bytes)

    print(f"Successfully wrote {len(eeprom_bytes)} bytes to {output_file}")

    # Display hex dump of first 64 bytes
    print(f"\nHex dump of first 64 bytes:")
    print("Offset   00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F")
    print("-" * 70)
    for i in range(0, 64, 16):
        hex_bytes = ' '.join(f'{b:02X}' for b in eeprom_bytes[i:i+16])
        print(f"{i:06X}   {hex_bytes}")

    # Demonstrate reading back the EEPROM
    print(f"\n{'=' * 70}")
    print("Reading EEPROM back from file...")
    print("=" * 70)

    with open(output_file, 'rb') as f:
        loaded_data = f.read()

    loaded_eeprom = SFPA0h.from_bytes(loaded_data)
    print(f"\nLoaded EEPROM: {loaded_eeprom}")

    # Verify it matches
    loaded_checksums = loaded_eeprom.validate_checksums()
    print(f"\nChecksum validation after reload:")
    print(f"    CC_BASE valid: {loaded_checksums['cc_base']}")
    print(f"    CC_EXT valid:  {loaded_checksums['cc_ext']}")

    print(f"\nVendor: {loaded_eeprom.get('vendor_name')}")
    print(f"Part Number: {loaded_eeprom.get('vendor_pn')}")
    print(f"Serial Number: {loaded_eeprom.get('vendor_sn')}")

    print(f"\n{'=' * 70}")
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == '__main__':
    main()
