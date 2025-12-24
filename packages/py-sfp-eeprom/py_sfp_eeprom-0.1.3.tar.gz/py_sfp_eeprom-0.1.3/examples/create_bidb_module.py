import sys
from pathlib import Path

# Add the parent directory to the path to import the library
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sfp_eeprom import SFPA0h


def main():
    print("Creating an example BIDB XGS-PON module EEPROM...")

    # Create new EEPROM
    eeprom = SFPA0h()

    # Set identification
    eeprom.set('identifier', SFPA0h.IDENTIFIER_SFP)
    eeprom.set('ext_identifier', SFPA0h.EXT_IDENTIFIER_SFF)
    eeprom.set('connector', SFPA0h.CONNECTOR_SC)

    # Set transceiver codes
    eeprom.set_transceiver_codes(
        SFPA0h.TRANSCEIVER_10GBASE_LR,     # 10GBASE-LR
        SFPA0h.TRANSCEIVER_FC_200_MBYTES,  # 200 MBd FC
        SFPA0h.TRANSCEIVER_FC_100_MBYTES,  # 100 MBd FC
    )

    # Set encoding and bit rate
    eeprom.set('encoding', SFPA0h.ENCODING_NRZ)
    eeprom.set('br_nominal', 100)  # 10 Gbps (100 * 100 Mbps)

    # Set link lengths
    eeprom.set('length_smf_km', 20)   # 20 km (automatically sets length_smf to 200)

    # Set vendor information
    eeprom.set('vendor_name', 'BIDB')
    eeprom.set('vendor_pn', 'X-ONU-SFPP')
    eeprom.set('vendor_rev', 'A-01')
    eeprom.set('vendor_sn', 'BIDB12345678')
    eeprom.set('date_code', '251202')  # 2025-12-02

    # Set wavelength
    eeprom.set('wavelength', 1270)  # 1270 nm (0x04F6)

    # Set diagnostic monitoring
    eeprom.set('diagnostic_monitoring',
               SFPA0h.DIAG_MONITORING_REQUIRED |
               SFPA0h.DIAG_MONITORING_INTERNALLY_CALIBRATED |
               SFPA0h.DIAG_MONITORING_RX_POWER_AVG)

    # Set enhanced options
    eeprom.set('enhanced_options',
               SFPA0h.ENHANCED_ALARM_WARNING |
               SFPA0h.ENHANCED_SOFT_TX_DISABLE |
               SFPA0h.ENHANCED_SOFT_TX_FAULT |
               SFPA0h.ENHANCED_SOFT_RX_LOS)

    # Set SFF-8472 compliance
    eeprom.set('sff8472_compliance', SFPA0h.SFF8472_REV_11_0)

    # Fill vendor specific area with 0x00 (bytes 96-127)
    eeprom._data[96:128] = bytes([0x00] * 32)

    # Fill reserved area with 0xFF (bytes 128-255)
    eeprom._data[128:256] = bytes([0xFF] * 128)

    # Export to file
    output_file = 'bidb-module.bin'
    with open(output_file, 'wb') as f:
        f.write(eeprom.to_bytes())

    print(f"Created {output_file}")


if __name__ == '__main__':
    main()
