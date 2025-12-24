from .futures_transaction_records import FuturesTransactionRecords
from .margin_transaction_records import MarginTransactionRecords
from .p2p_transaction_records import P2PTransactionRecords
from .spot_transaction_records import SpotTransactionRecords

class Tax(
  FuturesTransactionRecords,
  MarginTransactionRecords,
  P2PTransactionRecords,
  SpotTransactionRecords,
):
  ...