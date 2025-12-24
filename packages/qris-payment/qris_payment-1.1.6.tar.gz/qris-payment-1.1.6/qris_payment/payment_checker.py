import requests
from datetime import datetime
import logging
from typing import Optional, Dict, Any

class PaymentChecker:
    """
    Class to check payment status via external API, with robust validation and error handling.
    """
    def __init__(self, config: Dict[str, Any], debug: bool = False):
        """
        Initialize PaymentChecker with required config.
        :param config: Dict with 'auth_username' and 'auth_token'.
        :param debug: Enable debug logging if True.
        """
        if not config.get('auth_username'):
            raise ValueError('auth_username harus diisi')
        if not config.get('auth_token'):
            raise ValueError('auth_token harus diisi')
        self.config = {
            'auth_username': config.get('auth_username'),
            'auth_token': config.get('auth_token')
        }
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    def check_payment_status(self, reference: Optional[str], amount: Optional[int]) -> Dict[str, Any]:
        """
        Check payment status for a given amount (reference is ignored, only for compatibility).
        :param reference: (Ignored)
        :param amount: Amount to check (int)
        :return: Dict with 'success', 'data' or 'error'
        """
        try:
            if not amount or amount <= 0:
                raise ValueError('Amount harus diisi dengan benar')

            url = 'https://sawargipay.net/api/mutasi'
            headers = {'Content-Type': 'application/json'}
            payload = {
                'auth_username': self.config['auth_username'],
                'auth_token': self.config['auth_token']
            }
            if self.debug:
                self.logger.debug('Mengirim request ke API...')
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if self.debug:
                self.logger.debug(f'Response status: {response.status_code}')
                self.logger.debug(f'Response text: {response.text}')
            if not response.ok:
                raise Exception(f"HTTP error: {response.status_code}")
            data = response.json()
            if not data.get('status') or not data.get('data'):
                raise Exception('Response tidak valid dari server')

            transactions = data['data']
            now = datetime.now()
            matching_transactions = []
            for tx in transactions:
                try:
                    tx_amount = int(tx['amount'])
                    # Handle two date formats
                    try:
                        tx_date = datetime.strptime(tx['date'], '%Y-%m-%d %H:%M')
                    except ValueError:
                        tx_date = datetime.strptime(tx['date'], '%Y-%m-%d %H:%M:%S')
                    time_diff = (now - tx_date).total_seconds() * 1000  # ms
                    match = (
                        tx_amount == amount and
                        tx.get('qris') == 'static' and  # HARUS persis static
                        tx.get('type') == 'CR' and
                        time_diff <= 10 * 60 * 1000  # 10 menit (bukan 5 menit)
                    )
                    if self.debug:
                        self.logger.debug({
                            'txAmount': tx_amount,
                            'amount': amount,
                            'qris': tx.get('qris'),
                            'type': tx.get('type'),
                            'txDate': tx['date'],
                            'now': now.isoformat(),
                            'timeDiff': time_diff,
                            'match': match
                        })
                    if match:
                        matching_transactions.append(tx)
                except Exception as e:
                    self.logger.warning(f"Error parsing transaction: {e} | TX: {tx}")
                    continue

            if matching_transactions:
                def parse_date(x):
                    try:
                        return datetime.strptime(x['date'], '%Y-%m-%d %H:%M')
                    except ValueError:
                        return datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S')
                latest_transaction = max(matching_transactions, key=parse_date)
                return {
                    'success': True,
                    'data': {
                        'status': 'PAID',
                        'amount': int(latest_transaction['amount']),
                        'date': latest_transaction['date'],
                        'brand_name': latest_transaction.get('brand_name'),
                        'buyer_reff': latest_transaction.get('buyer_reff')
                    }
                }

            return {
                'success': True,
                'data': {
                    'status': 'UNPAID',
                    'amount': amount
                }
            }
        except Exception as error:
            self.logger.error(f'Gagal cek status pembayaran: {str(error)}')
            return {
                'success': False,
                'error': f'Gagal cek status pembayaran: {str(error)}'
            }