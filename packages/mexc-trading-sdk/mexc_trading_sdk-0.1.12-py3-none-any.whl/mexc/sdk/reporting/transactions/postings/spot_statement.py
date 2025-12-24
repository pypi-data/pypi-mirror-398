from decimal import Decimal
from datetime import timedelta, timezone
import re
import pandas as pd
from trading_sdk.reporting import CurrencyPosting

from .. import util

creation_time_regex = re.compile(r'Creation Time\(UTC\+(\d{2}):(\d{2})\)')

def parse_timezone(key: str) -> timezone:
  match = creation_time_regex.match(key)
  assert match is not None
  hours, minutes = match.groups()
  return timezone(timedelta(hours=int(hours), minutes=int(minutes)))

def parse_posting(row: pd.Series) -> util.TaggedPosting:
  return util.TaggedPosting(
    time=util.ensure_datetime(str(row['Creation Time'])).replace(tzinfo=timezone.utc),
    tag='Spot ' + str(row['Transaction Type']),
    posting=CurrencyPosting(
      asset=str(row['Crypto']),
      change=Decimal(str(row['Quantity'])),
    )
  )

class spot_statement:
  """Parsing MEXC's spot statement.

  Data must be downloaded as an Excel file from:
  
  > [Data Export](https://www.mexc.com/support/data-export) > `Spot` > `Spot Statement` > `Excel`

  **Expected schema:**

  - `Creation Time(<timezone>)`, e.g. `Creation Time(UTC+03:00)`
  - `Crypto`
  - `Transaction Type`
  - `Quantity`
  """

  schema: util.Schema = {
    creation_time_regex: str,
    'Crypto': str,
    'Transaction Type': str,
    'Quantity': str,
  }

  @staticmethod
  def load(path: str, *, skip_zero_changes: bool = True) -> pd.DataFrame:
    df = pd.read_excel(path, dtype={'Quantity': str})
    util.validate_schema(df, spot_statement.schema)
    key = util.find_key(df, creation_time_regex)
    assert key is not None
    df['Creation Time'] = pd.to_datetime(df[key]).dt.tz_localize(parse_timezone(key)).dt.tz_convert(timezone.utc)
    if skip_zero_changes:
      df.drop(df[df['Quantity'].astype(float) == 0].index, inplace=True) # type: ignore
      df.reset_index(drop=True, inplace=True)
    return df

  @staticmethod
  def parse(path: str, *, skip_zero_changes: bool = True):
    df = spot_statement.load(path, skip_zero_changes=skip_zero_changes)
    for posting in spot_statement.parse_df(df):
      yield posting

  @staticmethod
  def parse_df(df: pd.DataFrame):
    for _, row in df.iterrows():
      yield parse_posting(row)