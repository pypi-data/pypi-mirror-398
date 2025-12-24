import unittest
from unittest.mock import patch
from qris_payment import QRISPayment, PaymentChecker, QRISGenerator
from PIL import Image

class TestQRISPayment(unittest.TestCase):
    def setUp(self):
        self.config = {
            'auth_username': 'agin',
            'auth_token': '2169948:r2Pjf3QnVEGTxSsvqK5DX01AlHdghyWk',
            'base_qr_string': '00020101021126670016COM.NOBUBANK.WWW01189360050300000879140214158455875489000303UMI51440014ID.CO.QRIS.WWW0215ID20253762751400303UMI5204541153033605802ID5920AGIN STORE OK21699486006CIAMIS61054621162070703A0163049492',
            'logo_path': False
        }
        self.qris = QRISPayment(self.config)

    def test_generate_qr_string(self):
        qr_string = self.qris.qr_generator.generate_qr_string(10000)
        self.assertIn('54', qr_string)
        self.assertTrue(qr_string.endswith(qr_string[-4:]))  # Ada CRC

    def test_generate_qr_with_logo(self):
        qr_string = self.qris.qr_generator.generate_qr_string(10000)
        img = self.qris.qr_generator.generate_qr_with_logo(qr_string)
        self.assertIsInstance(img, Image.Image)

    @patch('qris_payment.payment_checker.requests.post')
    def test_check_payment_paid(self, mock_post):
        # Mock response untuk transaksi PAID
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {
            'status': True,
            'data': [
                {
                    'amount': '10000',
                    'date': '2024-06-01 12:00',
                    'qris': 'static',
                    'type': 'CR',
                    'issuer_reff': 'REF123',
                    'brand_name': 'BRAND',
                    'buyer_reff': 'BUYER'
                }
            ]
        }
        result = self.qris.check_payment('REF123', 10000)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['status'], 'PAID')
        self.assertEqual(result['data']['amount'], 10000)
        self.assertEqual(result['data']['reference'], 'REF123')

    @patch('qris_payment.payment_checker.requests.post')
    def test_check_payment_unpaid(self, mock_post):
        # Mock response untuk transaksi UNPAID
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {
            'status': True,
            'data': []
        }
        result = self.qris.check_payment('REF123', 10000)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['status'], 'UNPAID')
        self.assertEqual(result['data']['amount'], 10000)
        self.assertEqual(result['data']['reference'], 'REF123')

    @patch('qris_payment.payment_checker.requests.post')
    def test_check_payment_error(self, mock_post):
        # Mock response error
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 500
        result = self.qris.check_payment('REF123', 10000)
        self.assertFalse(result['success'])
        self.assertIn('Gagal cek status pembayaran', result['error'])

if __name__ == '__main__':
    unittest.main() 