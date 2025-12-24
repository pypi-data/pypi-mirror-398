#!/usr/bin/env python3
"""
CLI tool to read and display SFP EEPROM information from a binary file.

Usage:
    python read_eeprom.py <path_to_eeprom_file>
"""

import sys
import argparse
from pathlib import Path

# Add the parent directory to the path to import the library
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sfp_eeprom import SFPA0h


def format_bytes_hex(data: bytes, bytes_per_line: int = 16) -> str:
    """Format bytes as a hex dump."""
    lines = []
    for i in range(0, len(data), bytes_per_line):
        hex_part = ' '.join(f'{b:02X}' for b in data[i:i+bytes_per_line])
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+bytes_per_line])
        lines.append(f"{i:06X}   {hex_part:<{bytes_per_line*3}}  {ascii_part}")
    return '\n'.join(lines)


def print_eeprom_info(eeprom: SFPA0h, show_hex: bool = False):
    """Print comprehensive EEPROM information."""

    print("=" * 80)
    print("SFP EEPROM A0h Information")
    print("=" * 80)

    # Get comprehensive info
    info = eeprom.get_info()

    # Identification Section
    print("\n┌─ IDENTIFICATION " + "─" * 62)
    print(f"│ Identifier:          {info['identifier']['description']}")
    print(f"│                      (0x{info['identifier']['value']:02X})")
    print(f"│ Extended Identifier: 0x{eeprom.get('ext_identifier'):02X}")
    print(f"│ Connector:           {info['connector']['description']}")
    print(f"│                      (0x{info['connector']['value']:02X})")
    print("└" + "─" * 79)

    # Vendor Information Section
    print("\n┌─ VENDOR INFORMATION " + "─" * 58)
    print(f"│ Vendor Name:         {info['vendor_name']}")
    print(f"│ Vendor OUI:          {info['vendor_oui']}")
    print(f"│ Part Number:         {info['vendor_pn']}")
    print(f"│ Revision:            {info['vendor_rev']}")
    print(f"│ Serial Number:       {info['vendor_sn']}")
    print(f"│ Date Code:           {info['date_code']}")
    if len(info['date_code']) >= 6:
        try:
            year = info['date_code'][0:2]
            month = info['date_code'][2:4]
            day = info['date_code'][4:6]
            lot = info['date_code'][6:8] if len(info['date_code']) >= 8 else ''
            print(f"│                      (20{year}-{month}-{day}, Lot: {lot})")
        except:
            pass
    print("└" + "─" * 79)

    # Transceiver Specifications Section
    print("\n┌─ TRANSCEIVER SPECIFICATIONS " + "─" * 49)
    print(f"│ Encoding:            0x{info['encoding']:02X}")

    # Decode encoding
    encoding_map = {
        SFPA0h.ENCODING_UNSPECIFIED: "Unspecified",
        SFPA0h.ENCODING_8B10B: "8B/10B",
        SFPA0h.ENCODING_4B5B: "4B/5B",
        SFPA0h.ENCODING_NRZ: "NRZ",
        SFPA0h.ENCODING_MANCHESTER: "Manchester",
        SFPA0h.ENCODING_SONET: "SONET Scrambled",
        SFPA0h.ENCODING_64B66B: "64B/66B",
        SFPA0h.ENCODING_256B257B: "256B/257B",
    }
    if info['encoding'] in encoding_map:
        print(f"│                      ({encoding_map[info['encoding']]})")

    br_nominal_mbps = info['br_nominal'] * 100
    print(f"│ Bit Rate (Nominal):  {info['br_nominal']} units ({br_nominal_mbps} Mbps)")

    br_max = eeprom.get('br_max')
    br_min = eeprom.get('br_min')
    if br_max > 0:
        print(f"│ Bit Rate (Max):      +{br_max}%")
    if br_min > 0:
        print(f"│ Bit Rate (Min):      -{br_min}%")

    wavelength = info['wavelength']
    if wavelength > 0:
        print(f"│ Wavelength:          {wavelength} nm")

    # Display and decode transceiver codes (bytes 3-10)
    transceiver = eeprom.get('transceiver')
    if isinstance(transceiver, bytes):
        print(f"│ Transceiver Codes:   {transceiver.hex().upper()}")

        # Decode each byte if any bits are set
        if any(b != 0 for b in transceiver):
            # Byte 3: 10G Ethernet Compliance Codes
            if transceiver[0] != 0:
                codes_10g_eth = []
                if transceiver[0] & 0x80: codes_10g_eth.append("10GBASE-ER")
                if transceiver[0] & 0x40: codes_10g_eth.append("10GBASE-LRM")
                if transceiver[0] & 0x20: codes_10g_eth.append("10GBASE-LR")
                if transceiver[0] & 0x10: codes_10g_eth.append("10GBASE-SR")
                # Check for unknown bits in byte 3
                unknown_bits = transceiver[0] & 0x0F  # Lower 4 bits not decoded
                if unknown_bits:
                    codes_10g_eth.append(f"UNKNOWN(0x{unknown_bits:02X})")
                if codes_10g_eth:
                    print(f"│   10G Ethernet:      {', '.join(codes_10g_eth)}")

            # Byte 4: 10G Ethernet Compliance Codes (continued)
            if transceiver[1] != 0:
                print(f"│   Byte 4 (10G):      UNKNOWN (0x{transceiver[1]:02X})")

            # Byte 5: 10G Ethernet Compliance Codes (continued)
            if transceiver[2] != 0:
                print(f"│   Byte 5 (10G):      UNKNOWN (0x{transceiver[2]:02X})")

            # Byte 6: Ethernet Compliance Codes
            if transceiver[3] != 0:
                codes_eth = []
                decoded_bits = 0
                if transceiver[3] & 0x80: codes_eth.append("BASE-PX"); decoded_bits |= 0x80
                if transceiver[3] & 0x40: codes_eth.append("BASE-BX10"); decoded_bits |= 0x40
                if transceiver[3] & 0x20: codes_eth.append("100BASE-FX"); decoded_bits |= 0x20
                if transceiver[3] & 0x10: codes_eth.append("100BASE-LX/LX10"); decoded_bits |= 0x10
                if transceiver[3] & 0x08: codes_eth.append("1000BASE-T"); decoded_bits |= 0x08
                if transceiver[3] & 0x04: codes_eth.append("1000BASE-CX"); decoded_bits |= 0x04
                if transceiver[3] & 0x02: codes_eth.append("1000BASE-LX"); decoded_bits |= 0x02
                if transceiver[3] & 0x01: codes_eth.append("1000BASE-SX"); decoded_bits |= 0x01
                # Check for unknown bits
                unknown_bits = transceiver[3] & ~decoded_bits
                if unknown_bits:
                    codes_eth.append(f"UNKNOWN(0x{unknown_bits:02X})")
                if codes_eth:
                    print(f"│   Ethernet:          {', '.join(codes_eth)}")

            # Byte 7: Fibre Channel Link Length
            if transceiver[4] != 0:
                fc_len = []
                decoded_bits = 0
                if transceiver[4] & 0x80: fc_len.append("very long distance (V)"); decoded_bits |= 0x80
                if transceiver[4] & 0x40: fc_len.append("short distance (S)"); decoded_bits |= 0x40
                if transceiver[4] & 0x20: fc_len.append("intermediate distance (I)"); decoded_bits |= 0x20
                if transceiver[4] & 0x10: fc_len.append("long distance (L)"); decoded_bits |= 0x10
                if transceiver[4] & 0x08: fc_len.append("medium distance (M)"); decoded_bits |= 0x08
                # Check for unknown bits
                unknown_bits = transceiver[4] & ~decoded_bits
                if unknown_bits:
                    fc_len.append(f"UNKNOWN(0x{unknown_bits:02X})")
                if fc_len:
                    print(f"│   FC Length:         {', '.join(fc_len)}")

            # Byte 8: Fibre Channel Technology
            if transceiver[5] != 0:
                fc_tech = []
                decoded_bits = 0
                if transceiver[5] & 0x04: fc_tech.append("Shortwave laser (SN)"); decoded_bits |= 0x04
                if transceiver[5] & 0x02: fc_tech.append("Longwave laser (LC)"); decoded_bits |= 0x02
                if transceiver[5] & 0x01: fc_tech.append("Electrical inter-enclosure (EL)"); decoded_bits |= 0x01
                # Check for unknown bits
                unknown_bits = transceiver[5] & ~decoded_bits
                if unknown_bits:
                    fc_tech.append(f"UNKNOWN(0x{unknown_bits:02X})")
                if fc_tech:
                    print(f"│   FC Technology:     {', '.join(fc_tech)}")

            # Byte 9: SFP+ Cable Technology
            if transceiver[6] != 0:
                cable_tech = []
                decoded_bits = 0
                if transceiver[6] & 0x08: cable_tech.append("Active Cable"); decoded_bits |= 0x08
                if transceiver[6] & 0x04: cable_tech.append("Passive Cable"); decoded_bits |= 0x04
                # Check for unknown bits
                unknown_bits = transceiver[6] & ~decoded_bits
                if unknown_bits:
                    cable_tech.append(f"UNKNOWN(0x{unknown_bits:02X})")
                if cable_tech:
                    print(f"│   Cable Technology:  {', '.join(cable_tech)}")

            # Byte 10: Fibre Channel Transmission Media
            if transceiver[7] != 0:
                fc_media = []
                decoded_bits = 0
                if transceiver[7] & 0x80: fc_media.append("Twin Axial Pair (TW)"); decoded_bits |= 0x80
                if transceiver[7] & 0x40: fc_media.append("Twisted Pair (TP)"); decoded_bits |= 0x40
                if transceiver[7] & 0x20: fc_media.append("Miniature Coax (MI)"); decoded_bits |= 0x20
                if transceiver[7] & 0x10: fc_media.append("Video Coax (TV)"); decoded_bits |= 0x10
                if transceiver[7] & 0x08: fc_media.append("Multi-mode 62.5µm (M6)"); decoded_bits |= 0x08
                if transceiver[7] & 0x04: fc_media.append("Multi-mode 50µm (M5)"); decoded_bits |= 0x04
                if transceiver[7] & 0x02: fc_media.append("Multi-mode 50µm (OM3)"); decoded_bits |= 0x02
                if transceiver[7] & 0x01: fc_media.append("Single Mode (SM)"); decoded_bits |= 0x01
                # Check for unknown bits
                unknown_bits = transceiver[7] & ~decoded_bits
                if unknown_bits:
                    fc_media.append(f"UNKNOWN(0x{unknown_bits:02X})")
                if fc_media:
                    print(f"│   FC Media:          {', '.join(fc_media)}")

    # Display extended compliance codes (byte 36) - important for 2.5G/5G/etc
    transceiver_ext = eeprom.get('transceiver_ext')

    # Extended Specification Compliance Codes from SFF-8024
    ext_compliance_map = {
        0x00: "Unspecified",
        0x01: "100G AOC or 25GAUI C2M AOC",
        0x02: "100GBASE-SR4 or 25GBASE-SR",
        0x03: "100GBASE-LR4 or 25GBASE-LR",
        0x04: "100GBASE-ER4 or 25GBASE-ER",
        0x05: "100GBASE-SR10",
        0x06: "100G CWDM4",
        0x07: "100G PSM4 Parallel SMF",
        0x08: "100G ACC or 25GAUI C2M ACC",
        0x0B: "100GBASE-CR4 or 25GBASE-CR CA-L",
        0x0C: "25GBASE-CR CA-S",
        0x0D: "25GBASE-CR CA-N",
        0x10: "40GBASE-ER4",
        0x11: "4x10GBASE-SR",
        0x12: "40G PSM4 Parallel SMF",
        0x13: "G959.1 P1I1-2D1",
        0x18: "100G ACC or 25GAUI C2M ACC",
        0x19: "100G AOC or 25GAUI C2M AOC",
        0x1A: "100G-CWDM4-OCP",
        0x30: "2.5GBASE-T",
        0x31: "5GBASE-T",
        0x32: "10GBASE-T Short Reach",
        0x33: "10GBASE-T",
    }

    if transceiver_ext in ext_compliance_map:
        print(f"│ Extended Compliance: 0x{transceiver_ext:02X} ({ext_compliance_map[transceiver_ext]})")
    elif transceiver_ext != 0:
        print(f"│ Extended Compliance: 0x{transceiver_ext:02X}")

    print("└" + "─" * 79)

    # Link Lengths Section
    print("\n┌─ LINK LENGTHS " + "─" * 64)
    if info['length_smf_km'] > 0:
        print(f"│ SMF (Single-Mode):   {info['length_smf_km']} km")
    if info['length_smf'] > 0:
        print(f"│ SMF:                 {info['length_smf'] * 100} m")
    if info['length_50um'] > 0:
        print(f"│ 50µm (OM2):          {info['length_50um'] * 10} m")
    if info['length_62_5um'] > 0:
        print(f"│ 62.5µm (OM1):        {info['length_62_5um'] * 10} m")
    if info['length_om3'] > 0:
        print(f"│ 50µm (OM3):          {info['length_om3'] * 10} m")
    if info['length_copper'] > 0:
        print(f"│ Copper:              {info['length_copper']} m")

    # If no lengths are specified
    if all(v == 0 for v in [info['length_smf_km'], info['length_smf'], info['length_50um'],
                             info['length_62_5um'], info['length_om3'], info['length_copper']]):
        print(f"│ No link lengths specified")
    print("└" + "─" * 79)

    # Options and Diagnostics Section
    print("\n┌─ OPTIONS & DIAGNOSTICS " + "─" * 55)
    options = info.get('options', 0)
    print(f"│ Options:             0x{options:04X}")

    # Decode options bits
    if options != 0:
        if options & 0x2000: print(f"│   - RATE_SELECT implemented")
        if options & 0x1000: print(f"│   - TX_DISABLE implemented")
        if options & 0x0800: print(f"│   - TX_FAULT signal implemented")
        if options & 0x0400: print(f"│   - Loss of Signal inverted")
        if options & 0x0200: print(f"│   - Loss of Signal implemented")
        if options & 0x0004: print(f"│   - Tunable transmitter")
        if options & 0x0002: print(f"│   - Cooled transmitter")
        if options & 0x0001: print(f"│   - Power level 2 requirement")

    diag_mon = eeprom.get('diagnostic_monitoring')
    print(f"│ Diagnostic Monitor:  0x{diag_mon:02X}")

    # Decode diagnostic monitoring bits
    if diag_mon != 0:
        if diag_mon & 0x40: print(f"│   - Digital diagnostic monitoring implemented")
        if diag_mon & 0x20: print(f"│   - Internally calibrated")
        if diag_mon & 0x10: print(f"│   - Externally calibrated")
        if diag_mon & 0x08: print(f"│   - Received power: average")
        if diag_mon & 0x04: print(f"│   - Address change required")

    enhanced = eeprom.get('enhanced_options')
    print(f"│ Enhanced Options:    0x{enhanced:02X}")

    # Decode enhanced options bits
    if enhanced != 0:
        if enhanced & 0x80: print(f"│   - Alarm/warning flags implemented")
        if enhanced & 0x40: print(f"│   - Soft TX_DISABLE implemented")
        if enhanced & 0x20: print(f"│   - Soft TX_FAULT implemented")
        if enhanced & 0x10: print(f"│   - Soft RX_LOS implemented")
        if enhanced & 0x08: print(f"│   - Soft RATE_SELECT implemented")

    compliance = eeprom.get('sff8472_compliance')
    compliance_map = {
        0x00: "Unspecified",
        0x01: "Rev 9.3",
        0x02: "Rev 9.5",
        0x03: "Rev 10.2",
        0x04: "Rev 10.4",
        0x05: "Rev 11.0",
        0x06: "Rev 11.3",
        0x07: "Rev 11.4",
        0x08: "Rev 12.0",
    }

    compliance_desc = compliance_map.get(compliance, f"Unknown (0x{compliance:02X})")
    print(f"│ SFF-8472 Compliance: {compliance_desc}")

    print("└" + "─" * 79)

    # Checksums Section
    print("\n┌─ CHECKSUMS " + "─" * 67)
    checksums = info['checksums']
    cc_base_status = "✓ VALID" if checksums['cc_base'] else "✗ INVALID"
    cc_ext_status = "✓ VALID" if checksums['cc_ext'] else "✗ INVALID"

    cc_base = eeprom.get('cc_base')
    cc_ext = eeprom.get('cc_ext')

    print(f"│ CC_BASE (0-62):      0x{cc_base:02X}  {cc_base_status}")
    print(f"│ CC_EXT (64-94):      0x{cc_ext:02X}  {cc_ext_status}")
    print("└" + "─" * 79)

    # Hex Dump Section (if requested)
    if show_hex:
        print("\n┌─ HEX DUMP " + "─" * 68)
        eeprom_bytes = eeprom.to_bytes()
        hex_dump = format_bytes_hex(eeprom_bytes, bytes_per_line=16)
        for line in hex_dump.split('\n'):
            print(f"│ {line}")
        print("└" + "─" * 79)

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Read and display SFP EEPROM information from a binary file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python read_eeprom.py eeprom_a0h.bin
  python read_eeprom.py eeprom_a0h.bin --hex
  python read_eeprom.py /path/to/sfp_eeprom.bin --hex
        """
    )

    parser.add_argument(
        'file',
        type=str,
        help='Path to the EEPROM binary file (256 bytes)'
    )

    parser.add_argument(
        '--hex',
        action='store_true',
        help='Show hex dump of the entire EEPROM'
    )

    args = parser.parse_args()

    # Check if file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{args.file}' not found", file=sys.stderr)
        sys.exit(1)

    # Read the EEPROM file
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate size
    if len(data) != 256:
        print(f"Warning: File size is {len(data)} bytes, expected 256 bytes", file=sys.stderr)
        if len(data) < 256:
            print(f"Error: File is too small to be a valid EEPROM", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Warning: Using first 256 bytes only", file=sys.stderr)
            data = data[:256]

    # Load EEPROM
    try:
        eeprom = SFPA0h.from_bytes(data)
    except Exception as e:
        print(f"Error loading EEPROM: {e}", file=sys.stderr)
        sys.exit(1)

    # Print information
    print_eeprom_info(eeprom, show_hex=args.hex)

    # Exit with error code if checksums are invalid
    checksums = eeprom.validate_checksums()
    if not checksums['cc_base'] or not checksums['cc_ext']:
        sys.exit(2)


if __name__ == '__main__':
    main()
