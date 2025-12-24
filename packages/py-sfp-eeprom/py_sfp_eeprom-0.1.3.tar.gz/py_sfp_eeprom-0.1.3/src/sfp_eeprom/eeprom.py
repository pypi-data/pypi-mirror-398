"""
SFP EEPROM A0h implementation based on SFF-8472 specification.
"""

import struct
from typing import Dict, Any, Optional, Union


class SFPA0h:
    """
    SFP EEPROM A0h (256 bytes) based on SFF-8472 specification.

    This class manages the lower page (A0h) of the SFP EEPROM which contains
    identification and vendor information.
    """

    # EEPROM size is 256 bytes
    EEPROM_SIZE = 256

    # Field offsets and sizes based on SFF-8472 Table 3-1
    FIELDS = {
        'identifier': (0, 1),           # Type of serial transceiver
        'ext_identifier': (1, 1),       # Extended identifier
        'connector': (2, 1),            # Code for connector type
        'transceiver': (3, 8),          # Transceiver compliance codes
        'encoding': (11, 1),            # Code for serial encoding algorithm
        'br_nominal': (12, 1),          # Nominal signaling rate
        'rate_identifier': (13, 1),     # Type of rate select functionality
        'length_smf_km': (14, 1),       # Link length supported for SMF, km
        'length_smf': (15, 1),          # Link length supported for SMF, 100m
        'length_50um': (16, 1),         # Link length supported for 50um OM2, 10m
        'length_62_5um': (17, 1),       # Link length supported for 62.5um OM1, 10m
        'length_copper': (18, 1),       # Link length supported for copper, 1m
        'length_om3': (19, 1),          # Link length supported for 50um OM3, 10m
        'vendor_name': (20, 16),        # SFP vendor name (ASCII)
        'transceiver_ext': (36, 1),     # Extended transceiver codes
        'vendor_oui': (37, 3),          # SFP vendor IEEE company ID
        'vendor_pn': (40, 16),          # Part number provided by SFP vendor (ASCII)
        'vendor_rev': (56, 4),          # Revision level for part number (ASCII)
        'wavelength': (60, 2),          # Laser wavelength (or copper cable attenuation)
        'unallocated_1': (62, 1),       # Unallocated
        'cc_base': (63, 1),             # Check code for base ID fields (0-62)
        'options': (64, 2),             # Indicates implemented options
        'br_max': (66, 1),              # Upper bit rate margin
        'br_min': (67, 1),              # Lower bit rate margin
        'vendor_sn': (68, 16),          # Serial number (ASCII)
        'date_code': (84, 8),           # Vendor's mfg date code
        'diagnostic_monitoring': (92, 1), # Diagnostic monitoring type
        'enhanced_options': (93, 1),    # Enhanced options
        'sff8472_compliance': (94, 1),  # SFF-8472 compliance
        'cc_ext': (95, 1),              # Check code for extended ID fields (64-94)
        'vendor_specific': (96, 32),    # Vendor specific data
        'reserved': (128, 128),         # Reserved for SFF-8079
    }

    # Identifier type constants
    IDENTIFIER_UNKNOWN = 0x00
    IDENTIFIER_GBIC = 0x01
    IDENTIFIER_SOLDERED = 0x02
    IDENTIFIER_SFP = 0x03
    IDENTIFIER_XBI = 0x04
    IDENTIFIER_XENPAK = 0x05
    IDENTIFIER_XFP = 0x06
    IDENTIFIER_XFF = 0x07
    IDENTIFIER_XFP_E = 0x08
    IDENTIFIER_XPAK = 0x09
    IDENTIFIER_X2 = 0x0A
    IDENTIFIER_DWDM_SFP = 0x0B
    IDENTIFIER_QSFP = 0x0C
    IDENTIFIER_QSFP_PLUS = 0x0D
    IDENTIFIER_CXP = 0x0E
    IDENTIFIER_HD_4X = 0x0F
    IDENTIFIER_HD_8X = 0x10
    IDENTIFIER_QSFP28 = 0x11
    IDENTIFIER_CXP2 = 0x12
    IDENTIFIER_CDFP = 0x13
    IDENTIFIER_HD_4X_FANOUT = 0x14
    IDENTIFIER_HD_8X_FANOUT = 0x15
    IDENTIFIER_CDFP_STYLE3 = 0x16
    IDENTIFIER_MICRO_QSFP = 0x17

    # Identifier types (byte 0)
    IDENTIFIER_TYPES = {
        0x00: 'Unknown or unspecified',
        0x01: 'GBIC',
        0x02: 'Module/connector soldered to motherboard',
        0x03: 'SFP/SFP+/SFP28',
        0x04: '300 pin XBI',
        0x05: 'XENPAK',
        0x06: 'XFP',
        0x07: 'XFF',
        0x08: 'XFP-E',
        0x09: 'XPAK',
        0x0A: 'X2',
        0x0B: 'DWDM-SFP/SFP+',
        0x0C: 'QSFP',
        0x0D: 'QSFP+ or later',
        0x0E: 'CXP or later',
        0x0F: 'Shielded Mini Multilane HD 4X',
        0x10: 'Shielded Mini Multilane HD 8X',
        0x11: 'QSFP28 or later',
        0x12: 'CXP2 (aka CXP28) or later',
        0x13: 'CDFP (Style 1/Style2)',
        0x14: 'Shielded Mini Multilane HD 4X Fanout Cable',
        0x15: 'Shielded Mini Multilane HD 8X Fanout Cable',
        0x16: 'CDFP (Style 3)',
        0x17: 'microQSFP',
    }

    # Connector type constants
    CONNECTOR_UNKNOWN = 0x00
    CONNECTOR_SC = 0x01
    CONNECTOR_FC_STYLE1 = 0x02
    CONNECTOR_FC_STYLE2 = 0x03
    CONNECTOR_BNC_TNC = 0x04
    CONNECTOR_FC_COAX = 0x05
    CONNECTOR_FIBER_JACK = 0x06
    CONNECTOR_LC = 0x07
    CONNECTOR_MT_RJ = 0x08
    CONNECTOR_MU = 0x09
    CONNECTOR_SG = 0x0A
    CONNECTOR_OPTICAL_PIGTAIL = 0x0B
    CONNECTOR_MPO_1X12 = 0x0C
    CONNECTOR_MPO_2X16 = 0x0D
    CONNECTOR_HSSDC_II = 0x20
    CONNECTOR_COPPER_PIGTAIL = 0x21
    CONNECTOR_RJ45 = 0x22
    CONNECTOR_NO_SEPARABLE = 0x23
    CONNECTOR_MXC_2X16 = 0x24

    # Connector types (byte 2)
    CONNECTOR_TYPES = {
        0x00: 'Unknown or unspecified',
        0x01: 'SC (Subscriber Connector)',
        0x02: 'Fibre Channel Style 1 copper connector',
        0x03: 'Fibre Channel Style 2 copper connector',
        0x04: 'BNC/TNC (Bayonet/Threaded Neill-Concelman)',
        0x05: 'Fibre Channel coax headers',
        0x06: 'Fiber Jack',
        0x07: 'LC (Lucent Connector)',
        0x08: 'MT-RJ (Mechanical Transfer - Registered Jack)',
        0x09: 'MU (Multiple Optical)',
        0x0A: 'SG',
        0x0B: 'Optical Pigtail',
        0x0C: 'MPO 1x12 (Multifiber Parallel Optic)',
        0x0D: 'MPO 2x16',
        0x20: 'HSSDC II (High Speed Serial Data Connector)',
        0x21: 'Copper pigtail',
        0x22: 'RJ45 (Registered Jack)',
        0x23: 'No separable connector',
        0x24: 'MXC 2x16',
    }

    # Encoding type constants
    ENCODING_UNSPECIFIED = 0x00
    ENCODING_8B10B = 0x01
    ENCODING_4B5B = 0x02
    ENCODING_NRZ = 0x03
    ENCODING_MANCHESTER = 0x04
    ENCODING_SONET = 0x05
    ENCODING_64B66B = 0x06
    ENCODING_256B257B = 0x07

    # Extended identifier constants
    EXT_IDENTIFIER_GBIC = 0x00
    EXT_IDENTIFIER_SFF = 0x04

    # SFF-8472 Compliance (Byte 94) constants
    SFF8472_UNSPECIFIED = 0x00
    SFF8472_REV_9_3 = 0x01
    SFF8472_REV_9_5 = 0x02
    SFF8472_REV_10_2 = 0x03
    SFF8472_REV_10_4 = 0x04
    SFF8472_REV_11_0 = 0x05
    SFF8472_REV_11_3 = 0x06
    SFF8472_REV_11_4 = 0x07
    SFF8472_REV_12_0 = 0x08

    # Diagnostic Monitoring Type (Byte 92) bit flags
    DIAG_MONITORING_REQUIRED = 0x40          # Bit 6: Digital diagnostic monitoring implemented
    DIAG_MONITORING_INTERNALLY_CALIBRATED = 0x20   # Bit 5: Internally calibrated
    DIAG_MONITORING_EXTERNALLY_CALIBRATED = 0x10   # Bit 4: Externally calibrated
    DIAG_MONITORING_RX_POWER_AVG = 0x08      # Bit 3: Received power measurement type (0=OMA, 1=average)
    DIAG_MONITORING_ADDR_CHANGE = 0x04       # Bit 2: Address change required

    # Options (Bytes 64-65) bit flags
    # Byte 64 (high byte of options)
    OPTIONS_RATE_SELECT = 0x2000             # Bit 13: RATE_SELECT implemented
    OPTIONS_TX_DISABLE = 0x1000              # Bit 12: TX_DISABLE implemented
    OPTIONS_TX_FAULT = 0x0800                # Bit 11: TX_FAULT signal implemented
    OPTIONS_RX_LOS_INVERTED = 0x0400         # Bit 10: Loss of Signal inverted
    OPTIONS_RX_LOS = 0x0200                  # Bit 9: Loss of Signal implemented
    # Byte 65 (low byte of options)
    OPTIONS_TUNABLE = 0x0004                 # Bit 2: Tunable transmitter technology
    OPTIONS_COOLED_TRANSMITTER = 0x0002      # Bit 1: Cooled transmitter implemented
    OPTIONS_POWER_LEVEL_2 = 0x0001           # Bit 0: Power level 2 requirement

    # Enhanced Options (Byte 93) bit flags
    ENHANCED_ALARM_WARNING = 0x80            # Bit 7: Optional alarm/warning flags implemented
    ENHANCED_SOFT_TX_DISABLE = 0x40          # Bit 6: Soft TX_DISABLE implemented
    ENHANCED_SOFT_TX_FAULT = 0x20            # Bit 5: Soft TX_FAULT implemented
    ENHANCED_SOFT_RX_LOS = 0x10              # Bit 4: Soft RX_LOS implemented
    ENHANCED_SOFT_RATE_SELECT = 0x08         # Bit 3: Soft RATE_SELECT implemented

    # Transceiver compliance code constants (bit positions in bytes 3-10)
    # Byte 3 (index 0): 10G Ethernet Compliance Codes
    TRANSCEIVER_10GBASE_ER = (0, 0x80)   # 10GBASE-ER
    TRANSCEIVER_10GBASE_LRM = (0, 0x40)  # 10GBASE-LRM
    TRANSCEIVER_10GBASE_LR = (0, 0x20)   # 10GBASE-LR
    TRANSCEIVER_10GBASE_SR = (0, 0x10)   # 10GBASE-SR

    # Byte 6 (index 3): Ethernet Compliance Codes
    TRANSCEIVER_BASE_PX = (3, 0x80)      # BASE-PX
    TRANSCEIVER_BASE_BX10 = (3, 0x40)    # BASE-BX10
    TRANSCEIVER_100BASE_FX = (3, 0x20)   # 100BASE-FX
    TRANSCEIVER_100BASE_LX = (3, 0x10)   # 100BASE-LX/LX10
    TRANSCEIVER_1000BASE_T = (3, 0x08)   # 1000BASE-T
    TRANSCEIVER_1000BASE_CX = (3, 0x04)  # 1000BASE-CX
    TRANSCEIVER_1000BASE_LX = (3, 0x02)  # 1000BASE-LX
    TRANSCEIVER_1000BASE_SX = (3, 0x01)  # 1000BASE-SX

    # Byte 4 (index 1): Fibre Channel Speed
    TRANSCEIVER_FC_1200_MBYTES = (1, 0x80)  # 1200 MBytes/sec
    TRANSCEIVER_FC_800_MBYTES = (1, 0x40)   # 800 MBytes/sec
    TRANSCEIVER_FC_1600_MBYTES = (1, 0x20)  # 1600 MBytes/sec
    TRANSCEIVER_FC_400_MBYTES = (1, 0x10)   # 400 MBytes/sec
    TRANSCEIVER_FC_3200_MBYTES = (1, 0x08)  # 3200 MBytes/sec (modern)
    TRANSCEIVER_FC_200_MBYTES = (1, 0x04)   # 200 MBytes/sec
    TRANSCEIVER_FC_EXTENDED = (1, 0x02)     # See byte 36 for extended speeds
    TRANSCEIVER_FC_100_MBYTES = (1, 0x01)   # 100 MBytes/sec

    # Byte 7 (index 4): Fibre Channel Link Length
    TRANSCEIVER_FC_VERY_LONG = (4, 0x80)  # Very long distance (V)
    TRANSCEIVER_FC_SHORT = (4, 0x40)      # Short distance (S)
    TRANSCEIVER_FC_INTERMEDIATE = (4, 0x20)  # Intermediate distance (I)
    TRANSCEIVER_FC_LONG = (4, 0x10)       # Long distance (L)
    TRANSCEIVER_FC_MEDIUM = (4, 0x08)     # Medium distance (M)

    # Byte 8 (index 5): Fibre Channel Technology
    TRANSCEIVER_FC_SHORTWAVE = (5, 0x04)  # Shortwave laser (SN)
    TRANSCEIVER_FC_LONGWAVE = (5, 0x02)   # Longwave laser (LC)
    TRANSCEIVER_FC_ELECTRICAL = (5, 0x01) # Electrical inter-enclosure (EL)

    # Byte 9 (index 6): SFP+ Cable Technology
    TRANSCEIVER_LIMITING = (6, 0x40)      # Limiting (SFP specific bit)
    TRANSCEIVER_ACTIVE_CABLE = (6, 0x08)  # Active Cable
    TRANSCEIVER_PASSIVE_CABLE = (6, 0x04) # Passive Cable

    # Byte 10 (index 7): Fibre Channel Transmission Media
    TRANSCEIVER_TWIN_AXIAL = (7, 0x80)    # Twin Axial Pair (TW)
    TRANSCEIVER_TWISTED_PAIR = (7, 0x40)  # Twisted Pair (TP)
    TRANSCEIVER_MINIATURE_COAX = (7, 0x20)  # Miniature Coax (MI)
    TRANSCEIVER_VIDEO_COAX = (7, 0x10)    # Video Coax (TV)
    TRANSCEIVER_MULTIMODE_62_5 = (7, 0x08)  # Multi-mode 62.5µm (M6)
    TRANSCEIVER_MULTIMODE_50 = (7, 0x04)  # Multi-mode 50µm (M5)
    TRANSCEIVER_MULTIMODE_OM3 = (7, 0x02) # Multi-mode 50µm (OM3)
    TRANSCEIVER_SINGLE_MODE = (7, 0x01)   # Single Mode (SM)

    def __init__(self, data: Optional[bytes] = None):
        """
        Initialize SFP A0h EEPROM.

        Args:
            data: Optional 256-byte EEPROM data to load. If None, creates empty EEPROM.
        """
        if data is None:
            # Initialize with zeros
            self._data = bytearray(self.EEPROM_SIZE)
        else:
            if len(data) != self.EEPROM_SIZE:
                raise ValueError(f"EEPROM data must be exactly {self.EEPROM_SIZE} bytes")
            self._data = bytearray(data)

    def _get_field(self, field_name: str) -> bytes:
        """Get raw bytes for a field."""
        if field_name not in self.FIELDS:
            raise ValueError(f"Unknown field: {field_name}")
        offset, size = self.FIELDS[field_name]
        return bytes(self._data[offset:offset + size])

    def _set_field(self, field_name: str, value: Union[bytes, int, str]):
        """Set raw bytes for a field."""
        if field_name not in self.FIELDS:
            raise ValueError(f"Unknown field: {field_name}")
        offset, size = self.FIELDS[field_name]

        if isinstance(value, int):
            if size == 1:
                self._data[offset] = value & 0xFF
            elif size == 2:
                self._data[offset:offset + 2] = struct.pack('>H', value)
            elif size == 3:
                self._data[offset:offset + 3] = value.to_bytes(3, 'big')
            else:
                raise ValueError(f"Cannot set integer for field with size {size}")
        elif isinstance(value, str):
            # Convert string to ASCII bytes, padding with spaces
            encoded = value.encode('ascii')[:size]
            padded = encoded.ljust(size, b' ')
            self._data[offset:offset + size] = padded
        elif isinstance(value, bytes):
            if len(value) > size:
                raise ValueError(f"Value too large for field {field_name} (max {size} bytes)")
            # Pad with zeros if needed
            padded = value.ljust(size, b'\x00')
            self._data[offset:offset + size] = padded
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

    def get(self, field_name: str) -> Any:
        """
        Get a field value in a human-readable format.

        Args:
            field_name: Name of the field to retrieve

        Returns:
            Field value (int, str, or bytes depending on field type)
        """
        raw = self._get_field(field_name)

        # String fields
        if field_name in ['vendor_name', 'vendor_pn', 'vendor_rev', 'vendor_sn']:
            return raw.rstrip(b' \x00').decode('ascii', errors='ignore')

        # Date code (YYMMDD + lot code)
        if field_name == 'date_code':
            return raw.decode('ascii', errors='ignore')

        # Single byte integer fields
        if self.FIELDS[field_name][1] == 1:
            return raw[0]

        # Two byte integer fields
        if field_name == 'wavelength':
            return struct.unpack('>H', raw)[0]

        # Multi-byte fields
        if field_name == 'vendor_oui':
            return raw.hex().upper()

        if field_name == 'options':
            return struct.unpack('>H', raw)[0]

        # Default: return raw bytes
        return raw

    def set(self, field_name: str, value: Union[int, str, bytes]):
        """
        Set a field value.

        Args:
            field_name: Name of the field to set
            value: Value to set (int, str, or bytes)
        """
        self._set_field(field_name, value)

        # Auto-calculate related SMF length fields
        # length_smf_km (byte 14) is in km, length_smf (byte 15) is in 100m units
        if field_name == 'length_smf_km' and isinstance(value, int):
            # Set length_smf to match: 1 km = 10 units of 100m
            self._set_field('length_smf', value * 10)
        elif field_name == 'length_smf' and isinstance(value, int):
            # Set length_smf_km to match: 10 units of 100m = 1 km
            self._set_field('length_smf_km', value // 10)

        # Recalculate checksums if we modified a checksummed field
        if field_name != 'cc_base' and self.FIELDS[field_name][0] < 63:
            self._update_cc_base()
        if field_name != 'cc_ext' and 64 <= self.FIELDS[field_name][0] < 95:
            self._update_cc_ext()

    def set_transceiver_codes(self, *codes):
        """
        Set transceiver compliance codes using named constants.

        Args:
            *codes: Variable number of transceiver code constants (tuples of byte_index, bitmask)
                   e.g., SFPA0h.TRANSCEIVER_1000BASE_LX, SFPA0h.TRANSCEIVER_SINGLE_MODE

        Example:
            eeprom.set_transceiver_codes(
                SFPA0h.TRANSCEIVER_10GBASE_LR,
                SFPA0h.TRANSCEIVER_SINGLE_MODE
            )
        """
        # Start with zeros
        transceiver_bytes = bytearray(8)

        # Set bits for each code
        for code in codes:
            if isinstance(code, tuple) and len(code) == 2:
                byte_index, bitmask = code
                if 0 <= byte_index < 8:
                    transceiver_bytes[byte_index] |= bitmask
                else:
                    raise ValueError(f"Invalid transceiver code byte index: {byte_index}")
            else:
                raise ValueError(f"Invalid transceiver code format: {code}")

        # Set the transceiver field
        self.set('transceiver', bytes(transceiver_bytes))

    def _calculate_checksum(self, start: int, end: int) -> int:
        """Calculate checksum for a range of bytes."""
        total = sum(self._data[start:end])
        return total & 0xFF

    def _update_cc_base(self):
        """Update the base ID checksum (CC_BASE at byte 63)."""
        checksum = self._calculate_checksum(0, 63)
        self._data[63] = checksum

    def _update_cc_ext(self):
        """Update the extended ID checksum (CC_EXT at byte 95)."""
        checksum = self._calculate_checksum(64, 95)
        self._data[95] = checksum

    def validate_checksums(self) -> Dict[str, bool]:
        """
        Validate both checksums.

        Returns:
            Dictionary with 'cc_base' and 'cc_ext' validation results
        """
        cc_base_calculated = self._calculate_checksum(0, 63)
        cc_ext_calculated = self._calculate_checksum(64, 95)

        return {
            'cc_base': self._data[63] == cc_base_calculated,
            'cc_ext': self._data[95] == cc_ext_calculated,
        }

    def update_checksums(self):
        """Update both CC_BASE and CC_EXT checksums."""
        self._update_cc_base()
        self._update_cc_ext()

    def to_bytes(self) -> bytes:
        """
        Export EEPROM as 256 bytes.

        Returns:
            Complete EEPROM data as bytes
        """
        return bytes(self._data)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'SFPA0h':
        """
        Create EEPROM object from binary data.

        Args:
            data: 256 bytes of EEPROM data

        Returns:
            New SFPA0h instance
        """
        return cls(data)

    def get_info(self) -> Dict[str, Any]:
        """
        Get a dictionary of human-readable EEPROM information.

        Returns:
            Dictionary containing decoded EEPROM fields
        """
        info = {}

        # Basic identification
        identifier = self.get('identifier')
        info['identifier'] = {
            'value': identifier,
            'description': self.IDENTIFIER_TYPES.get(identifier, 'Unknown')
        }

        connector = self.get('connector')
        info['connector'] = {
            'value': connector,
            'description': self.CONNECTOR_TYPES.get(connector, 'Unknown')
        }

        # Vendor information
        info['vendor_name'] = self.get('vendor_name')
        info['vendor_oui'] = self.get('vendor_oui')
        info['vendor_pn'] = self.get('vendor_pn')
        info['vendor_rev'] = self.get('vendor_rev')
        info['vendor_sn'] = self.get('vendor_sn')
        info['date_code'] = self.get('date_code')

        # Transceiver specifications
        info['encoding'] = self.get('encoding')
        info['br_nominal'] = self.get('br_nominal')
        info['wavelength'] = self.get('wavelength')

        # Options and diagnostics
        info['options'] = self.get('options')

        # Link lengths
        info['length_smf_km'] = self.get('length_smf_km')
        info['length_smf'] = self.get('length_smf')
        info['length_50um'] = self.get('length_50um')
        info['length_62_5um'] = self.get('length_62_5um')
        info['length_copper'] = self.get('length_copper')
        info['length_om3'] = self.get('length_om3')

        # Checksums
        checksums = self.validate_checksums()
        info['checksums'] = checksums

        return info

    def __repr__(self) -> str:
        """String representation of EEPROM."""
        vendor = self.get('vendor_name')
        pn = self.get('vendor_pn')
        sn = self.get('vendor_sn')
        return f"SFPA0h(vendor='{vendor}', pn='{pn}', sn='{sn}')"
