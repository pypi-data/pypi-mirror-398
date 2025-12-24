from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from collections import Counter
import re
import pandas as pd
from trading_sdk.reporting import Yield, CurrencyPosting

from .. import util

creation_time_regex = re.compile(r'Creation Time\(UTC\+(\d{2}):(\d{2})\)')

def parse_timezone(key: str) -> timedelta:
  match = creation_time_regex.match(key)
  assert match is not None
  hours, minutes = match.groups()
  return timedelta(hours=int(hours), minutes=int(minutes))

@dataclass
class FixedYield(Yield, util.Operation):
  tag: str
  time_idx: int = 0
  """Index of the transaction within the same instant."""
  @property
  def expected_postings(self):
    return [
      util.TaggedPosting(
        time=self.time,
        tag=self.tag,
        posting=CurrencyPosting(
          asset=self.asset,
          change=self.qty,
        )
      )
    ]

  @property
  def id(self) -> str:
    id = f'{self.tag};{self.asset};{self.time:%Y-%m-%d %H:%M:%S}'
    if self.time_idx:
      id += f';{self.time_idx}'
    return id

def parse_entry(row: pd.Series):
  return FixedYield(
    asset=str(row['Crypto']),
    qty=Decimal(str(row['Quantity'])),
    time=util.ensure_datetime(str(row['Creation Time'])).replace(tzinfo=timezone.utc),
    tag='Spot ' + str(row['Transaction Type']),
  )

class fixed_earn(util.Module):
  """Parsing MEXC's fixed earn log.

  *This data is already included in the spot statement.*

    It must be downloaded as an Excel file from:
    
    > [Data Export](https://www.mexc.com/support/data-export) > `Earn` > `Fixed` > `Excel`

    **Expected schema:**

    - `Creation Time(<timezone>)`, e.g. `Creation Time(UTC+03:00)`
    - `Crypto`
    - `Transaction Type`
    - `Quantity`
    """

  matching_mode = 'eq'

  schema: util.Schema = {
    creation_time_regex: str,
    'Crypto': str,
    'Transaction Type': str,
    'Quantity': str,
  }

  @staticmethod
  def load(path: str, *, skip_zero_changes: bool = True) -> pd.DataFrame:
    df = pd.read_excel(path, dtype={'Quantity': str})
    util.validate_schema(df, fixed_earn.schema)
    if len(df) == 0:
      return df
    key = util.find_key(df, creation_time_regex)
    assert key is not None
    df['Creation Time'] = pd.to_datetime(df[key]) - parse_timezone(key)
    if skip_zero_changes:
      df.drop(df[df['Quantity'].astype(float) == 0].index, inplace=True) # type: ignore
      df.reset_index(drop=True, inplace=True)
    return df

  @staticmethod
  def parse(path: str, *_, skip_zero_changes: bool = True):
    df = fixed_earn.load(path, skip_zero_changes=skip_zero_changes)
    for posting in fixed_earn.parse_df(df):
      yield posting

  @staticmethod
  def parse_df(df: pd.DataFrame):
    times = Counter[datetime]()
    for _, row in df.iterrows():
      entry = parse_entry(row)
      times[entry.time] += 1
      entry.time_idx = times[entry.time]
      yield entry