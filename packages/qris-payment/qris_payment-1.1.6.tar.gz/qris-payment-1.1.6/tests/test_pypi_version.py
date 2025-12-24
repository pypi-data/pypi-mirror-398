import sys
import os
# Test versi PyPI yang baru diupload
from qris_payment.payment_checker import PaymentChecker
import logging

# Setup logging untuk debug
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_pypi_version():
    print("=== TEST VERSI PYPI 1.1.5 ===")
    
    config = {
        'auth_username': 'agin',
        'auth_token': '2169948:r2Pjf3QnVEGTxSsvqK5DX01AlHdghyWk'
    }
    
    # Test dengan amount 3148 yang baru masuk (11:17)
    amount = 3148
    
    print(f"Testing amount: {amount}")
    print("Transaksi ini baru masuk: 2025-07-16 11:17, amount: 3148, type: CR, qris: static")
    print("Menggunakan versi PyPI 1.1.5 dengan filter waktu 10 menit")
    print()
    
    try:
        # Test versi PyPI dengan debug mode
        checker = PaymentChecker(config, debug=True)
        result = checker.check_payment_status(None, amount)
        
        print("=== RESULT ===")
        print(f"Success: {result['success']}")
        if result['success']:
            print(f"Status: {result['data']['status']}")
            if result['data']['status'] == 'PAID':
                print("Detail transaksi:")
                for k, v in result['data'].items():
                    print(f"  {k}: {v}")
                print("\n✅ VERSI PYPI BERHASIL! Filter 10 menit bekerja dengan baik!")
            else:
                print("❌ Masih UNPAID - kemungkinan transaksi sudah lewat dari 10 menit")
        else:
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_pypi_version() 