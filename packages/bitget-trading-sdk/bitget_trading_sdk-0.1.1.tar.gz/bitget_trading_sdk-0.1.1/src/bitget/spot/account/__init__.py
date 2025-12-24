from .assets import Assets
from .deposit_records import DepositRecords
from .withdrawal_records import WithdrawalRecords

class Account(Assets, DepositRecords, WithdrawalRecords):
  ...