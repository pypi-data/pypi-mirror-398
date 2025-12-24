from typing_extensions import AsyncIterable, Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_sdk.reporting import (
  Transaction, Transactions as TransactionsTDK, Other,
  Posting, CurrencyPosting, FuturePosting, StrategyPosting,
)

from bitget import Bitget
from bitget.sdk.core import SdkMixin
from bitget.common.tax.spot_transaction_records import SpotTransaction

def parse_spot_transactions(transactions: Iterable[SpotTransaction]) -> Iterable[SpotTransaction]:
  for tx in transactions:
    type = tx['spotTaxType']
    if type in ('financial_lock_out', 'financial_unlock_in', 'financial_user_out', 'Redemption'):
      continue
    yield tx

def spot_transaction(tx: SpotTransaction) -> Transaction:
  change = tx['amount'] - abs(tx['fee'])
  asset = tx['coin']
  postings: list[Posting] = [CurrencyPosting(
      asset=asset,
      change=change,
    )]
  if tx['spotTaxType'] in ('Automatic withdrawal', 'Automatic deposit'):
    postings.append(StrategyPosting(
      asset=f'BOT-{asset}',
      change=-change,
    ))
  return Transaction(
    id='spot-' + tx['id'],
    time=tx['ts'],
    operation=Other(details=tx),
    postings=postings,
  )

async def spot_transactions(client: Bitget, *, start: datetime, end: datetime) -> AsyncIterable[list[Transaction]]:
  stream = client.common.tax.spot_transaction_records_paged(start=start, end=end)
  transactions = [tx async for chunk in stream for tx in chunk]
  transactions = parse_spot_transactions(transactions)
  yield [spot_transaction(tx) for tx in transactions]

async def isolated_transactions(client: Bitget, *, start: datetime, end: datetime) -> AsyncIterable[list[Transaction]]:
  async for chunk in client.common.tax.margin_transaction_records_paged(
    'isolated', start=start, end=end
  ):
    yield [
      Transaction(
        id='isolate-' + tx['id'],
        time=tx['ts'],
        operation=Other(
          details=tx
        ),
        postings=[CurrencyPosting(
          asset=tx['coin'],
          change=tx['amount'] - abs(tx['fee']),
        )]
      )
      for tx in chunk
    ]

async def cross_transactions(client: Bitget, *, start: datetime, end: datetime) -> AsyncIterable[list[Transaction]]:
  async for chunk in client.common.tax.margin_transaction_records_paged(
    'crossed', start=start, end=end
  ):
    yield [
      Transaction(
        id='cross-' + tx['id'],
        time=tx['ts'],
        operation=Other(
          details=tx
        ),
        postings=[CurrencyPosting(
          asset=tx['coin'],
          change=tx['amount'] - abs(tx['fee']),
        )]
      )
      for tx in chunk
    ]

async def futures_transactions(client: Bitget, *, start: datetime, end: datetime) -> AsyncIterable[list[Transaction]]:
  async for chunk in client.common.tax.futures_transaction_records_paged(
    start=start, end=end
  ):
    yield [
      Transaction(
        id='futures-' + tx['id'],
        time=tx['ts'],
        operation=Other(
          details=tx
        ),
        postings=[CurrencyPosting(
          asset=tx['marginCoin'],
          change=tx['amount'] - abs(tx['fee']),
        )]
      )
      for tx in chunk
    ]

@dataclass
class Transactions(SdkMixin, TransactionsTDK):
  """Bitget Transactions
  
  **Does not support**:
  - P2P trading
  - Copy trading
  """
  async def transactions(
    self, *, start: datetime, end: datetime
  ) -> AsyncIterable[list[Transaction]]:
    async for chunk in spot_transactions(self.client, start=start, end=end):
      yield chunk
    async for chunk in isolated_transactions(self.client, start=start, end=end):
      yield chunk
    async for chunk in cross_transactions(self.client, start=start, end=end):
      yield chunk
    async for chunk in futures_transactions(self.client, start=start, end=end):
      yield chunk