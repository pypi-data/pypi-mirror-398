from decimal import Decimal
from datetime import timedelta, timezone
import re
import pandas as pd
from trading_sdk.reporting import CurrencyPosting

from .. import util

time_regex = re.compile(r'Time\(UTC\+(\d{2}):(\d{2})\)')

def parse_timezone(key: str) -> timezone:
  match = time_regex.match(key)
  assert match is not None
  hours, minutes = match.groups()
  return timezone(timedelta(hours=int(hours), minutes=int(minutes)))

def parse_posting(row: pd.Series):
  return util.TaggedPosting(
    time=util.ensure_datetime(str(row['Creation Time'])).replace(tzinfo=timezone.utc),
    tag='Futures ' + str(row['Fund Type']),
    posting=CurrencyPosting(
      asset=str(row['Crypto']),
      change=Decimal(str(row['Amount'])),
    )
  )

class futures_capital_flow:
  """Parsing MEXC's futures capital flow.

  Data must be downloaded as an Excel file from:
  
  > [Data Export](https://www.mexc.com/support/data-export) > `Futures` > `Futures Capital Flow` > `Excel`

  **Expected schema:**
  - `Creation Time(<timezone>)`, e.g. `Creation Time(UTC+03:00)`
  - `Crypto`
  - `Fund Type`
  - `Amount`
  """  

  schema: util.Schema = {
    time_regex: str,
    'Crypto': str,
    'Fund Type': str,
    'Amount': str,
  }

  @staticmethod
  def load(path: str, *, skip_zero_changes: bool = True) -> pd.DataFrame:
    df = pd.read_excel(path, dtype={'Amount': str})
    util.validate_schema(df, futures_capital_flow.schema)
    key = util.find_key(df, time_regex)
    assert key is not None
    df['Creation Time'] = pd.to_datetime(df[key]).dt.tz_localize(parse_timezone(key)).dt.tz_convert(timezone.utc)
    if skip_zero_changes:
      df.drop(df[df['Amount'].astype(float) == 0].index, inplace=True) # type: ignore
    df.drop(df[df['Fund Type'] == 'BONUS_DEDUCT'].index, inplace=True) # these are doubly counted (MEXC-side mistake) # type: ignore
    df.reset_index(drop=True, inplace=True)
    return df

  @staticmethod
  def parse(path: str, *, skip_zero_changes: bool = True):
    df = futures_capital_flow.load(path, skip_zero_changes=skip_zero_changes)
    for posting in futures_capital_flow.parse_df(df):
      yield posting

  @staticmethod
  def parse_df(df: pd.DataFrame):
    for _, row in df.iterrows():
      yield parse_posting(row)