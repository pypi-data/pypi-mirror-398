import qrcode
from PIL import Image
import os
import logging
from typing import Optional, Dict, Any

class QRISGenerator:
    """
    Class to generate QRIS QR codes with optional logo overlay and CRC16 checksum.
    """
    def __init__(self, config: Dict[str, Any], debug: bool = False):
        """
        Initialize QRISGenerator with config.
        :param config: Dict with 'base_qr_string' and optional 'logo_path'.
        :param debug: Enable debug logging if True.
        """
        if not config.get('base_qr_string'):
            raise ValueError('base_qr_string harus diisi di config')
        self.config = {
            'base_qr_string': config.get('base_qr_string'),
            'logo_path': config.get('logo_path')
        }
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    def generate_qr_with_logo(self, qr_string: str) -> Image.Image:
        """
        Generate a QR image from a QRIS string, with a logo in the center if provided.
        :param qr_string: The QRIS string to encode.
        :return: PIL Image object of the QR code.
        """
        try:
            if not qr_string:
                raise ValueError('qr_string tidak boleh kosong')
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')

            # Add logo if provided and exists
            logo_path = self.config.get('logo_path')
            if logo_path and os.path.exists(logo_path):
                logo = Image.open(logo_path)
                logo_size = int(qr_image.size[0] * 0.2)
                logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
                pos = ((qr_image.size[0] - logo_size) // 2, (qr_image.size[1] - logo_size) // 2)
                # Draw white background for logo
                white_bg = Image.new('RGB', (logo_size + 10, logo_size + 10), 'white')
                qr_image.paste(white_bg, (pos[0] - 5, pos[1] - 5))
                qr_image.paste(logo, pos, mask=logo if logo.mode == 'RGBA' else None)
            return qr_image
        except Exception as e:
            self.logger.error(f"Gagal generate QR: {str(e)}")
            raise Exception(f"Gagal generate QR: {str(e)}")

    def generate_qr_string(self, amount: int) -> str:
        """
        Generate a QRIS string with a specific amount and CRC16 checksum.
        :param amount: The nominal amount (int, >0)
        :return: QRIS string with amount and checksum
        """
        try:
            if not amount or amount <= 0:
                raise ValueError('Nominal harus lebih besar dari 0')
            base_qr = self.config['base_qr_string']
            if "5802ID" not in base_qr:
                raise Exception("Format QRIS tidak valid")
            final_amount = int(amount)
            qris_base = base_qr[:-4].replace("010211", "010212")
            nominal_str = str(final_amount)
            nominal_tag = f"54{len(nominal_str):02d}{nominal_str}"
            insert_position = qris_base.find("5802ID")
            qris_with_nominal = qris_base[:insert_position] + nominal_tag + qris_base[insert_position:]
            checksum = self._calculate_crc16(qris_with_nominal)
            return qris_with_nominal + checksum
        except Exception as e:
            self.logger.error(f"Gagal generate QR string: {str(e)}")
            raise Exception(f"Gagal generate QR string: {str(e)}")

    def _calculate_crc16(self, data: str) -> str:
        """
        Calculate CRC16-CCITT checksum for a QRIS string.
        :param data: The string to calculate checksum for.
        :return: 4-character uppercase hex string
        """
        try:
            if not data:
                raise ValueError('String tidak boleh kosong')
            crc = 0xFFFF
            for byte in data.encode('utf-8'):
                crc ^= byte << 8
                for _ in range(8):
                    if crc & 0x8000:
                        crc = (crc << 1) ^ 0x1021
                    else:
                        crc = crc << 1
                crc &= 0xFFFF
            return f"{crc:04X}"
        except Exception as e:
            self.logger.error(f"Gagal kalkulasi CRC16: {str(e)}")
            raise Exception(f"Gagal kalkulasi CRC16: {str(e)}") 