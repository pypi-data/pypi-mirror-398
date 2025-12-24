from .qr_generator import QRISGenerator
from .payment_checker import PaymentChecker

class QRISPayment:
    """
    Fasad utama untuk generate QRIS dan cek status pembayaran.
    Config wajib:
      - auth_username
      - auth_token
      - base_qr_string
      - logo_path (opsional)
    """
    def __init__(self, config):
        self.qr_generator = QRISGenerator(config)
        self.payment_checker = PaymentChecker(config)

    def generate_qr(self, amount):
        qr_string = self.qr_generator.generate_qr_string(amount)
        qr_image = self.qr_generator.generate_qr_with_logo(qr_string)
        return {
            'qr_string': qr_string,
            'qr_image': qr_image
        }

    def check_payment(self, reference, amount):
        return self.payment_checker.check_payment_status(reference, amount) 