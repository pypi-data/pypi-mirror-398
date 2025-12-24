import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'qris_payment'))

from payment_checker import PaymentChecker
import logging

# Setup logging untuk debug
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_recent_transaction():
    print("=== TEST RECENT TRANSACTION ===")
    
    config = {
        'auth_username': 'agin',
        'auth_token': '2169948:r2Pjf3QnVEGTxSsvqK5DX01AlHdghyWk'
    }
    
    # Test dengan amount 3148 yang baru masuk (11:17)
    amount = 3148
    
    print(f"Testing amount: {amount}")
    print("Transaksi ini baru masuk: 2025-07-16 11:17, amount: 3148, type: CR, qris: static")
    print()
    
    try:
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
        else:
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_recent_transaction() 