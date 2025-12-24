from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from collections import Counter
import re
import pandas as pd
from trading_sdk.reporting.types import (
  Posting, CurrencyPosting, FuturePosting,
  Trade, Fee
)

from .. import util

time_regex = re.compile(r'Time\(UTC\+(\d{2}):(\d{2})\)')

def parse_timezone(key: str) -> timezone:
  match = time_regex.match(key)
  assert match is not None
  hours, minutes = match.groups()
  return timezone(timedelta(hours=int(hours), minutes=int(minutes)))

pair_regex = re.compile(r'^(.+?)(USDT|USDC)$')

@dataclass
class FuturesTrade(Trade, util.Operation):
  time_idx: int = 0
  """Index of the transaction within the same instant."""

  @property
  def expected_postings(self) -> list[util.TaggedPosting]:
    if self.fee is not None:
      return [
        util.TaggedPosting(
          time=self.time,
          tag='Futures FEE',
          posting=CurrencyPosting(
            asset=self.fee.asset,
            change=-self.fee.amount,
          )
        )
      ]
    else:
      return []

  @property
  def fixed_postings(self) -> list[Posting]:
    s = 1 if self.side == 'BUY' else -1
    return [
      FuturePosting(
        asset=f'{self.base}_{self.quote}',
        change=s*self.qty,
        price=self.price,
      )
    ]

  @property
  def id(self) -> str:
    id = f'{self.base}_{self.quote}-PERPETUAL;{self.time:%Y-%m-%d %H:%M:%S}'
    if self.time_idx:
      id += f';{self.time_idx}'
    return id

def parse_entry(row: pd.Series):
  fee_amount = Decimal(str(row['Trading Fee']))
  if fee_amount == 0:
    fee = None
  else:
    fee = Fee(fee_amount, str(row['Fee-payment Crypto']))
  return FuturesTrade(
    base=str(row['base']),
    quote=str(row['quote']),
    qty=Decimal(str(row['Filled Qty (Crypto)'])),
    price=Decimal(str(row['Filled Price'])),
    liquidity='TAKER' if row['Role'] == 'Taker' else 'MAKER',
    time=util.ensure_datetime(row['Time(UTC)']),
    side='BUY' if row['Direction'] in ('sell short', 'buy long') else 'SELL',
    fee=fee,
  )

class futures_trades(util.Module):
  """Parsing MEXC's futures trades log.

  *This data is already included in the futures capital flow.*

    It must be downloaded as an Excel file from:
    
    > [Data Export](https://www.mexc.com/support/data-export) > `Futures` > `Futures Trade History` > `Excel`

    **Expected schema:**

    - `Time(<timezone>)`, e.g. `'Time(UTC+03:00)'`
    - `Futures Trading Pair, e.g. 'BTCUSDT'`	
    - `Direction :: 'sell short' | 'buy short' | 'sell long' | 'buy long'`
    - `Filled Qty (Crypto)`
    - `Filled Price`
    - `Trading Fee`
    - `Fee-payment Crypto`
    - `Role :: Taker | Maker`
    """

  matching_mode = 'eq'

  schema: util.Schema = {
    time_regex: str,
    'Futures Trading Pair': pair_regex,
    'Direction': re.compile(r"^(sell short|buy short|sell long|buy long)$"),
    'Filled Qty (Crypto)': str,
    'Filled Price': str,
    'Trading Fee': str,
    'Fee-payment Crypto': str,
    'Role': re.compile(r"^(Taker|Maker)$"),
  }

  @staticmethod
  def load(path: str, *, skip_zero_changes: bool = True) -> pd.DataFrame:
    df = pd.read_excel(path, dtype={'Filled Qty (Crypto)': str, 'Filled Price': str, 'Trading Fee': str})
    util.validate_schema(df, futures_trades.schema)
    if skip_zero_changes:
      df.drop(df[df['Filled Qty (Crypto)'].astype(float) == 0].index, inplace=True) # type: ignore
      df.reset_index(drop=True, inplace=True)
    df[['base', 'quote']] = df['Futures Trading Pair'].str.extract(pair_regex)
    key = util.find_key(df, time_regex)
    assert key is not None
    df['Time(UTC)'] = pd.to_datetime(df[key]).dt.tz_localize(parse_timezone(key)).dt.tz_convert(timezone.utc)
    return df

  @staticmethod
  def parse(path: str, *_, skip_zero_changes: bool = True):
    """Parse spot trades history excel file.

    - `path`: Path to excel file
    - `tz`: Timezone of the times in the log
    """
    df = futures_trades.load(path, skip_zero_changes=skip_zero_changes)
    for posting in futures_trades.parse_df(df):
      yield posting

  @staticmethod
  def parse_df(df: pd.DataFrame):
    times = Counter[datetime]()
    for _, row in df.iterrows():
      entry = parse_entry(row)
      times[entry.time] += 1
      entry.time_idx = times[entry.time]
      yield entry